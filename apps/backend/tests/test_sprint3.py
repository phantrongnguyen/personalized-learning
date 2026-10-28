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
async def test_sprint_3_advisor_and_lecturer():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Đăng nhập với tài khoản Giáo viên Chủ nhiệm (Advisor)
        adv_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "advisor@huit.edu.vn", "password": "123"},
        )
        assert adv_login.status_code == 200, adv_login.text
        adv_token = adv_login.json()["access_token"]
        adv_headers = {"Authorization": f"Bearer {adv_token}"}

        # 2. GVCN xem danh sách các lớp sinh hoạt (/api/v1/advisor/classes)
        classes_res = await client.get("/api/v1/advisor/classes", headers=adv_headers)
        assert classes_res.status_code == 200
        classes_data = classes_res.json()
        assert len(classes_data) >= 1
        assert classes_data[0]["class_name"] == "12DHTH01"

        # 3. GVCN xem danh sách sinh viên lớp chủ nhiệm kèm cảnh báo rủi ro (/api/v1/advisor/students)
        students_res = await client.get("/api/v1/advisor/students", headers=adv_headers)
        assert students_res.status_code == 200
        students = students_res.json()
        assert len(students) >= 1
        target_student = students[0]
        student_id = target_student["student_id"]
        assert target_student["risk_level"] == "HIGH_RISK"

        # 4. GVCN Lập Kế hoạch can thiệp 4 nhóm cho sinh viên (/api/v1/advisor/interventions)
        plan_payload = {
            "student_id": student_id,
            "target_completion_date": "2026-11-20",
            "advisor_note_summary": "Sinh viên cần tăng tương tác và làm bài tập bổ trợ môn CSDL",
            "tasks": [
                {
                    "category": "CHUYEN_CAN",
                    "priority": "HIGH",
                    "title": "Tăng số ngày truy cập VLE",
                    "description": "Đăng nhập LMS tối thiểu 3 ngày/tuần",
                    "target_metric": "3 ngày/tuần",
                },
                {
                    "category": "HOC_THUAT",
                    "priority": "HIGH",
                    "title": "Làm bài tập TMA bổ sung",
                    "description": "Nộp bù bài tập số 2 trước ngày 15/11",
                    "target_metric": "Điểm >= 6.0",
                },
            ],
        }
        plan_res = await client.post("/api/v1/advisor/interventions", json=plan_payload, headers=adv_headers)
        assert plan_res.status_code == 200, plan_res.text
        plan_data = plan_res.json()
        assert plan_data["status"] == "ACTIVE"
        assert len(plan_data["tasks"]) == 2

        # 5. Đăng nhập với tài khoản Giảng viên bộ môn (Lecturer)
        lec_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "lecturer@huit.edu.vn", "password": "123"},
        )
        assert lec_login.status_code == 200, lec_login.text
        lec_token = lec_login.json()["access_token"]
        lec_headers = {"Authorization": f"Bearer {lec_token}"}

        # 6. GVBM xem danh sách học phần giảng dạy (/api/v1/lecturer/courses)
        courses_res = await client.get("/api/v1/lecturer/courses", headers=lec_headers)
        assert courses_res.status_code == 200
        courses = courses_res.json()
        assert len(courses) >= 1
        pres_id = courses[0]["presentation_id"]

        # 7. GVBM xem Bảng cảnh báo nguy cơ học phần (Risk Board)
        risk_board_res = await client.get(f"/api/v1/lecturer/courses/{pres_id}/risk-board", headers=lec_headers)
        assert risk_board_res.status_code == 200
        board = risk_board_res.json()
        assert len(board) >= 1
        assert board[0]["risk_status"] == "HIGH_RISK"

        # 8. GVBM giao bài tập bổ trợ môn học cho sinh viên (/api/v1/lecturer/courses/{pres_id}/tasks)
        task_payload = {
            "student_id": student_id,
            "title": "Bài tập bổ trợ môn CSDL Nâng cao",
            "description": "Thực hành truy vấn SQL phức tạp",
            "priority": "HIGH",
            "target_metric": "Hoàn thành 10 câu truy vấn",
        }
        assign_res = await client.post(
            f"/api/v1/lecturer/courses/{pres_id}/tasks",
            json=task_payload,
            headers=lec_headers,
        )
        assert assign_res.status_code == 200, assign_res.text
        assert assign_res.json()["title"] == "Bài tập bổ trợ môn CSDL Nâng cao"

        # 9. GVBM gửi cảnh báo học vụ tới GVCN
        alert_payload = {
            "presentation_id": pres_id,
            "subject": "Sinh viên vắng tương tác 2 tuần liên tiếp",
            "content": "Sinh viên không nộp bài tập TMA đúng hạn, cần GVCN trao đổi trực tiếp",
        }
        alert_res = await client.post(
            f"/api/v1/lecturer/students/{student_id}/alert-advisor",
            json=alert_payload,
            headers=lec_headers,
        )
        assert alert_res.status_code == 200
        assert "alert_id" in alert_res.json()
