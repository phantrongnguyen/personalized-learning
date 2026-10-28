"""Regression checks for grouped risk queries, stable pages and database bounds."""
import uuid
from datetime import datetime, timezone
import httpx
import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import IntegrityError
from core.database import engine
from core.security import create_access_token
from main import app
from models.user import User, Role
from models.profile import StudentProfile, AdvisorProfile
from models.academic import CoursePresentation, StudentEnrollment
from models.assignment import AdvisorStudent
from models.feature import StudentFeatureSnapshot
from models.ml import MLModel, PredictionRun
from models.intervention import InterventionPlan, InterventionTask
from repositories.academic_repo import get_advisor_students, get_course_risk_board


@pytest.mark.anyio
async def test_grouped_risk_and_pagination(integration_db, request):
    db = integration_db
    suffix = uuid.uuid4().hex[:10]
    advisor_role = await db.scalar(select(Role).where(Role.code == 'ADVISOR'))
    user = User(email=f'query-{suffix}@test', full_name='Advisor', hashed_password='fixture', roles=[advisor_role])
    db.add(user)
    await db.flush()
    advisor = AdvisorProfile(user_id=user.id, department='Test')
    db.add(advisor)
    presentations = list((await db.scalars(select(CoursePresentation).order_by(CoursePresentation.id).limit(2))).all())
    model = await db.scalar(select(MLModel).where(MLModel.is_active.is_(True)))
    students, enrollments = [], []
    for i in range(4):
        account = User(email=f'q{i}-{suffix}@test', full_name=f'Student {i}', hashed_password='fixture')
        db.add(account)
        await db.flush()
        student = StudentProfile(user_id=account.id, student_code=f'Q{suffix}-{i}', gender='M',
                                 age_band='0-35', highest_education='A Level or Equivalent')
        db.add(student)
        await db.flush()
        students.append(student)
        db.add(AdvisorStudent(advisor_id=advisor.id, student_id=student.id, academic_year='2026', class_name='Query'))
        for presentation in presentations:
            enrollment = StudentEnrollment(student_id=student.id, presentation_id=presentation.id)
            db.add(enrollment)
            await db.flush()
            enrollments.append(enrollment)
            snap = StudentFeatureSnapshot(enrollment_id=enrollment.id, total_clicks_to_t=10)
            db.add(snap)
            await db.flush()
            pred = PredictionRun(snapshot_id=snap.id, model_id=model.id,
                                 prediction_label=1 if i == 0 else 0, risk_probability=0.8 if i == 0 else 0.2)
            db.add(pred)
            await db.flush()
            if i == 0 and presentation == presentations[0]:
                plan = InterventionPlan(prediction_run_id=pred.id, student_id=student.id)
                db.add(plan)
                await db.flush()
                db.add(InterventionTask(plan_id=plan.id, category='HOC_THUAT', title='Task',
                    description='Test', target_metric='Test'))
    # Equal timestamps exercise the UUID tie-break; the newest snapshot is unpredicted.
    timestamp = datetime(2030, 1, 1, tzinfo=timezone.utc)
    db.add_all([StudentFeatureSnapshot(id=uuid.UUID(int=n), enrollment_id=enrollments[-1].id,
                                     created_at=timestamp, total_clicks_to_t=n) for n in (1, 2)])
    await db.flush()
    queries = []
    def record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('SELECT'):
            queries.append(statement)
    event.listen(engine.sync_engine, 'before_cursor_execute', record)
    try:
        first = await get_advisor_students(db, advisor.id, limit=1)
        small_count = len(queries)
        queries.clear()
        all_students = await get_advisor_students(db, advisor.id, limit=4)
        assert len(queries) <= small_count, 'Query count must not grow with student count'
        request.node.user_properties.extend([('selects_one_student', small_count), ('selects_four_students', len(queries))])
    finally:
        event.remove(engine.sync_engine, 'before_cursor_execute', record)
    assert len(all_students) == 4
    assert first == all_students[:1]
    assert all_students[0]['risk_level'] == 'HIGH_RISK'
    assert all_students[0]['uncompleted_tasks_count'] == 1
    assert all_students[0]['has_active_plan']
    assert all_students[-1]['risk_level'] == 'NOT_PREDICTED'
    assert all_students[-1]['unpredicted_courses'] == 1
    second = await get_advisor_students(db, advisor.id, limit=2, offset=2)
    assert [s['student_id'] for s in second] == [s['student_id'] for s in all_students[2:]]
    board = await get_course_risk_board(db, presentations[1].id)
    row = next(row for row in board if row['student_id'] == students[-1].id)
    assert row['risk_status'] == 'NOT_PREDICTED' and row['total_clicks'] == 2
    headers = {'Authorization': 'Bearer ' + create_access_token({'sub': str(user.id)})}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/api/v1/advisor/students?limit=2&offset=2', headers=headers)
        assert response.status_code == 200, response.text
        assert [s['student_id'] for s in response.json()] == [str(s.id) for s in students[2:]]
        for query in ('limit=0', 'limit=501', 'offset=-1'):
            assert (await client.get('/api/v1/advisor/students?' + query, headers=headers)).status_code == 422


@pytest.mark.anyio
async def test_numeric_and_state_checks(integration_db):
    db = integration_db
    suffix = uuid.uuid4().hex[:10]
    account = User(email=f'bounds-{suffix}@test', full_name='Bounds', hashed_password='fixture')
    db.add(account)
    await db.flush()
    student = StudentProfile(user_id=account.id, student_code=f'B{suffix}', gender='M', age_band='0-35', highest_education='HE Qualification')
    db.add(student)
    await db.flush()
    presentation = await db.scalar(select(CoursePresentation).limit(1))
    enrollment = StudentEnrollment(student_id=student.id, presentation_id=presentation.id, date_registration=-20)
    db.add(enrollment)
    await db.flush()
    snap = StudentFeatureSnapshot(enrollment_id=enrollment.id)
    db.add(snap)
    await db.flush()
    statements = [
        f"UPDATE student_feature_snapshots SET {column}=-1 WHERE id='{snap.id}'" for column in (
            'total_clicks_to_t', 'clicks_resource_to_t', 'clicks_url_to_t', 'active_days_to_t',
            'days_since_last_activity', 'clicks_recent_7', 'clicks_recent_30',
            'assessments_submitted_to_t', 'late_submissions_to_t')]
    statements += [f"UPDATE student_feature_snapshots SET {column}={value} WHERE id='{snap.id}'"
                   for column in ('active_day_ratio', 'submission_rate')
                   for value in ('-0.1', '1.1', "'NaN'::float8", "'Infinity'::float8")]
    statements += [f"UPDATE student_enrollments SET {column}={value} WHERE id='{enrollment.id}'"
                   for column, value in [('studied_credits','0'), ('num_of_prev_attempts','-1'), ('final_result',"'INVALID'")]]
    statements += [f"UPDATE student_profiles SET disability='UNKNOWN' WHERE id='{student.id}'"]
    for statement in statements:
        with pytest.raises(IntegrityError) as caught:
            async with db.begin_nested():
                await db.execute(text(statement))
        assert caught.value.orig.sqlstate == '23514'
    for statement in (
        "INSERT INTO courses(code_module,name,credits_default) VALUES ('INVALID','Test',0)",
        "UPDATE course_presentations SET module_presentation_length=-1",
    ):
        with pytest.raises(IntegrityError) as caught:
            async with db.begin_nested():
                await db.execute(text(statement))
        assert caught.value.orig.sqlstate == '23514'
