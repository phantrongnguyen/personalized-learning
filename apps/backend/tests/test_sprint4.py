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
async def test_sprint_4_student_interactive():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Đăng nhập với tài khoản Sinh viên (Student)
        stu_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "student@huit.edu.vn", "password": "123"},
        )
        assert stu_login.status_code == 200, stu_login.text
        stu_token = stu_login.json()["access_token"]
        stu_headers = {"Authorization": f"Bearer {stu_token}"}

        # 2. Sinh viên xem hồ sơ cá nhân và số tín chỉ tích lũy (/api/v1/student/profile)
        prof_res = await client.get("/api/v1/student/profile", headers=stu_headers)
        assert prof_res.status_code == 200, prof_res.text
        prof_data = prof_res.json()
        assert prof_data["student_code"] == "SV001"
        assert prof_data["studied_credits_total"] == 60

        # 3. Sinh viên xem danh sách các môn học đang theo học (/api/v1/student/courses)
        courses_res = await client.get("/api/v1/student/courses", headers=stu_headers)
        assert courses_res.status_code == 200
        courses = courses_res.json()
        assert len(courses) >= 1
        enrollment_id = courses[0]["enrollment_id"]

        # 4. Sinh viên xem dự báo nguy cơ môn học tại Cutoff 75% (/api/v1/student/courses/{id}/risk-prediction)
        risk_res = await client.get(f"/api/v1/student/courses/{enrollment_id}/risk-prediction", headers=stu_headers)
        assert risk_res.status_code == 200, risk_res.text
        risk_data = risk_res.json()
        assert risk_data["risk_level"] == "HIGH_RISK"
        assert len(risk_data["pedagogical_recommendations"]) >= 1

        # 5. Sinh viên xem Biểu đồ Radar Năng lực 6 chiều đối sánh Benchmark Top 25% (/api/v1/student/courses/{id}/radar)
        radar_res = await client.get(f"/api/v1/student/courses/{enrollment_id}/radar", headers=stu_headers)
        assert radar_res.status_code == 200, radar_res.text
        radar_data = radar_res.json()
        assert len(radar_data["dimensions"]) == 6
        metric_names = [d["metric"] for d in radar_data["dimensions"]]
        assert "Tổng tương tác VLE" in metric_names
        assert "Kỷ luật đúng hạn" in metric_names

        # 6. Sinh viên xem Checklist nhiệm vụ can thiệp (/api/v1/student/tasks)
        tasks_res = await client.get("/api/v1/student/tasks", headers=stu_headers)
        assert tasks_res.status_code == 200
        tasks = tasks_res.json()
        assert len(tasks) >= 1
        task_id = tasks[0]["id"]

        # 7. Sinh viên bấm hoàn thành nhiệm vụ kèm gửi feedback (/api/v1/student/tasks/{id}/complete)
        complete_res = await client.patch(
            f"/api/v1/student/tasks/{task_id}/complete",
            json={"student_feedback": "Em đã hoàn thành bài tập nộp bù TMA số 2"},
            headers=stu_headers,
        )
        assert complete_res.status_code == 200, complete_res.text
        completed_task = complete_res.json()
        assert completed_task["is_completed"] is True
        assert completed_task["student_feedback"] == "Em đã hoàn thành bài tập nộp bù TMA số 2"

        # 8. Sinh viên gửi yêu cầu trợ giúp học vụ tới Cố vấn học tập (/api/v1/student/help-requests)
        help_payload = {
            "target_role": "ADVISOR",
            "subject": "Xin lịch hẹn tư vấn phương pháp ôn thi cuối kỳ",
            "content": "Thưa thầy, em muốn xin lịch gặp online để trao đổi thêm về kế hoạch cải thiện điểm số.",
        }
        help_res = await client.post("/api/v1/student/help-requests", json=help_payload, headers=stu_headers)
        assert help_res.status_code == 200, help_res.text
        help_data = help_res.json()
        assert help_data["status"] == "PENDING"
        assert help_data["target_role"] == "ADVISOR"

        # 9. Sinh viên xem danh sách các yêu cầu trợ giúp đã gửi
        list_help_res = await client.get("/api/v1/student/help-requests", headers=stu_headers)
        assert list_help_res.status_code == 200
        assert len(list_help_res.json()) >= 1
