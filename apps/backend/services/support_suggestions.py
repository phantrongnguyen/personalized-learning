"""Evidence-gated, read-only suggestions for a lecturer at the course cutoff."""
from datetime import date, datetime, timedelta, timezone
from math import floor, isfinite

RULE_VERSION = "lecturer-support-1.0"
OULAD_SOURCES = {"studentInfo", "studentRegistration", "courses", "assessments",
                 "studentAssessment", "studentVle", "vle"}


def is_historical_oulad(metadata):
    if not isinstance(metadata, dict) or metadata.get("timeline") != "relative_course_day":
        return False
    hashes = metadata.get("source_sha256")
    return (metadata.get("source") == "OULAD processed Parquet"
            and isinstance(hashes, dict) and set(hashes) == OULAD_SOURCES
            and all(isinstance(value, str) and len(value) == 64
                    and all(char in "0123456789abcdef" for char in value.lower())
                    for value in hashes.values()))


def validated_assessment_details(snapshot, metadata, cutoff_day):
    records = metadata.get("assessment_records")
    if not isinstance(records, list) or not records:
        return None
    seen = set()
    for record in records:
        if (not isinstance(record, dict) or "submitted_day" not in record
                or type(record.get("id")) is not int
                or record["id"] in seen or type(record.get("due_day")) is not int
                or not 0 <= record["due_day"] <= cutoff_day
                or not isinstance(record.get("type"), str) or not record["type"].strip()):
            return None
        seen.add(record["id"])
        submitted_day = record.get("submitted_day")
        score = record.get("score")
        if submitted_day is not None and (type(submitted_day) is not int or not 0 <= submitted_day <= cutoff_day):
            return None
        if (score is not None and (submitted_day is None or type(score) not in (int, float)
                                   or not isfinite(score) or not 0 <= score <= 100)):
            return None
    submitted = sum(record["submitted_day"] is not None for record in records)
    late = sum(record["submitted_day"] is not None and record["submitted_day"] > record["due_day"] for record in records)
    rate = snapshot.submission_rate
    if (submitted != snapshot.assessments_submitted_to_t or late != snapshot.late_submissions_to_t
            or type(rate) not in (int, float) or not isfinite(rate)
            or not 0 <= rate <= 1 or abs(rate - submitted / len(records)) > 1e-6):
        return None
    return records


def evaluate_suggestions(snapshot, presentation, today=None):
    warnings = []
    suggestions = []
    if snapshot is None or snapshot.cutoff_stage != "CUTOFF_75":
        return "insufficient_data", suggestions, warnings + ["Chưa có snapshot hợp lệ tại cutoff 75%."], None

    raw_features = snapshot.raw_features_json
    metadata = raw_features.get("support_evidence") if isinstance(raw_features, dict) else None
    if not presentation or not presentation.module_presentation_length or presentation.module_presentation_length <= 0:
        return "insufficient_data", suggestions, warnings + ["Thiếu độ dài học phần hợp lệ."], None
    cutoff_day = floor(presentation.module_presentation_length * 0.75)
    relative = is_historical_oulad(metadata)
    if isinstance(metadata, dict) and metadata.get("timeline") == "relative_course_day" and not relative:
        return "insufficient_data", suggestions, ["Nguồn OULAD lịch sử chưa được xác nhận đầy đủ."], None
    if (not isinstance(metadata, dict) or type(metadata.get("snapshot_day")) is not int
            or metadata["snapshot_day"] != cutoff_day or (not relative and not presentation.start_date)
            or not isinstance(metadata.get("source"), str) or not metadata["source"].strip()
            or not isinstance(metadata.get("confirmed_at"), str) or not metadata["confirmed_at"].strip()):
        return "insufficient_data", suggestions, warnings + ["Thiếu ngày cutoff hoặc nguồn/xác nhận dữ liệu; không dùng thời gian ghi snapshot làm ngày quan sát."], None

    try:
        confirmed_at = datetime.fromisoformat(metadata["confirmed_at"])
    except ValueError:
        return "insufficient_data", suggestions, warnings + ["Thời điểm xác nhận không hợp lệ."], None
    if confirmed_at.tzinfo is None or confirmed_at > datetime.now(timezone.utc):
        return "insufficient_data", suggestions, warnings + ["Thời điểm xác nhận phải có múi giờ và không ở tương lai."], None
    cutoff_date = None if relative else presentation.start_date + timedelta(days=cutoff_day)
    if not relative and (confirmed_at.date() < cutoff_date or snapshot.created_at.date() < cutoff_date):
        return "insufficient_data", suggestions, warnings + ["Xác nhận hoặc bản ghi snapshot có trước ngày cutoff; không thể xác nhận dữ liệu đến cutoff."], cutoff_date
    if cutoff_date is not None and cutoff_date > (today or date.today()):
        return "abstained", suggestions, warnings + ["Ngày cutoff ở tương lai; cần kiểm tra lại mốc quan sát."], cutoff_date
    if relative:
        warnings.append("OULAD là dữ liệu lịch sử theo ngày tương đối; không thể suy ra ngày lịch hoặc tình hình hiện tại của sinh viên HUIT.")
        warnings.append("Không có ánh xạ bài đánh giá với chủ đề/rubric; không xác định điểm yếu kiến thức cụ thể.")
    elif cutoff_date < (today or date.today()):
        warnings.append("Dữ liệu chỉ phản ánh thời điểm cutoff; không phản ánh hoạt động hiện tại.")
    evidence = {"source": metadata["source"], "confirmed_at": metadata["confirmed_at"],
                "snapshot_id": str(snapshot.id), "snapshot_day": cutoff_day,
                "recorded_at": snapshot.created_at.isoformat()}
    if cutoff_date is not None:
        evidence["cutoff_date"] = cutoff_date.isoformat()

    details = validated_assessment_details(snapshot, metadata, cutoff_day) if metadata.get("assessments_complete") is True else None
    if details is None:
        warnings.append("Không có dữ liệu bài và hạn nộp theo từng bài đã đối chiếu; không xác định được bài nào thiếu hoặc trễ.")
    else:
        missing = [record for record in details if record["submitted_day"] is None]
        if missing:
            labels = {"TMA": "bài giảng viên chấm", "CMA": "bài hệ thống chấm", "Exam": "bài thi"}
            samples = ", ".join(f'{labels.get(item["type"], "bài đánh giá")} (ngày thứ {item["due_day"]})' for item in missing[:3])
            suggestions.append({"rule_id": "G01", "title": "Kiểm tra bài chưa ghi nhận nộp",
                "observation": f"Có {len(missing)}/{len(details)} bài đến hạn trước mốc đánh giá chưa ghi nhận nộp: {samples}.",
                "evidence": {**evidence, "assessments_due": len(details), "assessments_missing": len(missing)},
                "proposed_action": "Đối chiếu từng bài với lịch lớp và hỏi sinh viên trước khi chọn bài bổ trợ.",
                "limitation": "Chưa biết miễn bài, hạn cá nhân, chủ đề kiến thức hoặc lý do không nộp.",
                "rule_version": RULE_VERSION})

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
                "limitation": ("Không xác định bài nào trễ; " if details is None else "")
                              + "Không biết hạn cá nhân, miễn bài hoặc nguyên nhân nộp trễ.",
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
                suggestions.append({"rule_id": rule_id, "title": "Xác minh hoạt động tại mốc đánh giá",
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
