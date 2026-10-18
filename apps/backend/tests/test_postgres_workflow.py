"""Real JWT, PostgreSQL constraints, account lifecycle and intervention workflow."""
import uuid
import pytest
import httpx
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from main import app
from models.academic import StudentEnrollment
from models.feature import StudentFeatureSnapshot

pytestmark = pytest.mark.anyio


async def test_account_to_completed_intervention(integration_db):
    db = integration_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        async def call(method, path, headers=None, **kwargs):
            response = await client.request(method, "/api/v1" + path, headers=headers, **kwargs)
            assert response.status_code == 200, response.text
            return response.json()
        async def login(identifier, password="Task5-password!"):
            tokens = await call("POST", "/auth/login", json={"username": identifier, "password": password})
            return {"Authorization": "Bearer " + tokens["access_token"]}, tokens
        admin, _ = await login("admin@huit.edu.vn", "admin")
        suffix = uuid.uuid4().hex[:10]
        users = {}
        for role in ("STUDENT", "ADVISOR", "LECTURER"):
            users[role] = await call("POST", "/admin/users", admin, json={
                "email": f"{role.lower()}-{suffix}@example.com", "full_name": f"Test {role}",
                "password": "Task5-password!", "role_codes": [role],
                "student_code": f"S{suffix}" if role == "STUDENT" else None,
                "lecturer_code": f"L{suffix}" if role == "LECTURER" else None})
        student = users["STUDENT"]
        student_id = student["student_profile"]["id"]
        student_headers, tokens = await login(f"S{suffix}")  # MSSV login, not just email
        assert (await call("GET", "/auth/me", student_headers))["id"] == student["id"]
        refreshed = await call("POST", "/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refreshed["access_token"]
        await call("PUT", f'/admin/users/{student["id"]}/status', admin, json={"is_active": False})
        assert (await client.get("/api/v1/auth/me", headers=student_headers)).status_code == 403
        assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code in (401, 403)
        await call("PUT", f'/admin/users/{student["id"]}/status', admin, json={"is_active": True})
        await call("PUT", "/auth/change-password", student_headers,
                   json={"old_password": "Task5-password!", "new_password": "Changed-password!"})
        assert (await client.post("/api/v1/auth/login", json={"username": f"S{suffix}", "password": "Task5-password!"})).status_code == 401
        await login(student["email"], "Changed-password!")
        await call("PUT", f'/admin/users/{student["id"]}/reset-password', admin, json={"new_password": "Reset-password!"})
        student_headers, _ = await login(f"S{suffix}", "Reset-password!")
        await call("POST", f'/admin/users/{student["id"]}/roles', admin, json={"role_codes": ["LECTURER"]})
        assert (await client.get("/api/v1/student/courses", headers=student_headers)).status_code == 403
        await call("POST", f'/admin/users/{student["id"]}/roles', admin, json={"role_codes": ["STUDENT"]})
        courses = await call("GET", "/admin/academic/courses", admin)
        presentation = await call("POST", "/admin/academic/presentations", admin, json={
            "course_id": courses[0]["id"], "code_presentation": suffix, "module_presentation_length": 268})
        await call("POST", "/admin/academic/assign-advisor", admin, json={
            "advisor_id": users["ADVISOR"]["advisor_profile"]["id"], "student_id": student_id,
            "class_name": f"T{suffix}"})
        await call("POST", "/admin/academic/assign-lecturer", admin, json={
            "lecturer_id": users["LECTURER"]["lecturer_profile"]["id"], "presentation_id": presentation["id"]})
        # No enrollment/snapshot creation API exists: this is the import boundary.
        enrollment = StudentEnrollment(student_id=uuid.UUID(student_id), presentation_id=uuid.UUID(presentation["id"]))
        db.add(enrollment)
        await db.flush()
        risk_url = f"/student/courses/{enrollment.id}/risk-prediction"
        assert (await call("GET", risk_url, student_headers))["risk_level"] == "NOT_PREDICTED"
        db.add(StudentFeatureSnapshot(enrollment_id=enrollment.id))
        await db.flush()
        batch = await call("POST", f"/admin/ml/batch-predict?enrollment_id={enrollment.id}", admin)
        assert batch["predictions_generated"] == 1
        risk = await call("GET", risk_url, student_headers)
        assert risk["provenance_status"] == "VERIFIED"
        with pytest.raises(IntegrityError) as restricted:
            async with db.begin_nested():
                await db.execute(text("DELETE FROM ml_models WHERE id=:id"),
                                 {"id": uuid.UUID(risk["provenance"]["model_id"])})
        assert restricted.value.orig.sqlstate == "23503"
        advisor_headers, _ = await login(users["ADVISOR"]["email"])
        lecturer_headers, _ = await login(users["LECTURER"]["email"])
        for i in range(2):
            plan = await call("POST", "/advisor/interventions", advisor_headers, json={
                "student_id": student_id, "enrollment_id": str(enrollment.id),
                "tasks": [{"category": "HOC_THUAT", "priority": "HIGH", "title": f"Practice {i}", "description": "Complete exercises"}]})
            assert plan["status"] == "ACTIVE"
        await call("POST", f'/lecturer/courses/{presentation["id"]}/tasks', lecturer_headers,
                   json={"student_id": student_id, "title": "Extra practice", "description": "Review exercises"})
        tasks = await call("GET", f"/student/tasks?enrollment_id={enrollment.id}", student_headers)
        assert len(tasks) == 3
        before = await call("GET", "/student/reminders", student_headers)
        assert before[0]["pending_tasks"] == 3
        for task in tasks:
            completed = await call("PATCH", f'/student/tasks/{task["id"]}/complete', student_headers,
                                   json={"enrollment_id": str(enrollment.id), "student_feedback": "Completed"})
            assert completed["is_completed"] is True
        after = await call("GET", "/student/reminders", student_headers)
        assert not after or all(item["pending_tasks"] == 0 for item in after)
        summary = await call("GET", "/advisor/students", advisor_headers)
        assert summary[0]["uncompleted_tasks_count"] == 0
        # Document the current DB deletion contract (migration hardening is task 4).
        savepoint = await db.begin_nested()
        await db.execute(text("DELETE FROM student_feature_snapshots WHERE id=:id"),
                         {"id": uuid.UUID(risk["snapshot_id"])})
        assert await db.scalar(text("SELECT count(*) FROM prediction_runs WHERE snapshot_id=:id"),
                               {"id": uuid.UUID(risk["snapshot_id"])}) == 0
        await savepoint.rollback()
        assert len(await call("GET", f"/student/tasks?enrollment_id={enrollment.id}", student_headers)) == 3
        # A fresh imported snapshot invalidates current risk without changing old results.
        db.add(StudentFeatureSnapshot(enrollment_id=enrollment.id))
        await db.flush()
        assert (await call("GET", risk_url, student_headers))["risk_level"] == "NOT_PREDICTED"


async def test_real_constraints_and_savepoint_recovery(integration_db):
    db = integration_db
    statements = [
        ("INSERT INTO roles(code,name) VALUES ('ADMIN','duplicate')", "23505"),
        ("INSERT INTO student_enrollments(student_id,presentation_id) VALUES (gen_random_uuid(),gen_random_uuid())", "23503"),
        ("INSERT INTO student_profiles(user_id,student_code,gender,highest_education,age_band) SELECT id,'invalid-check','X','HE Qualification','0-35' FROM users LIMIT 1", "23514"),
    ]
    for statement, sqlstate in statements:
        with pytest.raises(IntegrityError) as caught:
            async with db.begin_nested():
                await db.execute(text(statement))
        assert caught.value.orig.sqlstate == sqlstate
        assert await db.scalar(text("SELECT 1")) == 1
    # Database CASCADE removes role links; raw SQL ensures ORM cascades cannot mask DB behavior.
    async with db.begin_nested():
        uid = await db.scalar(text("INSERT INTO users(email,hashed_password,full_name) VALUES ('cascade@example.com','fixture','Fixture') RETURNING id"))
        await db.execute(text("INSERT INTO user_roles SELECT :id,id FROM roles WHERE code='STUDENT'"), {"id": uid})
        await db.execute(text("DELETE FROM users WHERE id=:id"), {"id": uid})
        assert await db.scalar(text("SELECT count(*) FROM user_roles WHERE user_id=:id"), {"id": uid}) == 0
