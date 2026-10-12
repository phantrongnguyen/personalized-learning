"""Authentication regression tests without a running database."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from schemas.auth import LoginRequest
from services.auth_service import authenticate_user


class LoginIdentifierTests(unittest.IsolatedAsyncioTestCase):
    def test_request_validation(self):
        self.assertEqual(LoginRequest(username=" 20012345 ", password="pw").username, "20012345")
        self.assertEqual(LoginRequest(email="admin@huit.edu.vn", password="pw").email, "admin@huit.edu.vn")
        for payload in ({}, {"username": "   "}, {"username": "20012345", "email": "admin@huit.edu.vn"}):
            with self.assertRaises(ValidationError):
                LoginRequest(password="pw", **payload)

    async def authenticate_case(self, identifier, active=True, password_valid=True, exists=True):
        user = SimpleNamespace(id="test-id", email="test@huit.edu.vn", hashed_password="hash", is_active=active, roles=[SimpleNamespace(code="STUDENT")])
        with patch("services.auth_service.get_user_by_student_code", new_callable=AsyncMock) as student_lookup, \
             patch("services.auth_service.get_user_by_email", new_callable=AsyncMock) as email_lookup, \
             patch("services.auth_service.verify_password", return_value=password_valid), \
             patch("services.auth_service.create_access_token", return_value="access"), \
             patch("services.auth_service.create_refresh_token", return_value="refresh"):
            student_lookup.return_value = email_lookup.return_value = user if exists else None
            if not exists or not password_valid or not active:
                with self.assertRaises(HTTPException) as result:
                    await authenticate_user(None, identifier, "pw")
                self.assertEqual(result.exception.status_code, 403 if exists and password_valid and not active else 401)
            else:
                _, tokens = await authenticate_user(None, identifier, "pw")
                self.assertEqual(tokens["access_token"], "access")
            expected, unused = (email_lookup, student_lookup) if "@" in identifier else (student_lookup, email_lookup)
            expected.assert_awaited_once_with(None, identifier.strip())
            unused.assert_not_awaited()

    async def test_student_code(self):
        await self.authenticate_case(" 20012345 ")

    async def test_staff_email(self):
        await self.authenticate_case("admin@huit.edu.vn")

    async def test_wrong_password(self):
        await self.authenticate_case("20012345", password_valid=False)

    async def test_unknown_student(self):
        await self.authenticate_case("20012345", exists=False)

    async def test_disabled_student(self):
        await self.authenticate_case("20012345", active=False)
