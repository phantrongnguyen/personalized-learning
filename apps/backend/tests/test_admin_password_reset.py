import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from api.v1.endpoints import admin
from schemas.admin import AdminPasswordResetIn
from core.security import verify_password


class AdminPasswordResetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.actor = SimpleNamespace(id=uuid.uuid4())
        self.target = SimpleNamespace(id=uuid.uuid4(), hashed_password="old-hash", is_active=False)
        self.db = SimpleNamespace(get=AsyncMock(return_value=self.target), commit=AsyncMock(), rollback=AsyncMock())

    def test_validation(self):
        self.assertNotIn("test-password", repr(AdminPasswordResetIn(new_password="test-password")))
        for value in ("12345", " " * 6, "a" * 73, "ệ" * 25):
            with self.assertRaises(ValidationError):
                AdminPasswordResetIn(new_password=value)
        AdminPasswordResetIn(new_password="a" * 72)
        AdminPasswordResetIn(new_password="ệ" * 24)
        with self.assertRaises(ValidationError):
            AdminPasswordResetIn(new_password="test-password", role_codes=["ADMIN"])

    async def test_reset_hash_and_audit(self):
        with patch.object(admin, "write_audit_log", AsyncMock()) as audit:
            result = await admin.reset_user_password(self.target.id, AdminPasswordResetIn(new_password="test-password"), None, self.actor, self.db)
            self.assertTrue(verify_password("test-password", self.target.hashed_password))
            self.assertNotEqual(self.target.hashed_password, "test-password")
            self.assertFalse(self.target.is_active)
            self.assertEqual(set(result), {"message", "user_id"})
            self.assertNotIn("test-password", str(audit.call_args))
            self.assertNotIn(self.target.hashed_password, str(audit.call_args))
            self.assertEqual(audit.call_args.kwargs["action"], "RESET_USER_PASSWORD")
            self.db.commit.assert_awaited_once()

    async def test_missing_user(self):
        self.db.get.return_value = None
        with self.assertRaises(HTTPException) as result:
            await admin.reset_user_password(self.target.id, AdminPasswordResetIn(new_password="test-password"), None, self.actor, self.db)
        self.assertEqual(result.exception.status_code, 404)
        self.db.commit.assert_not_awaited()

    async def test_transaction_failure(self):
        self.db.commit.side_effect = RuntimeError("commit failed")
        with patch.object(admin, "write_audit_log", AsyncMock()):
            with self.assertRaises(RuntimeError):
                await admin.reset_user_password(self.target.id, AdminPasswordResetIn(new_password="test-password"), None, self.actor, self.db)
        self.db.rollback.assert_awaited_once()

    async def test_non_admin_denied(self):
        app = FastAPI()
        app.include_router(admin.router, prefix="/api/v1/admin")
        async def deny():
            raise HTTPException(403, "Admin only")
        app.dependency_overrides[admin.require_admin] = deny
        app.dependency_overrides[admin.get_db] = lambda: self.db
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            result = await client.put(f"/api/v1/admin/users/{self.target.id}/reset-password", json={"new_password": "test-password"})
            self.assertEqual(result.status_code, 403)
        self.db.get.assert_not_awaited()
