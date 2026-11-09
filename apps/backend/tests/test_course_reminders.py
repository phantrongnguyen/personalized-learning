import unittest
import uuid
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException
from api.v1.endpoints import student
from services.reminder_service import build_course_reminders


TODAY = date(2026, 10, 16)


def reminder_row(enrollment_id=None, days=None, completed=False, status="ACTIVE"):
    return (
        SimpleNamespace(id=uuid.uuid4(), is_completed=completed),
        SimpleNamespace(status=status, target_completion_date=TODAY + timedelta(days=days) if days is not None else None),
        SimpleNamespace(id=enrollment_id or uuid.uuid4()),
        SimpleNamespace(code_module="CCC", name="Kho dữ liệu"),
        SimpleNamespace(code_presentation="2013J"),
    )


class ReminderRulesTests(unittest.TestCase):
    def test_empty_and_completed_tasks_have_no_reminders(self):
        self.assertEqual(build_course_reminders([], TODAY), [])
        self.assertEqual(build_course_reminders([reminder_row(completed=True), reminder_row(status="COMPLETED")], TODAY), [])

    def test_missing_deadline_still_reminds_pending_tasks(self):
        reminder = build_course_reminders([reminder_row()], TODAY)[0]
        self.assertEqual(reminder["state"], "pending")
        self.assertIsNone(reminder["due_date"])
        self.assertIsNone(reminder["days_remaining"])

    def test_deadline_boundaries(self):
        for days, state in ((-1, "overdue"), (0, "due_soon"), (3, "due_soon"), (4, "pending")):
            with self.subTest(days=days):
                reminder = build_course_reminders([reminder_row(days=days)], TODAY)[0]
                self.assertEqual(reminder["state"], state)
                self.assertEqual(reminder["days_remaining"], days)

    def test_groups_plans_by_enrollment_and_deduplicates_tasks(self):
        enrollment = uuid.uuid4()
        first = reminder_row(enrollment, days=5)
        second = reminder_row(enrollment, days=2)
        reminders = build_course_reminders([first, first, second], TODAY)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]["pending_tasks"], 2)
        self.assertEqual(reminders[0]["days_remaining"], 2)

    def test_same_course_in_two_semesters_is_separate(self):
        rows = [reminder_row(), reminder_row()]
        rows[1][-1].code_presentation = "2014J"
        self.assertEqual(len(build_course_reminders(rows, TODAY)), 2)

    def test_urgent_reminders_sorted_first(self):
        reminders = build_course_reminders([reminder_row(days=10), reminder_row(days=1), reminder_row(days=-2)], TODAY)
        self.assertEqual([r["state"] for r in reminders], ["overdue", "due_soon", "pending"])

    def test_read_identity_changes_on_task_or_urgency_change(self):
        row = reminder_row(days=4)
        initial = build_course_reminders([row], TODAY)[0]["id"]
        self.assertEqual(initial, build_course_reminders([row], TODAY)[0]["id"])
        self.assertNotEqual(initial, build_course_reminders([row], TODAY + timedelta(days=1))[0]["id"])
        self.assertNotEqual(initial, build_course_reminders([row, reminder_row(row[2].id, days=4)], TODAY)[0]["id"])


class ReminderApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_endpoint_uses_current_students_profile(self):
        actor = SimpleNamespace(id=uuid.uuid4())
        profile = SimpleNamespace(id=uuid.uuid4())
        db = object()
        with patch.object(student, "get_student_profile_by_user_id", AsyncMock(return_value=profile)) as get_profile, \
             patch.object(student, "get_student_course_reminders", AsyncMock(return_value=[])) as get_reminders:
            self.assertEqual(await student.get_my_reminders(actor, db), [])
        get_profile.assert_awaited_once_with(db, actor.id)
        get_reminders.assert_awaited_once_with(db, profile.id)

    async def test_missing_profile_does_not_query_other_students(self):
        with patch.object(student, "get_student_profile_by_user_id", AsyncMock(return_value=None)), \
             patch.object(student, "get_student_course_reminders", AsyncMock()) as get_reminders:
            self.assertEqual(await student.get_my_reminders(SimpleNamespace(id=uuid.uuid4()), object()), [])
        get_reminders.assert_not_awaited()

    async def test_access_denied_before_query(self):
        app = FastAPI()
        app.include_router(student.router, prefix="/api/v1/student")
        async def deny():
            raise HTTPException(403, "Student role required")
        app.dependency_overrides[student.require_student] = deny
        app.dependency_overrides[student.get_db] = lambda: None
        with patch.object(student, "get_student_course_reminders", AsyncMock()) as get_reminders:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/student/reminders")
        self.assertEqual(response.status_code, 403)
        get_reminders.assert_not_awaited()
