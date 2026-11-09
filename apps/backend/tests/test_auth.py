import pytest
import httpx
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_auth_workflow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Đăng nhập sai mật khẩu -> 401
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@huit.edu.vn", "password": "wrong_password"},
        )
        assert res.status_code == 401

        # 2. Đăng nhập đúng thông tin -> 200
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@huit.edu.vn", "password": "123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 3. Lấy thông tin user hiện tại (/api/v1/auth/me) -> 200
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        user_info = res.json()
        assert user_info["email"] == "admin@huit.edu.vn"
        role_codes = [r["code"] for r in user_info["roles"]]
        assert "ADMIN" in role_codes

        # 4. Refresh Token -> 200
        res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert res.status_code == 200
        new_token_data = res.json()
        assert "access_token" in new_token_data

        # 5. Cập nhật Profile (/api/v1/auth/profile) -> 200
        res = await client.put(
            "/api/v1/auth/profile",
            json={"phone_number": "0987654321"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["phone_number"] == "0987654321"
