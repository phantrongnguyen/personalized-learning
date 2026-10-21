"""Evidence-gated, read-only suggestions for a lecturer at the course cutoff."""
from datetime import date, datetime, timedelta, timezone
from math import floor, isfinite

from services.support_evidence import REVIEW_VERSION, snapshot_digest

RULE_VERSION = "lecturer-support-1.1"


def evaluate_suggestions(snapshot, presentation, today=None):
    warnings = ["Không có dữ liệu bài và hạn nộp theo từng bài; không xác định được bài nào thiếu hoặc trễ."]
    suggestions = []
    if snapshot is None or snapshot.cutoff_stage != "CUTOFF_75":
        return "insufficient_data", suggestions, warnings + ["Chưa có snapshot hợp lệ tại cutoff 75%."], None

    raw_features = snapshot.raw_features_json
    metadata = raw_features.get("support_evidence") if isinstance(raw_features, dict) else None
    if not presentation or not presentation.module_presentation_length or presentation.module_presentation_length <= 0:
        return "insufficient_data", suggestions, warnings + ["Thiếu độ dài học phần hợp lệ."], None
    cutoff_day = floor(presentation.module_presentation_length * 0.75)
    if (not isinstance(metadata, dict) or type(metadata.get("snapshot_day")) is not int
            or metadata["snapshot_day"] != cutoff_day or not presentation.start_date
            or not isinstance(metadata.get("source"), str) or not metadata["source"].strip()
            or not isinstance(metadata.get("confirmed_at"), str) or not metadata["confirmed_at"].strip()):
        return "insufficient_data", suggestions, warnings + ["Thiếu ngày cutoff hoặc nguồn/xác nhận dữ liệu; không dùng thời gian ghi snapshot làm ngày quan sát."], None

    if (metadata.get("review_version") != REVIEW_VERSION
            or not metadata.get("confirmed_by_user_id")
            or metadata.get("review_scope") not in ("aggregate_only", "source_verified", "demonstration")
            or metadata.get("snapshot_sha256") != snapshot_digest(snapshot, presentation)):
        return "insufficient_data", suggestions, warnings + ["Chưa có xác nhận gắn với đúng nội dung snapshot và người phụ trách."], None
    if metadata["review_scope"] == "aggregate_only":
        return "insufficient_data", suggestions, warnings + ["Mới kiểm tra số liệu tổng hợp; chưa đối chiếu độ đầy đủ của nguồn LMS."], None
    if metadata["review_scope"] == "demonstration" or raw_features.get("data_source") == "synthetic_demo":
        warnings.append("Dữ liệu minh họa; gợi ý không phải bằng chứng từ LMS thực.")
    try:
        confirmed_at = datetime.fromisoformat(metadata["confirmed_at"])
    except ValueError:
        return "insufficient_data", suggestions, warnings + ["Thời điểm xác nhận không hợp lệ."], None
    if confirmed_at.tzinfo is None or confirmed_at > datetime.now(timezone.utc):
        return "insufficient_data", suggestions, warnings + ["Thời điểm xác nhận phải có múi giờ và không ở tương lai."], None
    cutoff_date = presentation.start_date + timedelta(days=cutoff_day)
    if confirmed_at.date() < cutoff_date or snapshot.created_at.date() < cutoff_date:
        return "insufficient_data", suggestions, warnings + ["Xác nhận hoặc bản ghi snapshot có trước ngày cutoff; không thể xác nhận dữ liệu đến cutoff."], cutoff_date
    if cutoff_date > (today or date.today()):
        return "abstained", suggestions, warnings + ["Ngày cutoff ở tương lai; cần kiểm tra lại mốc quan sát."], cutoff_date
    if cutoff_date < (today or date.today()):
        warnings.append("Dữ liệu chỉ phản ánh thời điểm cutoff; không phản ánh hoạt động hiện tại.")
    evidence = {"source": metadata["source"], "confirmed_at": metadata["confirmed_at"],
                "snapshot_id": str(snapshot.id), "snapshot_day": cutoff_day,
                "confirmed_by_user_id": metadata["confirmed_by_user_id"], "review_scope": metadata["review_scope"],
                "cutoff_date": cutoff_date.isoformat(), "recorded_at": snapshot.created_at.isoformat()}

    if metadata.get("assessments_complete") is True:
        late = snapshot.late_submissions_to_t
        submitted = snapshot.assessments_submitted_to_t
        rate = snapshot.submission_rate
        if (type(late) is int and type(submitted) is int and 0 < late <= submitted
                and type(rate) in (int, float) and isfinite(rate) and 0 <= rate <= 1):
            suggestions.append({"rule_id": "G02_AGGREGATE", "title": "Kiểm tra số liệu nộp trễ",
                "observation": f"Ghi nhận {late} lần nộp trễ trong số liệu tổng hợp đến cutoff.",
                "evidence": {**evidence, "late_submissions_to_t": late},
                "proposed_action": "Đối chiếu với lịch bài và trao đổi với sinh viên trước khi quyết định hỗ trợ.",
                "limitation": "Không xác định bài nào trễ; không biết hạn cá nhân, miễn bài hoặc nguyên nhân nộp trễ.",
                "rule_version": RULE_VERSION})
        elif type(late) is not int or late < 0 or type(submitted) is not int or late > submitted:
            warnings.append("Số liệu nộp trễ/tổng bài đã nộp không nhất quán; không gợi ý theo bài đánh giá.")
    else:
        warnings.append("Chưa xác nhận tính đầy đủ của dữ liệu bài đánh giá; không suy luận bài thiếu/trễ.")

    if metadata.get("activity_complete") is True:
        total, recent_7, recent_30 = snapshot.total_clicks_to_t, snapshot.clicks_recent_7, snapshot.clicks_recent_30
        if (all(type(value) is int and value >= 0 for value in (total, recent_7, recent_30))
                and recent_7 <= recent_30 <= total and type(snapshot.days_since_last_activity) is int
                and snapshot.days_since_last_activity >= 0
                and not (recent_7 > 0 and snapshot.days_since_last_activity >= 7)
                and not (recent_30 > 0 and snapshot.days_since_last_activity >= 30)
                and not (recent_7 == 0 and recent_30 > 0 and snapshot.days_since_last_activity < 7)
                and not (recent_30 == 0 and total > 0 and snapshot.days_since_last_activity < 30)):
            if total > 0 and recent_30 == 0 and snapshot.days_since_last_activity >= 30:
                rule_id, window = "G04", 30
            elif total > 0 and recent_7 == 0 and recent_30 > 0 and snapshot.days_since_last_activity >= 7:
                rule_id, window = "G03", 7
            else:
                rule_id, window = None, None
            if rule_id:
                suggestions.append({"rule_id": rule_id, "title": "Xác minh hoạt động học tập tại cutoff",
                    "observation": f"Không ghi nhận click trong {window} ngày kết thúc tại cutoff; có hoạt động trước đó.",
                    "evidence": {**evidence, "window_days": window, "window_end_day": cutoff_day,
                                 "total_clicks_to_t": total, "clicks_recent_7": recent_7,
                                 "clicks_recent_30": recent_30, "days_since_last_activity": snapshot.days_since_last_activity},
                    "proposed_action": "Xác minh cách học ngoài hệ thống hoặc khó khăn truy cập với sinh viên.",
                    "limitation": "Không có click không chứng minh ngừng học hay bỏ học; đây không phải log thời gian thực.",
                    "rule_version": RULE_VERSION})
        else:
            warnings.append("Số liệu click/mốc hoạt động mâu thuẫn hoặc không hợp lệ; không diễn giải cửa sổ thời gian.")
    else:
        warnings.append("Chưa xác nhận log hoạt động đầy đủ đến cutoff; không diễn giải 7/30 ngày.")
    if suggestions:
        return "available", suggestions, warnings, cutoff_date
    if metadata.get("activity_complete") is not True and metadata.get("assessments_complete") is not True:
        return "insufficient_data", suggestions, warnings, cutoff_date
    return "abstained", suggestions, warnings + ["Chưa có tín hiệu phù hợp quy tắc; không đồng nghĩa không cần hỗ trợ."], cutoff_date
