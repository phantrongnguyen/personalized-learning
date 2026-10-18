import sys
import os
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# This must run before importing the global engine or any test modules.
from sqlalchemy.engine import make_url
test_url = os.getenv("TEST_DATABASE_URL")
if test_url:
    if not make_url(test_url).database.endswith("_test"):
        raise pytest.UsageError("TEST_DATABASE_URL must end in _test")
    os.environ["DATABASE_URL"] = test_url
elif any(os.getenv(flag) == "1" for flag in
         ("RUN_COURSE_SCOPE_DB", "RUN_AVATAR_DB", "RUN_INTEGRATION_DB")):
    raise pytest.UsageError("Use scripts/run_backend_tests.py: dedicated TEST_DATABASE_URL required")

from core.database import engine
if not test_url:
    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "do_connect")
    def forbid_application_database(*args, **kwargs):
        raise RuntimeError("Tests cannot connect without a dedicated TEST_DATABASE_URL")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def cleanup_db_connections(anyio_backend):
    yield
    await engine.dispose()


@pytest.fixture
async def integration_db(anyio_backend):
    if os.getenv("RUN_INTEGRATION_DB") != "1":
        pytest.skip("Use scripts/run_backend_tests.py for PostgreSQL integration")
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import get_db
    from main import app
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    previous = dict(app.dependency_overrides)
    async def isolated_db():
        yield db
    app.dependency_overrides[get_db] = isolated_db
    try:
        yield db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        await db.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture(autouse=True)
async def legacy_workflow_fixture(request, anyio_backend):
    """Keep old sprint smoke tests self-contained, including endpoint commits."""
    legacy = request.node.path.name in {"test_auth.py", "test_sprint3.py", "test_sprint4.py", "test_sprint5.py"}
    if not legacy:
        yield
        return
    if os.getenv("RUN_INTEGRATION_DB") != "1":
        pytest.skip("Use scripts/run_backend_tests.py for PostgreSQL integration")
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import get_db
    from core.security import get_password_hash
    from main import app
    from models.user import User, Role
    from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
    from models.assignment import AdvisorStudent, CourseLecturer
    from models.academic import Course, CoursePresentation, StudentEnrollment
    from models.feature import StudentFeatureSnapshot
    from models.ml import MLModel, PredictionRun
    from models.intervention import InterventionPlan, InterventionTask
    import uuid
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    previous = dict(app.dependency_overrides)
    try:
        roles = {r.code: r for r in (await db.scalars(select(Role))).all()}
        accounts = {}
        for name, role in (("admin", "ADMIN"), ("advisor", "ADVISOR"), ("lecturer", "LECTURER"), ("student", "STUDENT")):
            user = await db.scalar(select(User).where(User.email == f"{name}@huit.edu.vn"))
            if user is None:
                user = User(email=f"{name}@huit.edu.vn", full_name=f"Test {name}", roles=[roles[role]])
                db.add(user)
            user.hashed_password = get_password_hash("123")
            accounts[name] = user
        await db.flush()
        student = StudentProfile(user_id=accounts["student"].id, student_code="SV001", gender="M",
                                 highest_education="HE Qualification", age_band="0-35")
        advisor = AdvisorProfile(user_id=accounts["advisor"].id, department="Test")
        lecturer = LecturerProfile(user_id=accounts["lecturer"].id, lecturer_code="TEST-L", department="Test")
        db.add_all([student, advisor, lecturer])
        course = await db.scalar(select(Course).where(Course.code_module == "AAA"))
        presentation = CoursePresentation(course_id=course.id, code_presentation=uuid.uuid4().hex[:15], module_presentation_length=268)
        db.add(presentation)
        await db.flush()
        db.add_all([AdvisorStudent(advisor_id=advisor.id, student_id=student.id, academic_year="2026", class_name="12DHTH01"),
                    CourseLecturer(lecturer_id=lecturer.id, presentation_id=presentation.id)])
        enrollment = StudentEnrollment(student_id=student.id, presentation_id=presentation.id, studied_credits=60)
        db.add(enrollment)
        await db.flush()
        snapshot = StudentFeatureSnapshot(enrollment_id=enrollment.id)
        db.add(snapshot)
        await db.flush()
        model = await db.scalar(select(MLModel).where(MLModel.is_active.is_(True)))
        prediction = PredictionRun(snapshot_id=snapshot.id, model_id=model.id, prediction_label=1, risk_probability=.95)
        db.add(prediction)
        await db.flush()
        plan = InterventionPlan(student_id=student.id, prediction_run_id=prediction.id)
        db.add(plan)
        await db.flush()
        db.add(InterventionTask(plan_id=plan.id, category="HOC_THUAT", priority="HIGH", title="Fixture task", description="Test", target_metric="Test"))
        await db.flush()
        async def isolated_db():
            yield db
        app.dependency_overrides[get_db] = isolated_db
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        await db.close()
        await transaction.rollback()
        await connection.close()
