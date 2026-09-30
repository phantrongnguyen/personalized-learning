from functools import lru_cache
import json
from time import perf_counter

from fastapi import HTTPException

from app.schemas.support import LearningEvidence, SupportInput
from app.services.prediction import BACKEND, catalog, predict, validate_course

RULE_VERSION = "goi-y-1.0"
CASES_PATH = BACKEND / "app" / "core" / "support_cases.json"


def assessment_evidence(evidence: LearningEvidence):
    cutoff = evidence.snapshot_day
    due = [record for record in evidence.assessments
           if record.due_day is not None and record.due_day <= cutoff]
    submitted = [record for record in evidence.assessments if record.submitted_day is not None]
    completed = [record for record in due if record.submitted_day is not None]
    missing = [record for record in due if record.submitted_day is None and not record.is_exempt]
    late = [record for record in submitted if not record.is_banked and not record.is_exempt
            and record.due_day is not None and record.submitted_day > record.due_day]
    return {
        "due": len(due), "submitted": len(submitted), "completed_due": len(completed),
        "missing": len(missing), "late": len(late),
        "missing_ids": [record.assessment_id for record in missing],
        "late_ids": [record.assessment_id for record in late],
        "unknown_deadlines": sum(record.due_day is None for record in evidence.assessments),
        "exempt_due": sum(record.is_exempt for record in due),
        "early_future": sum(record.due_day is not None and record.due_day > cutoff for record in submitted),
    }


def recommend(payload: SupportInput):
    evidence = payload.evidence
    features = payload.features
    summary = assessment_evidence(evidence)
    warnings = []
    suggestions = []
    if evidence.enrollment_active is not True:
        return {
            "status": "abstained", "suggestions": [], "assessment_summary": None,
            "warnings": ["Chưa xác nhận người học còn theo học tại cutoff; không sinh lời khuyên."],
        }
    if evidence.assessments_complete:
        if summary["unknown_deadlines"]:
            warnings.append(f'{summary["unknown_deadlines"]} bài chưa có hạn xác định; không kết luận thiếu các bài này.')
        if summary["missing"]:
            suggestions.append({
                "rule_id": "G01", "title": "Kiểm tra các bài đến hạn",
                "observation": f'{summary["missing"]} bài đến hạn chưa có bản ghi hoàn thành.',
                "evidence": [f'{summary["due"]} bài có hạn không sau ngày {evidence.snapshot_day}.',
                             f'{summary["completed_due"]} bài trong số đó đã có bản ghi nộp.',
                             'Mã minh họa cần kiểm tra: ' + ', '.join(summary["missing_ids"])],
                "action": "Kiểm tra trạng thái từng bài. Nếu thực sự còn thiếu, trao đổi với giảng viên về cách hoàn thành hoặc hỗ trợ phù hợp.",
                "limitation": "Hạn chung có thể khác gia hạn cá nhân. Không khẳng định vẫn được nộp muộn hoặc điểm sẽ tăng.",
            })
    else:
        warnings.append("Chưa xác nhận đủ danh sách bài đánh giá; không dùng tổng bài nộp để đoán bài còn thiếu hoặc nộp trễ.")
    if not evidence.activity_complete:
        warnings.append("Log hoạt động chưa được xác nhận đầy đủ đến cutoff; không suy ra ngừng tương tác.")
    elif features.total_clicks_to_t == 0:
        warnings.append("Chưa có lịch sử tương tác; cần xác minh cách học hoặc dữ liệu, không kết luận ngừng học.")
    elif features.clicks_recent_30 == 0:
        suggestions.append({
            "rule_id": "G04", "title": "Xác nhận tình trạng học hiện tại",
            "observation": "Không ghi nhận click trong 30 ngày gần nhất, dù có lịch sử trước đó.",
            "evidence": [f'0 click từ ngày {evidence.snapshot_day - 29} đến {evidence.snapshot_day}.',
                         f'{features.total_clicks_to_t} click tích lũy đến cutoff, có thể gồm trước ngày mở môn.'],
            "action": "Xác nhận bạn đang học ngoại tuyến hay gặp trở ngại. Nếu cần, trao đổi với giảng viên hoặc cố vấn về việc tiếp tục học.",
            "limitation": "Không có click không đồng nghĩa không học, đã bỏ học hay chắc chắn không đạt.",
        })
    elif features.clicks_recent_7 == 0:
        suggestions.append({
            "rule_id": "G03", "title": "Nhìn lại tiến độ tuần vừa qua",
            "observation": "Không ghi nhận click 7 ngày gần đây, nhưng trước đó trong tháng vẫn có hoạt động.",
            "evidence": [f'0 click từ ngày {evidence.snapshot_day - 6} đến {evidence.snapshot_day}.',
                         f'{features.clicks_recent_30} click trong 30 ngày gần nhất.'],
            "action": "Kiểm tra bạn có đang học ngoài hệ thống hoặc cần hỗ trợ truy cập không; xác định việc học muốn tiếp nối.",
            "limitation": "Chưa có nội dung bài học để chỉ ra chương yếu; không khẳng định bạn đã ngừng học 7 ngày.",
        })
    if evidence.assessments_complete and summary["late"]:
        suggestions.append({
            "rule_id": "G02", "title": "Sắp xếp tiến độ nộp bài",
            "observation": f'{summary["late"]} bài mới từng được nộp sau hạn chung.',
            "evidence": ['Mã minh họa nộp trễ: ' + ', '.join(summary["late_ids"]),
                         "Chỉ đếm bài đã nộp đến cutoff; không tính bài bảo lưu hoặc được miễn."],
            "action": "Nếu lịch học đang khó sắp xếp, thử chia bài thành các bước và đặt lịch nhắc trước hạn; xác nhận nguyên nhân trước khi điều chỉnh.",
            "limitation": "Từng nộp trễ không đồng nghĩa kiến thức yếu. Gia hạn cá nhân có thể chưa có trong dữ liệu.",
        })
    if not suggestions:
        warnings.append("Chưa đủ căn cứ để đưa ra gợi ý cụ thể trong bốn tình huống; không có nghĩa người học chắc chắn không gặp khó khăn.")
    return {
        "status": "available" if suggestions else "abstained",
        "suggestions": suggestions, "warnings": warnings,
        "assessment_summary": summary if evidence.assessments_complete else None,
    }


def evaluate_support(payload: SupportInput):
    started = perf_counter()
    course = validate_course(payload.features)
    evidence = payload.evidence
    if evidence.snapshot_day != course["cutoff_day"]:
        raise HTTPException(422, "Ngày bằng chứng phải đúng cutoff 75% của học phần/kỳ đang chọn.")
    summary = assessment_evidence(evidence)
    if evidence.assessments_complete:
        expected = (summary["due"], summary["submitted"])
        actual = (payload.features.assessments_due_to_t, payload.features.assessments_submitted_to_t)
        raw_late = sum(record.submitted_day is not None and record.due_day is not None
                       and record.submitted_day > record.due_day for record in evidence.assessments)
        if expected != actual or raw_late != payload.features.late_submissions_to_t:
            raise HTTPException(422, "Chi tiết bài đánh giá không khớp số tổng hợp. Kiểm tra lại trước khi dự báo.")
    output = recommend(payload)
    prediction = None
    if evidence.enrollment_active is True and evidence.feature_data_confirmed:
        prediction = predict(payload.features)
    else:
        output["warnings"].insert(0, "Chưa chạy model: cần xác nhận dữ liệu đặc trưng tại cutoff và tình trạng còn theo học.")
    return {
        **output, "prediction": prediction, "rule_version": RULE_VERSION,
        "cutoff_day": course["cutoff_day"], "cutoff_fraction": .75,
        "course": f'{course["code_module"]} · {course["code_presentation"]}',
        "runtime_ms": round((perf_counter() - started) * 1000, 2),
        "notice": "Gợi ý theo quy tắc có giải thích, chưa được chứng minh làm tăng điểm. HCO–VNLS chọn đặc trưng cho dự báo, không trực tiếp tối ưu các lời khuyên này.",
    }


@lru_cache(maxsize=1)
def demo_cases():
    if not CASES_PATH.exists():
        raise HTTPException(503, "Chưa có hồ sơ minh họa. Chạy notebook 11 để tạo dữ liệu demo.")
    content = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    for case in content:
        SupportInput.model_validate(case["payload"])
    return content


def evaluate_case(case_id: str):
    case = next((case for case in demo_cases() if case["id"] == case_id), None)
    if case is None:
        raise HTTPException(404, "Không tìm thấy hồ sơ minh họa.")
    return {**evaluate_support(SupportInput.model_validate(case["payload"])),
            "case_id": case["id"], "case_title": case["title"], "source_notice": case["source_notice"]}
