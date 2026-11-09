import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from api.v1.endpoints import admin
from schemas.admin import AdminUserUpdateIn, UserStatusUpdateIn


class AdminAccountTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(id=uuid.uuid4())
        self.target = SimpleNamespace(id=uuid.uuid4(), email="student@huit.edu.vn", full_name="Old name", phone_number=None,
                                      student_profile=SimpleNamespace(student_code="SV001"), advisor_profile=None, lecturer_profile=None)
        self.db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock(), execute=AsyncMock())

    def test_update_validation(self):
        self.assertEqual(AdminUserUpdateIn(full_name=" New name ").full_name, "New name")
        for payload in ({"full_name": "  "}, {"email": None}, {"role_codes": ["ADMIN"]}, {"academic_rank": "x" * 51}):
            with self.assertRaises(ValidationError):
                AdminUserUpdateIn(**payload)

    async def test_view_missing(self):
        with patch.object(admin, "_load_user_full", AsyncMock(return_value=None)):
            with self.assertRaises(HTTPException) as result:
                await admin.get_user_detail(self.target.id, self.actor, self.db)
            self.assertEqual(result.exception.status_code, 404)

    async def test_edit_profile(self):
        with patch.object(admin, "_load_user_full", AsyncMock(return_value=self.target)), patch.object(admin, "write_audit_log", AsyncMock()) as audit:
            await admin.edit_user(self.target.id, AdminUserUpdateIn(full_name="New name", student_code="SV002"), None, self.actor, self.db)
            self.assertEqual(self.target.full_name, "New name")
            self.assertEqual(self.target.student_profile.student_code, "SV002")
            self.db.commit.assert_awaited_once()
            self.assertEqual(audit.call_args.kwargs["action"], "UPDATE_USER")

    async def test_edit_wrong_profile(self):
        with patch.object(admin, "_load_user_full", AsyncMock(return_value=self.target)):
            with self.assertRaises(HTTPException) as result:
                await admin.edit_user(self.target.id, AdminUserUpdateIn(lecturer_code="GV001"), None, self.actor, self.db)
            self.assertEqual(result.exception.status_code, 400)
            self.db.commit.assert_not_awaited()

    async def test_duplicate_rollback(self):
        self.db.commit.side_effect = IntegrityError("sql", {}, Exception("duplicate"))
        with patch.object(admin, "_load_user_full", AsyncMock(return_value=self.target)), patch.object(admin, "write_audit_log", AsyncMock()):
            with self.assertRaises(HTTPException) as result:
                await admin.edit_user(self.target.id, AdminUserUpdateIn(email="used@huit.edu.vn"), None, self.actor, self.db)
            self.assertEqual(result.exception.status_code, 409)
            self.db.rollback.assert_awaited_once()

    async def test_self_delete_and_lock(self):
        with self.assertRaises(HTTPException) as result:
            await admin.delete_user(self.actor.id, None, self.actor, self.db)
        self.assertEqual(result.exception.status_code, 400)
        with self.assertRaises(HTTPException):
            await admin.toggle_user_status(self.actor.id, UserStatusUpdateIn(is_active=False), None, self.actor, self.db)
        self.db.execute.assert_not_awaited()

    async def test_delete(self):
        with patch.object(admin, "_load_user_full", AsyncMock(return_value=self.target)), patch.object(admin, "write_audit_log", AsyncMock()) as audit:
            await admin.delete_user(self.target.id, None, self.actor, self.db)
            self.db.execute.assert_awaited_once()
            self.db.commit.assert_awaited_once()
            self.assertEqual(audit.call_args.kwargs["action"], "DELETE_USER")

    async def test_routes_require_admin(self):
        app = FastAPI()
        app.include_router(admin.router, prefix="/api/v1/admin")
        async def deny():
            raise HTTPException(403, "Admin only")
        app.dependency_overrides[admin.require_admin] = deny
        app.dependency_overrides[admin.get_db] = lambda: self.db
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for method in ("GET", "PUT", "DELETE"):
                response = await client.request(method, f"/api/v1/admin/users/{self.target.id}", json={"full_name": "New name"} if method == "PUT" else None)
                self.assertEqual(response.status_code, 403)
        self.db.execute.assert_not_awaited()
