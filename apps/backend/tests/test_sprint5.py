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
async def test_sprint_5_admin_and_mlops():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Đăng nhập với tài khoản Admin
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@huit.edu.vn", "password": "123"},
        )
        assert admin_login.status_code == 200, admin_login.text
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Admin xem danh sách người dùng (/api/v1/admin/users)
        users_res = await client.get("/api/v1/admin/users", headers=admin_headers)
        assert users_res.status_code == 200
        users_list = users_res.json()
        assert len(users_list) >= 3

        # 3. Admin tạo mới một tài khoản sinh viên mới (/api/v1/admin/users)
        import uuid
        unique_email = f"student_{uuid.uuid4().hex[:6]}@huit.edu.vn"
        new_user_payload = {
            "email": unique_email,
            "password": "Password123!",
            "full_name": "Lê Văn Học Viên 2",
            "role_codes": ["STUDENT"],
            "student_code": f"SV_{uuid.uuid4().hex[:4]}",
            "gender": "F",
        }
        create_res = await client.post("/api/v1/admin/users", json=new_user_payload, headers=admin_headers)
        assert create_res.status_code == 200, create_res.text
        created_user = create_res.json()
        assert created_user["email"] == unique_email
        new_user_id = created_user["id"]

        # 4. Admin khóa/mở khóa tài khoản (/api/v1/admin/users/{id}/status)
        status_res = await client.put(
            f"/api/v1/admin/users/{new_user_id}/status",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert status_res.status_code == 200

        # 5. Admin xem danh sách học phần OULAD (/api/v1/admin/academic/courses)
        courses_res = await client.get("/api/v1/admin/academic/courses", headers=admin_headers)
        assert courses_res.status_code == 200
        assert len(courses_res.json()) >= 1

        # 6. Admin xem danh sách các phiên bản mô hình ML (/api/v1/admin/ml/models)
        models_res = await client.get("/api/v1/admin/ml/models", headers=admin_headers)
        assert models_res.status_code == 200
        models_list = models_res.json()
        assert len(models_list) >= 1
        assert any(model["is_active"] and model["version"] == "v1.0.0-cutoff75" for model in models_list)

        # 7. Admin nạp lại mô hình LightGBM vào bộ nhớ RAM (/api/v1/admin/ml/reload)
        reload_res = await client.post("/api/v1/admin/ml/reload", headers=admin_headers)
        assert reload_res.status_code == 200
        assert reload_res.json()["model"]["model_id"]

        # 8. Admin kích hoạt Batch Predict quét mốc Cutoff 75% (/api/v1/admin/ml/batch-predict)
        batch_res = await client.post("/api/v1/admin/ml/batch-predict", headers=admin_headers)
        assert batch_res.status_code == 200, batch_res.text
        batch_data = batch_res.json()
        assert batch_data["total_snapshots_scanned"] >= 1
        assert batch_data["predictions_generated"] >= 1
