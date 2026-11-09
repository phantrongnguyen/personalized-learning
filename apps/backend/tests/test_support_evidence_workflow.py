"""Persisted PostgreSQL workflow on disposable fixtures; never certify application data."""
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
import test_course_scope as scope_fixture
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun, MLModel
from models.intervention import InterventionTask
from models.audit import AuditLog
from models.academic import Course
from repositories.academic_repo import update_course_student_assessment
from services import prediction_service
from core.config import settings


@unittest.skipUnless(os.getenv('RUN_COURSE_SCOPE_DB') == '1', 'Dedicated rollback database required')
class SupportEvidenceWorkflowTests(unittest.IsolatedAsyncioTestCase):
    cleanup_fixture = scope_fixture.CourseScopeTests.cleanup_fixture
    request = scope_fixture.CourseScopeTests.request

    async def asyncSetUp(self):
        await scope_fixture.CourseScopeTests.asyncSetUp(self)
        self.presentation = self.presentations[0]
        self.presentation.start_date = (datetime.now(timezone.utc) - timedelta(days=100)).date()
        self.presentation.module_presentation_length = 100
        self.source = StudentFeatureSnapshot(enrollment_id=self.enrollments[0].id,
            total_clicks_to_t=12, clicks_resource_to_t=4, clicks_url_to_t=2,
            active_days_to_t=3, active_day_ratio=.04, days_since_last_activity=7,
            clicks_recent_7=0, clicks_recent_30=4, assessments_submitted_to_t=4,
            late_submissions_to_t=1, submission_rate=.8,
            raw_features_json={'data_source': 'synthetic_demo'},
            created_at=datetime.now(timezone.utc))
        self.db.add(self.source)
        await self.db.flush()
        self.base = f'/lecturer/courses/{self.presentation.id}/students/{self.profile.id}'
        self.review_url = f'{self.base}/snapshots/{self.source.id}/review'

    async def review(self, scope='demonstration'):
        response = await self.request('GET', self.review_url)
        assert response.status_code == 200, response.text
        request = dict(snapshot_sha256=response.json()['snapshot_sha256'], review_scope=scope,
            source_reference='database disposable fixture source',
            review_note='Illustrative fixture inspected by the assigned test lecturer; not real LMS evidence.',
            activity_complete=scope != 'aggregate_only', assessments_complete=scope != 'aggregate_only',
            acknowledged_limitations=True)
        response = await self.request('POST', self.review_url, json=request)
        assert response.status_code == 200, response.text
        return response.json()

    async def test_review_real_inference_plan_and_edited_task_with_audit(self):
        before = await self.db.scalar(select(func.count()).select_from(InterventionTask))
        reviewed = await self.review()
        data = (await self.request('GET', self.base + '/suggestions')).json()
        assert data['status'] == 'available'
        assert data['prediction'] is None  # Reviewing never invents a prediction.
        assert {s['rule_id'] for s in data['suggestions']} == {'G02_AGGREGATE', 'G03'}
        assert data['data_source'] == 'synthetic_demo'
        assert before == await self.db.scalar(select(func.count()).select_from(InterventionTask))
        snapshot = await self.db.get(StudentFeatureSnapshot, uuid.UUID(reviewed['snapshot_id']))
        # Use the real artifact on the disposable snapshot, with a supported OULAD course.
        course = (await self.db.execute(select(Course).where(Course.code_module == 'BBB'))).scalar_one()
        self.presentation.course_id = course.id
        await self.db.flush()
        # Course identity in the review is presentation-based and remains unchanged.
        model = (await self.db.execute(select(MLModel).where(MLModel.is_active.is_(True)))).scalar_one()
        artifact = prediction_service.load_model(settings.model_path)
        run = prediction_service.infer_record(artifact, prediction_service.database_features(
            snapshot, self.enrollments[0], self.profile, course), snapshot.id, model.id, self.user.id, model.version)
        self.db.add(run)
        self.plans[0].status = 'COMPLETED'
        await self.db.flush()
        plan = await self.request('POST', '/advisor/interventions', json={
            'student_id': str(self.profile.id), 'enrollment_id': str(self.enrollments[0].id)})
        assert plan.status_code == 200, plan.text
        detail = (await self.request('GET', self.base + '/suggestions')).json()
        assert detail['prediction']['run_id'] == str(run.id)
        selected = detail['suggestions'][0]
        task = await self.request('POST', f'/lecturer/courses/{self.presentation.id}/tasks', json={
            'student_id': str(self.profile.id), 'title': 'Lecturer edited the draft',
            'description': selected['proposed_action'] + ' Agreed scope for a fixture discussion.',
            'target_metric': 'Confirm timetable together', 'priority': 'LOW',
            'suggestion_snapshot_id': detail['snapshot_id'], 'suggestion_rule_id': selected['rule_id']})
        assert task.status_code == 200, task.text
        assert task.json()['title'] == 'Lecturer edited the draft'
        assert task.json()['plan_id'] == plan.json()['id']
        assert task.json()['priority'] == 'LOW'
        review_log = (await self.db.execute(select(AuditLog).where(
            AuditLog.target_id == snapshot.id, AuditLog.action == 'REVIEW_SUPPORT_EVIDENCE'))).scalar_one()
        assert review_log.user_id == self.user.id
        task_log = (await self.db.execute(select(AuditLog).where(
            AuditLog.target_id == uuid.UUID(task.json()['id']), AuditLog.action == 'ASSIGN_COURSE_TASK'))).scalar_one()
        assert json.loads(task_log.detail)['suggestion_snapshot_id'] == str(snapshot.id)
        assert 'support_evidence' not in self.source.raw_features_json

    async def test_review_is_scoped_and_cannot_reuse_old_snapshot(self):
        denied = await self.request('GET', self.review_url.replace(str(self.presentation.id), str(self.presentations[1].id)))
        assert denied.status_code == 409
        # Other teacher has no ownership of the second course.
        denied = await self.request('GET', self.review_url.replace(str(self.presentation.id), str(self.presentations[1].id)), self.other_user)
        assert denied.status_code == 403
        await self.review()
        stale = await self.request('GET', self.review_url)
        assert stale.status_code == 409

    async def test_aggregate_review_never_unlocks_rules_and_missing_plan_is_clear(self):
        await self.review('aggregate_only')
        self.plans[0].status = 'COMPLETED'
        await self.db.flush()
        response = await self.request('GET', self.base + '/suggestions')
        detail = response.json()
        assert detail['status'] == 'insufficient_data' and detail['suggestions'] == []
        assert not detail['assignment']['can_assign']
        task = await self.request('POST', f'/lecturer/courses/{self.presentation.id}/tasks', json={
            'student_id': str(self.profile.id), 'title': 'Should fail', 'description': 'No active plan'})
        assert task.status_code == 400

    async def test_changed_metrics_invalidate_review_and_stale_task_suggestion(self):
        reviewed = await self.review()
        await update_course_student_assessment(self.db, self.presentation.id, self.profile.id,
            assessments_submitted=4, late_submissions=2, submission_rate=.8, updated_by_user_id=self.user.id)
        detail = (await self.request('GET', self.base + '/suggestions')).json()
        assert detail['status'] == 'insufficient_data'
        latest = await self.db.get(StudentFeatureSnapshot, uuid.UUID(detail['snapshot_id']))
        assert 'support_evidence' not in latest.raw_features_json
        task = await self.request('POST', f'/lecturer/courses/{self.presentation.id}/tasks', json={
            'student_id': str(self.profile.id), 'title': 'Stale choice', 'description': 'Should not be assigned',
            'suggestion_snapshot_id': reviewed['snapshot_id'], 'suggestion_rule_id': 'G03'})
        assert task.status_code == 409
