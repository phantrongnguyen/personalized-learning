"""Opt-in PostgreSQL scope tests: all fixtures rolled back in outer transactions."""
import os
import unittest
import uuid
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import engine
from models.user import User
from models.profile import StudentProfile, AdvisorProfile
from models.assignment import AdvisorStudent
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import MLModel, PredictionRun
from models.intervention import InterventionPlan, InterventionTask
from models.help_request import StudentHelpRequest
from api.v1.endpoints import student, advisor, lecturer
from repositories.student_repo import get_student_tasks_list
from schemas.student import HelpRequestCreateIn, TaskCompleteIn
from schemas.advisor_lecturer import PlanCreateIn, CourseTaskAssignIn, AlertAdvisorIn


@unittest.skipUnless(os.getenv("RUN_COURSE_SCOPE_DB") == "1", "Explicit opt-in required for rollback-only DB fixtures")
class CourseScopeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = await engine.connect()
        self.outer = await self.connection.begin()
        self.db = AsyncSession(bind=self.connection, expire_on_commit=False,
                               join_transaction_mode="create_savepoint")
        unique = uuid.uuid4().hex[:10]
        self.user = User(email=f"scope-{unique}@example.invalid", full_name="Scope fixture",
                         hashed_password="test-fixture-not-a-password-hash")
        other = User(email=f"other-{unique}@example.invalid", full_name="Other fixture",
                     hashed_password="test-fixture-not-a-password-hash")
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

    async def asyncTearDown(self):
        await self.db.close()
        await self.outer.rollback()
        await self.connection.close()
        await engine.dispose()

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

    async def test_alert_is_scoped_and_addresses_assigned_advisor(self):
        profile = AdvisorProfile(user_id=self.other_profile.user_id, department="Test")
        self.db.add(profile)
        await self.db.flush()
        self.db.add(AdvisorStudent(advisor_id=profile.id, student_id=self.profile.id,
                                   academic_year="TEST", class_name="TEST"))
        await self.db.flush()
        result = await lecturer.alert_advisor(self.profile.id, AlertAdvisorIn(
            presentation_id=self.presentations[1].id, content="Scoped alert"), self.admin, self.db)
        alert = await self.db.get(StudentHelpRequest, result["alert_id"])
        self.assertEqual(alert.presentation_id, self.presentations[1].id)
        self.assertEqual(alert.target_user_id, self.other_profile.user_id)

    async def test_unassigned_lecturer_cannot_assign_task(self):
        actor = SimpleNamespace(id=self.user.id, roles=[SimpleNamespace(code="LECTURER")])
        with self.assertRaises(HTTPException) as error:
            await lecturer.assign_course_task(self.presentations[0].id,
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
