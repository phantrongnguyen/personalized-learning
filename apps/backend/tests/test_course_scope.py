"""Opt-in PostgreSQL scope tests: all fixtures rolled back in outer transactions."""
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
from fastapi import FastAPI, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import engine
from core.permissions import get_current_user
from models.user import User, Role
from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
from models.assignment import AdvisorStudent, CourseLecturer
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import MLModel, PredictionRun
from models.intervention import InterventionPlan, InterventionTask, AdvisingNote
from models.help_request import StudentHelpRequest
from api.v1.endpoints import student, advisor, lecturer
from repositories.student_repo import get_student_tasks_list
from schemas.student import HelpRequestCreateIn, TaskCompleteIn
from schemas.advisor_lecturer import (
    PlanCreateIn, CourseTaskAssignIn, AlertAdvisorIn,
)


@unittest.skipUnless(os.getenv("RUN_COURSE_SCOPE_DB") == "1", "Explicit opt-in required for rollback-only DB fixtures")
class CourseScopeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = await engine.connect()
        self.outer = await self.connection.begin()
        self.db = AsyncSession(bind=self.connection, expire_on_commit=False,
                               join_transaction_mode="create_savepoint")
        self.addAsyncCleanup(self.cleanup_fixture)
        unique = uuid.uuid4().hex[:10]
        self.user = User(email=f"scope-{unique}@example.invalid", full_name="Scope fixture",
                         hashed_password="test-fixture-not-a-password-hash")
        other = User(email=f"other-{unique}@example.invalid", full_name="Other fixture",
                     hashed_password="test-fixture-not-a-password-hash")
        roles = list((await self.db.execute(select(Role).where(
            Role.code.in_(["STUDENT", "ADVISOR", "LECTURER"]),
        ))).scalars().all())
        self.user.roles = list(roles)
        other.roles = list(roles)
        self.other_user = other
        self.db.add_all([self.user, other])
        await self.db.flush()
        self.profile = StudentProfile(user_id=self.user.id, student_code=f"scope-{unique}",
                                     gender="M", highest_education="HE Qualification", age_band="0-35")
        self.other_profile = StudentProfile(user_id=other.id, student_code=f"other-{unique}",
                                           gender="M", highest_education="HE Qualification", age_band="0-35")
        courses = [Course(code_module=f"S{i}-{unique}", name=f"Scope course {i}") for i in range(2)]
        self.db.add_all([self.profile, self.other_profile, *courses])
        await self.db.flush()
        self.presentations = [CoursePresentation(course_id=c.id, code_presentation="TEST", module_presentation_length=268) for c in courses]
        self.db.add_all(self.presentations)
        await self.db.flush()
        self.advisor_profile = AdvisorProfile(user_id=self.user.id, department="Scope")
        self.other_advisor = AdvisorProfile(user_id=other.id, department="Scope")
        self.lecturer_profile = LecturerProfile(user_id=self.user.id, lecturer_code=f"L-{unique}", department="Scope")
        self.other_lecturer = LecturerProfile(user_id=other.id, lecturer_code=f"O-{unique}", department="Scope")
        self.db.add_all([self.advisor_profile, self.other_advisor, self.lecturer_profile, self.other_lecturer])
        await self.db.flush()
        self.db.add_all([
            AdvisorStudent(advisor_id=self.advisor_profile.id, student_id=self.profile.id,
                           academic_year="TEST", class_name=f"A-{unique}"),
            AdvisorStudent(advisor_id=self.other_advisor.id, student_id=self.other_profile.id,
                           academic_year="TEST", class_name=f"B-{unique}"),
            *[CourseLecturer(lecturer_id=self.lecturer_profile.id, presentation_id=p.id)
              for p in self.presentations],
            CourseLecturer(lecturer_id=self.other_lecturer.id, presentation_id=self.presentations[0].id),
        ])
        self.enrollments = [StudentEnrollment(student_id=self.profile.id, presentation_id=p.id) for p in self.presentations]
        self.foreign = StudentEnrollment(student_id=self.other_profile.id, presentation_id=self.presentations[0].id)
        self.db.add_all([*self.enrollments, self.foreign])
        model = MLModel(model_name="Scope fixture", version=f"scope-{unique}", model_file_path="not-an-artifact", is_active=False)
        self.db.add(model)
        await self.db.flush()
        snapshots = [StudentFeatureSnapshot(enrollment_id=e.id) for e in self.enrollments]
        self.db.add_all(snapshots)
        await self.db.flush()
        self.predictions = [PredictionRun(snapshot_id=s.id, model_id=model.id, prediction_label=0, risk_probability=.1) for s in snapshots]
        self.db.add_all(self.predictions)
        await self.db.flush()
        self.plans = [InterventionPlan(student_id=self.profile.id, prediction_run_id=p.id) for p in self.predictions]
        self.db.add_all(self.plans)
        await self.db.flush()
        self.tasks = [InterventionTask(plan_id=p.id, category="HOC_THUAT", priority="HIGH",
                                      title=f"Task {i}", description="Scope fixture", target_metric="Test") for i, p in enumerate(self.plans)]
        self.db.add_all(self.tasks)
        self.requests = [StudentHelpRequest(student_id=self.profile.id, presentation_id=p.id,
                           target_role="ADVISOR", subject=f"Request {i}", content="Scope fixture") for i, p in enumerate(self.presentations)]
        self.generic = StudentHelpRequest(student_id=self.profile.id, target_role="ADVISOR", subject="General", content="Scope fixture")
        self.db.add_all([*self.requests, self.generic])
        await self.db.flush()
        self.admin = SimpleNamespace(id=self.user.id, roles=[SimpleNamespace(code="ADMIN")])
        self.actor = self.user
        self.app = FastAPI()
        for prefix, module in (("student", student), ("advisor", advisor), ("lecturer", lecturer)):
            self.app.include_router(module.router, prefix=f"/api/v1/{prefix}")
        async def current_actor():
            return self.actor
        async def test_db():
            yield self.db
        self.app.dependency_overrides[get_current_user] = current_actor
        self.app.dependency_overrides[student.get_db] = test_db

    async def request(self, method, path, actor=None, **kwargs):
        self.actor = actor or self.user
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
            return await client.request(method, f"/api/v1{path}", **kwargs)

    async def cleanup_fixture(self):
        await self.db.close()
        await self.outer.rollback()
        await self.connection.close()
        await engine.dispose()

    async def test_suggestions_read_is_scoped_and_does_not_create_tasks(self):
        before = len((await self.db.execute(select(InterventionTask.id))).all())
        response = await lecturer.get_course_student_suggestions(
            self.presentations[0].id, self.profile.id, self.admin, self.db)
        assert response["status"] == "insufficient_data"
        assert response["prediction"] is not None
        assert response["assignment"]["can_assign"] is True
        assert len((await self.db.execute(select(InterventionTask.id))).all()) == before
        with self.assertRaises(HTTPException) as error:
            await lecturer.get_course_student_suggestions(
                self.presentations[1].id, self.other_profile.id, self.admin, self.db)
        assert error.exception.status_code == 404
        actor = SimpleNamespace(id=self.other_user.id, roles=[SimpleNamespace(code="LECTURER")])
        with self.assertRaises(HTTPException) as error:
            await lecturer.get_course_student_suggestions(
                self.presentations[1].id, self.profile.id, actor, self.db)
        assert error.exception.status_code == 403
        assert len((await self.db.execute(select(InterventionTask.id))).all()) == before

    async def test_risk_board_without_snapshot_has_no_fake_zero_metrics(self):
        from repositories.academic_repo import get_course_risk_board
        board = await get_course_risk_board(self.db, self.presentations[0].id)
        entry = next(item for item in board if item["student_id"] == self.other_profile.id)
        assert entry["risk_status"] == "NOT_PREDICTED"
        assert entry["risk_probability"] is None
        assert entry["total_clicks"] is None
        assert entry["late_submissions"] is None
        assert entry["submission_rate"] is None

    async def test_model_threshold_boundary_is_reported_not_reinterpreted(self):
        for index, (probability, label) in enumerate(((0.499, 0), (0.5, 1))):
            snapshot = StudentFeatureSnapshot(enrollment_id=self.enrollments[0].id,
                                              created_at=datetime.now(timezone.utc) + timedelta(days=index + 1))
            self.db.add(snapshot)
            await self.db.flush()
            self.db.add(PredictionRun(snapshot_id=snapshot.id, model_id=self.predictions[0].model_id,
                                      prediction_label=label, risk_probability=probability))
            await self.db.flush()
            response = await lecturer.get_course_student_suggestions(
                self.presentations[0].id, self.profile.id, self.admin, self.db)
            assert response["prediction"]["risk_probability"] == probability
            assert response["prediction"]["prediction_label"] == label
            assert response["prediction"]["threshold"] == 0.5

    async def test_latest_snapshot_without_prediction_is_not_safe(self):
        from repositories.academic_repo import get_course_risk_board
        latest = StudentFeatureSnapshot(enrollment_id=self.enrollments[0].id,
                                        created_at=datetime.now(timezone.utc) + timedelta(days=1))
        self.db.add(latest)
        await self.db.flush()
        response = await lecturer.get_course_student_suggestions(
            self.presentations[0].id, self.profile.id, self.admin, self.db)
        assert response["prediction"] is None
        board = await get_course_risk_board(self.db, self.presentations[0].id)
        entry = next(item for item in board if item["student_id"] == self.profile.id)
        assert entry["risk_status"] == "NOT_PREDICTED" and entry["risk_probability"] is None

    async def test_tasks_are_separate_per_enrollment(self):
        for i, enrollment in enumerate(self.enrollments):
            tasks = await get_student_tasks_list(self.db, self.profile.id, enrollment.id)
            self.assertEqual([t.id for t in tasks], [self.tasks[i].id])

    async def test_reminders_exclude_other_students_and_completed_tasks(self):
        from services.reminder_service import get_student_course_reminders
        snapshot = StudentFeatureSnapshot(enrollment_id=self.foreign.id)
        self.db.add(snapshot)
        await self.db.flush()
        prediction = PredictionRun(snapshot_id=snapshot.id, model_id=self.predictions[0].model_id,
                                   prediction_label=0, risk_probability=.1)
        self.db.add(prediction)
        await self.db.flush()
        plan = InterventionPlan(student_id=self.other_profile.id, prediction_run_id=prediction.id)
        self.db.add(plan)
        await self.db.flush()
        self.db.add(InterventionTask(plan_id=plan.id, category="HOC_THUAT", priority="HIGH",
                                    title="Foreign task", description="Test", target_metric="Test"))
        self.tasks[1].is_completed = True
        await self.db.flush()
        reminders = await get_student_course_reminders(self.db, self.profile.id)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]["enrollment_id"], self.enrollments[0].id)
        self.assertEqual(reminders[0]["pending_tasks"], 1)

    async def test_help_excludes_other_course_and_general_requests(self):
        for i, enrollment in enumerate(self.enrollments):
            requests = await student.get_my_help_requests(self.user, self.db, enrollment.id)
            self.assertEqual([r.id for r in requests], [self.requests[i].id])
        self.assertEqual(len(await student.get_my_help_requests(self.user, self.db)), 3)

    async def test_new_help_is_linked_to_selected_course(self):
        request = await student.create_help_request(HelpRequestCreateIn(
            enrollment_id=self.enrollments[1].id, target_role="ADVISOR", subject="Scoped help", content="Test body"), self.user, self.db)
        self.assertEqual(request.presentation_id, self.presentations[1].id)

    async def test_foreign_enrollment_is_rejected(self):
        for endpoint in (student.get_my_tasks, student.get_my_help_requests):
            with self.assertRaises(HTTPException) as error:
                await endpoint(self.user, self.db, self.foreign.id)
            self.assertEqual(error.exception.status_code, 404)
        with self.assertRaises(HTTPException) as error:
            await student.create_help_request(HelpRequestCreateIn(enrollment_id=self.foreign.id,
                target_role="ADVISOR", subject="Invalid help", content="Test body"), self.user, self.db)
        self.assertEqual(error.exception.status_code, 404)

    async def test_conflicting_presentation_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            await student.create_help_request(HelpRequestCreateIn(enrollment_id=self.enrollments[0].id,
                presentation_id=self.presentations[1].id, target_role="ADVISOR", subject="Invalid help", content="Test body"), self.user, self.db)
        self.assertEqual(error.exception.status_code, 422)

    async def test_task_cannot_be_completed_from_another_course(self):
        with self.assertRaises(HTTPException) as error:
            await student.complete_task(self.tasks[0].id, TaskCompleteIn(enrollment_id=self.enrollments[1].id), self.user, self.db)
        self.assertEqual(error.exception.status_code, 404)
        self.assertFalse(self.tasks[0].is_completed)

    async def test_lecturer_task_goes_to_matching_plan(self):
        task = await lecturer.assign_course_task(self.presentations[1].id,
            CourseTaskAssignIn(student_id=self.profile.id, title="New task", description="Scope fixture"), self.admin, self.db)
        self.assertEqual(task.plan_id, self.plans[1].id)

    async def test_lecturer_assignment_reaches_student_and_can_be_completed(self):
        presentation_id = self.presentations[1].id
        enrollment_id = self.enrollments[1].id
        create = await self.request("POST", f"/lecturer/courses/{presentation_id}/tasks", json={
            "student_id": str(self.profile.id), "title": "Practice review",
            "description": "Verified basis: review two exercises", "priority": "MEDIUM",
            "target_metric": "Complete two exercises",
        })
        self.assertEqual(create.status_code, 200, create.text)
        task_id = create.json()["id"]
        self.assertEqual(create.json()["plan_id"], str(self.plans[1].id))

        tasks = await self.request("GET", f"/student/tasks?enrollment_id={enrollment_id}")
        self.assertEqual(tasks.status_code, 200, tasks.text)
        self.assertIn(task_id, [task["id"] for task in tasks.json()])
        self.assertNotIn(task_id, [task["id"] for task in (
            await self.request("GET", f"/student/tasks?enrollment_id={self.enrollments[0].id}")
        ).json()])

        completed = await self.request("PATCH", f"/student/tasks/{task_id}/complete", json={
            "enrollment_id": str(enrollment_id), "student_feedback": "Reviewed",
        })
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertTrue(completed.json()["is_completed"])

    async def test_alert_is_scoped_and_addresses_assigned_advisor(self):
        result = await lecturer.alert_advisor(self.profile.id, AlertAdvisorIn(
            presentation_id=self.presentations[1].id, content="Scoped alert"), self.admin, self.db)
        alert = await self.db.get(StudentHelpRequest, result["alert_id"])
        self.assertEqual(alert.presentation_id, self.presentations[1].id)
        self.assertEqual(alert.target_user_id, self.user.id)

    async def test_unassigned_lecturer_cannot_assign_task(self):
        actor = SimpleNamespace(id=self.other_user.id, roles=[SimpleNamespace(code="LECTURER")])
        with self.assertRaises(HTTPException) as error:
            await lecturer.assign_course_task(self.presentations[1].id,
                CourseTaskAssignIn(student_id=self.profile.id, title="Invalid task", description="Test"), actor, self.db)
        self.assertEqual(error.exception.status_code, 403)

    async def test_advisor_plan_uses_selected_enrollment(self):
        plan = await advisor.create_intervention_plan(PlanCreateIn(student_id=self.profile.id,
            enrollment_id=self.enrollments[1].id), self.admin, self.db)
        self.assertEqual(plan.prediction_run_id, self.predictions[1].id)

    async def test_ambiguous_plan_requires_course_selection(self):
        with self.assertRaises(HTTPException) as error:
            await advisor.create_intervention_plan(PlanCreateIn(student_id=self.profile.id), self.admin, self.db)
        self.assertEqual(error.exception.status_code, 422)

    async def test_notes_reject_other_advisors_student_without_writing(self):
        payload = dict(enrollment_id=str(self.enrollments[0].id), meeting_date="2026-10-18", content="Scope test")
        before = (await self.db.execute(select(func.count()).select_from(AdvisingNote))).scalar_one()
        denied = await self.request("POST", "/advisor/advising-notes", self.other_user, json=payload)
        self.assertEqual(denied.status_code, 403, denied.text)
        after = (await self.db.execute(select(func.count()).select_from(AdvisingNote))).scalar_one()
        self.assertEqual(after, before)
        allowed = await self.request("POST", "/advisor/advising-notes", json=payload)
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(allowed.json()["advisor_id"], str(self.advisor_profile.id))
        missing = await self.request("POST", "/advisor/advising-notes", json={**payload, "enrollment_id": str(uuid.uuid4())})
        self.assertEqual(missing.status_code, 404)

    async def test_advisor_cannot_read_or_change_other_students_records(self):
        for suffix in ("overview", "radar", "notes"):
            response = await self.request("GET", f"/advisor/students/{self.profile.id}/{suffix}", self.other_user)
            self.assertIn(response.status_code, (403, 404), response.text)
        create = await self.request("POST", "/advisor/interventions", self.other_user,
            json=dict(student_id=str(self.profile.id), enrollment_id=str(self.enrollments[0].id)))
        self.assertEqual(create.status_code, 403)
        update = await self.request("PUT", f"/advisor/interventions/{self.plans[0].id}", self.other_user,
            json={"status": "COMPLETED"})
        self.assertEqual(update.status_code, 404)
        task = await self.request("POST", f"/advisor/interventions/{self.plans[0].id}/tasks", self.other_user,
            json=dict(category="HOC_THUAT", title="Denied", description="Denied"))
        self.assertEqual(task.status_code, 404)
        self.assertEqual(self.plans[0].status, "ACTIVE")
        listed = await self.request("GET", "/advisor/interventions", self.other_user)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json(), [])

    async def test_assigned_advisor_can_read_update_and_add_task(self):
        for suffix in ("overview", "radar", "notes"):
            response = await self.request("GET", f"/advisor/students/{self.profile.id}/{suffix}")
            self.assertEqual(response.status_code, 200, response.text)
        response = await self.request("PUT", f"/advisor/interventions/{self.plans[0].id}",
            json={"advisor_note_summary": "Updated by assigned advisor"})
        self.assertEqual(response.status_code, 200, response.text)
        response = await self.request("POST", f"/advisor/interventions/{self.plans[0].id}/tasks",
            json=dict(category="HOC_THUAT", title="Allowed", description="Allowed"))
        self.assertEqual(response.status_code, 200, response.text)

    async def test_lecturer_cannot_access_other_course_or_alert_its_students(self):
        course_id = self.presentations[1].id
        for suffix in ("risk-board", "students"):
            allowed = await self.request("GET", f"/lecturer/courses/{course_id}/{suffix}")
            self.assertEqual(allowed.status_code, 200, allowed.text)
            response = await self.request("GET", f"/lecturer/courses/{course_id}/{suffix}", self.other_user)
            self.assertEqual(response.status_code, 403, response.text)
        response = await self.request("PUT", f"/lecturer/courses/{course_id}/students/{self.profile.id}/assessment",
            self.other_user, json={"submission_rate": .5})
        self.assertEqual(response.status_code, 403)
        for body, code in (({"content": "No course"}, 422),
                           ({"presentation_id": None, "content": "Null course"}, 422),
                           ({"presentation_id": str(course_id), "content": "Other course"}, 403)):
            response = await self.request("POST", f"/lecturer/students/{self.profile.id}/alert-advisor",
                self.other_user, json=body)
            self.assertEqual(response.status_code, code, response.text)
        # Assigned teacher, but the selected student is not enrolled in this course.
        response = await self.request("POST", f"/lecturer/students/{self.other_profile.id}/alert-advisor",
            json={"presentation_id": str(course_id), "content": "Wrong student"})
        self.assertEqual(response.status_code, 404)

    async def test_student_cannot_read_or_complete_another_students_task(self):
        for suffix in ("risk-prediction", "radar"):
            response = await self.request("GET", f"/student/courses/{self.enrollments[0].id}/{suffix}", self.other_user)
            self.assertEqual(response.status_code, 404, response.text)
        response = await self.request("PATCH", f"/student/tasks/{self.tasks[0].id}/complete", self.other_user, json={})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.tasks[0].is_completed)
        for route in ("tasks", "intervention-plans", "help-requests"):
            response = await self.request("GET", f"/student/{route}", self.other_user)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

    async def test_help_rejects_unassigned_recipients_and_invalid_roles(self):
        payload = dict(enrollment_id=str(self.enrollments[1].id), target_role="ADVISOR",
                       subject="Scope help", content="Scope test body")
        before = (await self.db.execute(select(func.count()).select_from(StudentHelpRequest))).scalar_one()
        for role in ("ADVISOR", "LECTURER"):
            response = await self.request("POST", "/student/help-requests",
                json={**payload, "target_role": role, "target_user_id": str(self.other_user.id)})
            self.assertEqual(response.status_code, 403, response.text)
        response = await self.request("POST", "/student/help-requests", json={**payload, "target_role": "ADMIN"})
        self.assertEqual(response.status_code, 422)
        response = await self.request("POST", "/student/help-requests",
            json=dict(target_role="LECTURER", subject="Missing course", content="Scope test body"))
        self.assertEqual(response.status_code, 422)
        after = (await self.db.execute(select(func.count()).select_from(StudentHelpRequest))).scalar_one()
        self.assertEqual(after, before)
        for role in ("ADVISOR", "LECTURER"):
            response = await self.request("POST", "/student/help-requests", json={**payload, "target_role": role})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["target_user_id"], str(self.user.id))
            response = await self.request("POST", "/student/help-requests",
                json={**payload, "target_role": role, "target_user_id": str(self.user.id)})
            self.assertEqual(response.status_code, 200, response.text)

    async def test_help_rejects_inactive_or_role_removed_assigned_recipient(self):
        payload = dict(enrollment_id=str(self.enrollments[0].id), target_role="LECTURER",
                       target_user_id=str(self.other_user.id), subject="Recipient state", content="Scope test body")
        self.other_user.is_active = False
        await self.db.flush()
        response = await self.request("POST", "/student/help-requests", json=payload)
        self.assertEqual(response.status_code, 403, response.text)
        self.other_user.is_active = True
        self.other_user.roles = [r for r in self.other_user.roles if r.code != "LECTURER"]
        await self.db.flush()
        response = await self.request("POST", "/student/help-requests", json=payload)
        self.assertEqual(response.status_code, 403, response.text)

    async def test_missing_profiles_and_admin_do_not_bypass_assignments(self):
        actor = SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(code="ADMIN")])
        response = await self.request("POST", "/advisor/interventions", actor,
            json=dict(student_id=str(self.profile.id), enrollment_id=str(self.enrollments[0].id)))
        self.assertEqual(response.status_code, 400)
        response = await self.request("GET", f"/lecturer/courses/{self.presentations[0].id}/risk-board", actor)
        self.assertEqual(response.status_code, 403)
        response = await self.request("PATCH", f"/student/tasks/{self.tasks[0].id}/complete", actor, json={})
        self.assertEqual(response.status_code, 404)
        # ADMIN with a real profile still cannot cross that profile's assignments.
        actor.id = self.other_user.id
        response = await self.request("POST", "/advisor/interventions", actor,
            json=dict(student_id=str(self.profile.id), enrollment_id=str(self.enrollments[0].id)))
        self.assertEqual(response.status_code, 403)
        response = await self.request("GET", f"/lecturer/courses/{self.presentations[1].id}/risk-board", actor)
        self.assertEqual(response.status_code, 403)

    async def test_role_gate_blocks_student_from_staff_portals(self):
        actor = SimpleNamespace(id=self.user.id, roles=[SimpleNamespace(code="STUDENT")])
        for route in ("/advisor/students", "/lecturer/courses"):
            response = await self.request("GET", route, actor)
            self.assertEqual(response.status_code, 403)

    async def test_anonymous_requests_cannot_read_portal_data(self):
        self.app.dependency_overrides.pop(get_current_user)
        for route in ("/advisor/students", "/lecturer/courses", "/student/tasks"):
            response = await self.request("GET", route)
            self.assertEqual(response.status_code, 401, response.text)
