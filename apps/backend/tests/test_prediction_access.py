"""Exercise the prediction route's real bearer-token dependency without a database."""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI

from api.v1.endpoints import predictions
from core.database import get_db
from core.security import create_access_token, create_refresh_token


class PredictionAccessTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user = SimpleNamespace(id=uuid.uuid4(), is_active=True)
        self.app = FastAPI()
        self.app.state.model = object()
        self.app.include_router(predictions.router, prefix="/api/v1/predictions")
        self.app.dependency_overrides[get_db] = lambda: None
        self.features = dict(code_module="CCC", gender="M", highest_education="HE Qualification",
            age_band="0-35", studied_credits=60, date_registration=-10,
            total_clicks_to_t=280, clicks_resource_to_t=180, clicks_url_to_t=50,
            active_days_to_t=32, active_day_ratio=.4, days_since_last_activity=2,
            clicks_recent_7=25, clicks_recent_30=100, assessments_submitted_to_t=8,
            late_submissions_to_t=1, submission_rate=.8)

    async def request(self, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
            return await client.post("/api/v1/predictions/", headers=headers, json={"features": self.features})

    async def test_anonymous_invalid_and_refresh_tokens_never_infer(self):
        with patch.object(predictions.PredictionService, "execute") as infer:
            for token in (None, "invalid", create_refresh_token({"sub": str(self.user.id)})):
                with self.subTest(token_type="missing" if token is None else "provided"):
                    response = await self.request(token)
                    self.assertEqual(response.status_code, 401, response.text)
            infer.assert_not_called()

    async def test_all_active_roles_can_infer(self):
        for role in ("STUDENT", "ADVISOR", "LECTURER", "ADMIN"):
            with self.subTest(role=role):
                self.user.roles = [SimpleNamespace(code=role)]
                with patch("core.permissions.get_user_by_id", AsyncMock(return_value=self.user)), \
                     patch.object(predictions.PredictionService, "execute", return_value={"prediction": 1, "confidence": .8}) as infer:
                    response = await self.request(create_access_token({"sub": str(self.user.id)}))
                    self.assertEqual(response.status_code, 200, response.text)
                    infer.assert_called_once()

    async def test_locked_or_deleted_accounts_never_infer(self):
        self.user.is_active = False
        with patch.object(predictions.PredictionService, "execute") as infer:
            for user, code in ((self.user, 403), (None, 404)):
                with patch("core.permissions.get_user_by_id", AsyncMock(return_value=user)):
                    response = await self.request(create_access_token({"sub": str(self.user.id)}))
                    self.assertEqual(response.status_code, code, response.text)
            infer.assert_not_called()

    async def test_authenticated_request_keeps_model_unavailable_response(self):
        self.app.state.model = None
        with patch("core.permissions.get_user_by_id", AsyncMock(return_value=self.user)):
            response = await self.request(create_access_token({"sub": str(self.user.id)}))
        self.assertEqual(response.status_code, 503)
