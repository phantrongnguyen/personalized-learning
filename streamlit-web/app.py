"""Ứng dụng độc lập: chỉ cần app.py và model trong cùng thư mục.

Python 3.12. Cài thư viện:
python -m pip install streamlit==1.64.0 numpy==2.2.6 pandas==2.2.2 scikit-learn==1.6.0 lightgbm==4.7.0 joblib==1.4.2

Chạy trong thư mục chứa file:
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false

HCO–VNLS chọn 17 đặc trưng; pipeline LightGBM tự tạo 30 cột số.
Model chỉ dùng cutoff 75%. Gợi ý là quy tắc có căn cứ, không phải bằng
chứng nhân quả hoặc cam kết cải thiện điểm. Không lưu thông tin nhập lên đĩa.
"""

from hashlib import sha256
from math import floor, isfinite
from pathlib import Path
import re

import joblib
import pandas as pd
import streamlit as st


MODEL_PATH = Path(__file__).resolve().parent / "model_hco_vnls_lightgbm_cutoff75.joblib"
MODEL_SHA256 = "90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db"
COURSES = {
    "AAA": {"2013J": 268, "2014J": 269},
    "BBB": {"2013J": 268, "2014J": 262, "2013B": 240, "2014B": 234},
    "CCC": {"2014J": 269, "2014B": 241},
    "DDD": {"2013J": 261, "2014J": 262, "2013B": 240, "2014B": 241},
    "EEE": {"2013J": 268, "2014J": 269, "2014B": 241},
    "FFF": {"2013J": 268, "2014J": 269, "2013B": 240, "2014B": 241},
    "GGG": {"2013J": 261, "2014J": 269, "2014B": 241},
}
GENDER = {"F": "Nữ", "M": "Nam"}
AGE = {"0-35": "0–35 tuổi", "35-55": "35–55 tuổi", "55<=": "Từ 55 tuổi (nhóm 55<= của nguồn)"}
EDUCATION = {
    "Lower Than A Level": "Dưới A Level",
    "A Level or Equivalent": "A Level hoặc tương đương",
    "HE Qualification": "Văn bằng giáo dục đại học",
    "Post Graduate Qualification": "Văn bằng sau đại học",
    "No Formal quals": "Không có văn bằng chính quy",
}
TABLE_COLUMNS = ["Mã bài", "Hạn nộp (ngày)", "Ngày đã nộp", "Bảo lưu", "Được miễn"]
FEATURES = [
    "code_module", "gender", "highest_education", "age_band", "studied_credits",
    "date_registration", "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
    "active_days_to_t", "assessments_submitted_to_t", "late_submissions_to_t",
    "active_day_ratio", "submission_rate", "days_since_last_activity", "clicks_recent_7",
    "clicks_recent_30",
]
SAMPLES = {
    "Cần kiểm tra bài đến hạn": {
        "features": {
            "code_module": "AAA", "code_presentation": "2013J", "gender": "F",
            "highest_education": "HE Qualification", "age_band": "35-55", "studied_credits": 60,
            "date_registration": -43, "total_clicks_to_t": 2026, "clicks_resource_to_t": 15,
            "clicks_url_to_t": 41, "active_days_to_t": 113, "last_activity_day": 200,
            "clicks_recent_7": 130, "clicks_recent_30": 195,
        },
        "assessments": [
            ["B01", 19, 10, False, False], ["B02", 54, None, False, False],
            ["B03", 117, 117, False, False], ["B04", 166, None, False, False],
            ["B05", 215, None, False, False], ["B06", None, None, False, False],
        ],
    },
    "Một tuần chưa có tương tác": {
        "features": {
            "code_module": "AAA", "code_presentation": "2013J", "gender": "F",
            "highest_education": "Lower Than A Level", "age_band": "0-35", "studied_credits": 60,
            "date_registration": -176, "total_clicks_to_t": 907, "clicks_resource_to_t": 37,
            "clicks_url_to_t": 10, "active_days_to_t": 58, "last_activity_day": 192,
            "clicks_recent_7": 0, "clicks_recent_30": 72,
        },
        "assessments": [
            ["B01", 19, 26, False, False], ["B02", 54, 75, False, False],
            ["B03", 117, 124, False, False], ["B04", 166, 181, False, False],
            ["B05", 215, None, False, False], ["B06", None, None, False, False],
        ],
    },
    "Nộp sớm không bù được bài thiếu": {
        "features": {
            "code_module": "BBB", "code_presentation": "2013B", "gender": "F",
            "highest_education": "A Level or Equivalent", "age_band": "0-35", "studied_credits": 60,
            "date_registration": -50, "total_clicks_to_t": 866, "clicks_resource_to_t": 124,
            "clicks_url_to_t": 23, "active_days_to_t": 32, "last_activity_day": 176,
            "clicks_recent_7": 81, "clicks_recent_30": 310,
        },
        "assessments": [
            ["B01", 19, 18, False, False], ["B02", 47, 46, False, False],
            ["B03", 54, 60, False, False], ["B04", 89, 88, False, False],
            ["B05", 89, 95, False, False], ["B06", 124, None, False, False],
            ["B07", 124, 126, False, False], ["B08", 159, 158, False, False],
            ["B09", 159, 164, False, False], ["B10", 187, 176, False, False],
            ["B11", 187, None, False, False], ["B12", None, None, False, False],
        ],
    },
}


@st.cache_resource(show_spinner="Đang nạp model…")
def load_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Đặt {MODEL_PATH.name} cạnh app.py.")
    if sha256(MODEL_PATH.read_bytes()).hexdigest() != MODEL_SHA256:
        raise ValueError("File model không đúng phiên bản đã kiểm chứng; không nạp file này.")
    artifact = joblib.load(MODEL_PATH)
    if artifact["feature_columns"] != FEATURES or artifact["cutoff_fraction"] != 0.75:
        raise ValueError("Đặc trưng hoặc cutoff của model không phù hợp với biểu mẫu.")
    return artifact


def parse_day(value, label, minimum=-1000, maximum=2000):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label}: nhập ngày bằng số nguyên, hoặc để trống nếu chưa biết.") from None
    if not isfinite(number) or not number.is_integer() or not minimum <= number <= maximum:
        raise ValueError(f"{label}: ngày phải là số nguyên từ {minimum} đến {maximum}.")
    return int(number)


def normalize_assessments(table, cutoff_day):
    if len(table) > 200:
        raise ValueError("Tối đa 200 bài đánh giá cho một học phần/kỳ học.")
    records = []
    seen = set()
    for position, row in enumerate(table.to_dict("records"), start=1):
        identifier = "" if pd.isna(row.get("Mã bài")) else str(row.get("Mã bài", "")).strip()
        due = parse_day(row.get("Hạn nộp (ngày)"), f"Bài dòng {position}, hạn nộp")
        submitted = parse_day(row.get("Ngày đã nộp"), f"Bài dòng {position}, ngày nộp")
        banked = bool(row.get("Bảo lưu", False))
        exempt = bool(row.get("Được miễn", False))
        if not identifier and due is None and submitted is None and not banked and not exempt:
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", identifier):
            raise ValueError(f"Bài dòng {position}: mã bài cần 1–32 ký tự chữ, số, dấu gạch ngang hoặc gạch dưới.")
        if identifier in seen:
            raise ValueError(f"Mã bài {identifier} bị lặp; mỗi bài chỉ có một dòng.")
        if submitted is not None and submitted > cutoff_day:
            raise ValueError(f"Bài {identifier}: không sử dụng lần nộp sau ngày cutoff {cutoff_day}.")
        if banked and submitted is None:
            raise ValueError(f"Bài {identifier}: bài bảo lưu cần ngày ghi nhận hoàn thành.")
        seen.add(identifier)
        records.append({"id": identifier, "due": due, "submitted": submitted,
                        "banked": banked, "exempt": exempt})
    return records


def assessment_summary(records, cutoff_day):
    due = [record for record in records if record["due"] is not None and record["due"] <= cutoff_day]
    submitted = [record for record in records if record["submitted"] is not None]
    raw_late = [record for record in submitted if record["due"] is not None and record["submitted"] > record["due"]]
    missing = [record for record in due if record["submitted"] is None and not record["exempt"]]
    return {
        "due": len(due), "submitted": len(submitted), "raw_late": len(raw_late),
        "completed_due": sum(record["submitted"] is not None for record in due),
        "missing_ids": [record["id"] for record in missing],
        "late_ids": [record["id"] for record in raw_late if not record["banked"] and not record["exempt"]],
        "unknown_deadlines": sum(record["due"] is None for record in records),
        "early_future": sum(record["due"] is not None and record["due"] > cutoff_day for record in submitted),
    }


def validate_features(raw, cutoff_day):
    errors = []
    for feature, choices in (("gender", GENDER), ("highest_education", EDUCATION), ("age_band", AGE)):
        if raw.get(feature) not in choices:
            errors.append("Cần chọn đầy đủ giới tính, nhóm tuổi và trình độ học vấn.")
            break
    numeric = ["studied_credits", "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
               "active_days_to_t", "clicks_recent_7", "clicks_recent_30"]
    for feature in numeric:
        value = raw.get(feature)
        if value is None or not isfinite(float(value)) or value < 0 or not float(value).is_integer():
            errors.append(f"{feature}: cần số nguyên không âm.")
    if errors:
        return errors
    if raw["studied_credits"] > 1000:
        errors.append("Số tín chỉ phải từ 0 đến 1.000.")
    total = raw["total_clicks_to_t"]
    last = raw["last_activity_day"]
    if raw["date_registration"] is not None and raw["date_registration"] > cutoff_day:
        errors.append("Ngày đăng ký không được sau cutoff của hồ sơ đang theo học.")
    if not raw["clicks_recent_7"] <= raw["clicks_recent_30"] <= total:
        errors.append("Lượt tương tác 7 ngày ≤ 30 ngày ≤ tổng lượt tương tác.")
    if raw["clicks_resource_to_t"] + raw["clicks_url_to_t"] > total:
        errors.append("Tổng tương tác tài liệu và liên kết không được vượt tổng tương tác.")
    if raw["active_days_to_t"] > total:
        errors.append("Số ngày hoạt động không được vượt tổng lượt tương tác.")
    if total == 0:
        if raw["active_days_to_t"] != 0 or last is not None:
            errors.append("Chưa có tương tác: số ngày hoạt động phải bằng 0 và ngày hoạt động cuối để trống.")
    elif last is None or raw["active_days_to_t"] == 0:
        errors.append("Đã có tương tác: cần ngày hoạt động cuối và số ngày hoạt động lớn hơn 0.")
    elif last > cutoff_day:
        errors.append("Ngày hoạt động cuối không được sau cutoff.")
    else:
        gap = cutoff_day - last
        if (gap < 7) != (raw["clicks_recent_7"] > 0):
            errors.append("Ngày hoạt động cuối không khớp lượt tương tác 7 ngày: kiểm tra cửa sổ từ cutoff − 6 đến cutoff.")
        if (gap < 30) != (raw["clicks_recent_30"] > 0):
            errors.append("Ngày hoạt động cuối không khớp lượt tương tác 30 ngày: kiểm tra cửa sổ từ cutoff − 29 đến cutoff.")
    return errors


def build_suggestions(raw, summary, flags, probability, threshold):
    suggestions = []
    warnings = []
    if not flags["enrollment_active"]:
        return [], ["Chưa xác nhận người học còn theo học tại cutoff; chưa đưa ra gợi ý."]
    priority = "Xem xét sớm" if probability is not None and probability >= threshold else "Theo dõi và kiểm tra"
    if flags["assessments_complete"]:
        if summary["unknown_deadlines"]:
            warnings.append(f'{summary["unknown_deadlines"]} bài chưa rõ hạn nộp; không kết luận thiếu các bài này.')
        if summary["missing_ids"]:
            suggestions.append({
                "rule_id": "G01", "title": "Kiểm tra các bài đến hạn", "priority": "Kiểm tra bài đến hạn",
                "evidence": f'{summary["due"]} bài đến hạn; {summary["completed_due"]} bài trong số đó có ghi nhận nộp. Bài cần kiểm tra: {", ".join(summary["missing_ids"])}.',
                "action": "Kiểm tra trạng thái từng bài. Nếu thực sự còn thiếu, trao đổi với giảng viên về cách hoàn thành hoặc hỗ trợ phù hợp.",
                "limitation": "Hạn chung có thể khác gia hạn cá nhân; không mặc định vẫn được nộp muộn.",
            })
        if summary["late_ids"]:
            suggestions.append({
                "rule_id": "G02", "title": "Sắp xếp tiến độ nộp bài", "priority": priority,
                "evidence": "Các bài nộp sau hạn chung: " + ", ".join(summary["late_ids"]) + ". Không tính bài bảo lưu hoặc được miễn trong gợi ý này.",
                "action": "Xác nhận nguyên nhân nộp trễ; thử chia bài thành từng bước và đặt lịch nhắc trước hạn nếu phù hợp.",
                "limitation": "Nộp trễ không đồng nghĩa kiến thức yếu; dữ liệu có thể chưa phản ánh gia hạn cá nhân.",
            })
    else:
        warnings.append("Danh sách bài đánh giá chưa được xác nhận đầy đủ; chưa kết luận bài thiếu hoặc nộp trễ.")
    if not flags["activity_complete"]:
        warnings.append("Log hoạt động chưa được xác nhận đầy đủ; không suy ra gián đoạn học từ số tương tác bằng 0.")
    elif raw["total_clicks_to_t"] == 0:
        warnings.append("Chưa có lịch sử tương tác; cần xác minh dữ liệu hoặc cách học ngoài hệ thống.")
    elif raw["clicks_recent_30"] == 0:
        suggestions.append({
            "rule_id": "G04", "title": "Xác nhận tình trạng học hiện tại", "priority": priority,
            "evidence": f'Không ghi nhận tương tác 30 ngày gần cutoff, dù đã có {raw["total_clicks_to_t"]} lượt tương tác trước đó.',
            "action": "Xác nhận đang học ngoại tuyến hay gặp trở ngại. Nếu cần, trao đổi với giảng viên hoặc cố vấn về hỗ trợ tiếp tục học.",
            "limitation": "Không có tương tác trên hệ thống không đồng nghĩa đã bỏ học.",
        })
    elif raw["clicks_recent_7"] == 0:
        suggestions.append({
            "rule_id": "G03", "title": "Nhìn lại tiến độ tuần vừa qua", "priority": priority,
            "evidence": f'Không ghi nhận tương tác 7 ngày gần cutoff; 30 ngày vẫn có {raw["clicks_recent_30"]} lượt.',
            "action": "Kiểm tra có học ngoài hệ thống hoặc cần hỗ trợ truy cập không; xác định việc học muốn tiếp nối.",
            "limitation": "Dữ liệu chưa chỉ ra chương kiến thức yếu hoặc nguyên nhân ngừng tương tác.",
        })
    if not suggestions:
        warnings.append("Chưa đủ căn cứ cho gợi ý cụ thể. Nếu xác suất cao, cần tìm thêm bằng chứng và trao đổi với người học.")
    return suggestions, warnings


def evaluate(raw, table, flags, artifact):
    cutoff_day = floor(COURSES[raw["code_module"]][raw["code_presentation"]] * 0.75)
    records = normalize_assessments(table, cutoff_day)
    summary = assessment_summary(records, cutoff_day)
    errors = validate_features(raw, cutoff_day)
    if errors:
        return {"errors": errors}
    values = dict(raw)
    values.update({
        "assessments_submitted_to_t": summary["submitted"],
        "late_submissions_to_t": summary["raw_late"],
        "active_day_ratio": raw["active_days_to_t"] / max(cutoff_day, 1),
        "submission_rate": summary["submitted"] / max(summary["due"], 1),
        "days_since_last_activity": cutoff_day + 1 if raw["last_activity_day"] is None else cutoff_day - raw["last_activity_day"],
    })
    probability = None
    warnings = []
    if all(flags.values()):
        row = pd.DataFrame([{feature: values[feature] for feature in FEATURES}], columns=FEATURES)
        classes = list(artifact["pipeline"].classes_)
        probability = float(artifact["pipeline"].predict_proba(row)[0, classes.index(1)])
        if not isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Model không trả về xác suất hợp lệ.")
    else:
        warnings.append("Chưa dự báo: cần xác nhận còn theo học, dữ liệu đúng cutoff, log hoạt động và danh sách bài đánh giá đầy đủ.")
    suggestions, rule_warnings = build_suggestions(raw, summary, flags, probability, artifact["threshold"])
    return {
        "errors": [], "probability": probability, "threshold": artifact["threshold"],
        "cutoff_day": cutoff_day, "summary": summary, "suggestions": suggestions,
        "warnings": warnings + rule_warnings, "features": {feature: values[feature] for feature in FEATURES},
    }


def make_assessment_table(rows):
    table = pd.DataFrame(rows, columns=TABLE_COLUMNS)
    table["Mã bài"] = table["Mã bài"].astype("string")
    for column in TABLE_COLUMNS[1:3]:
        table[column] = pd.to_numeric(table[column]).astype("float64")
    for column in TABLE_COLUMNS[3:]:
        table[column] = table[column].astype("bool")
    return table


def render_result(result):
    st.subheader("Kết quả")
    if result["errors"]:
        for message in result["errors"]:
            st.error(message)
        return
    probability = result["probability"]
    if probability is not None:
        left, right = st.columns(2)
        left.metric("Xác suất thuộc nhóm nguy cơ", f"{probability:.2%}")
        right.metric("Ngưỡng cảnh báo", f'{result["threshold"]:.0%}')
        if probability >= result["threshold"]:
            st.warning("Đạt ngưỡng cảnh báo — cần xem xét và xác nhận thêm.")
        else:
            st.info("Chưa đạt ngưỡng cảnh báo — không đồng nghĩa chắc chắn không gặp khó khăn.")
    for warning in result["warnings"]:
        st.warning(warning)
    summary = result["summary"]
    st.caption(f'Cutoff: ngày {result["cutoff_day"]}. Theo danh sách đã nhập: {summary["due"]} bài đến hạn, {summary["submitted"]} bài đã nộp.')
    if summary["early_future"]:
        st.caption(f'{summary["early_future"]} bài được nộp trước hạn tương lai. Bài nộp sớm không thay thế bài đến hạn còn thiếu.')
    st.subheader("Gợi ý chiến lược học tập")
    for position, suggestion in enumerate(result["suggestions"], start=1):
        st.markdown(f'**{position}. {suggestion["title"]}**')
        st.write("Ưu tiên:", suggestion["priority"])
        st.write("Căn cứ:", suggestion["evidence"])
        st.write("Nên làm:", suggestion["action"])
        st.caption(suggestion["limitation"])
    if not result["suggestions"]:
        st.write("Chưa có gợi ý cụ thể đủ căn cứ từ dữ liệu đã xác nhận.")
    st.caption("Kết quả là tín hiệu hỗ trợ, không phải quyết định học vụ. Gợi ý chưa được chứng minh làm tăng điểm; model được nghiên cứu trên OULAD.")


def main():
    st.set_page_config(page_title="Dự báo và gợi ý học tập", layout="centered")
    try:
        artifact = load_model()
    except (OSError, ValueError, ImportError, KeyError) as error:
        st.error(f"Không nạp được model: {error}")
        st.stop()
    st.subheader("Nhập thông tin")
    selected = st.selectbox("Hồ sơ", ["Nhập hồ sơ mới", *SAMPLES], key="profile")
    sample = SAMPLES.get(selected)
    defaults = sample["features"] if sample else {}
    if sample:
        st.caption("Hồ sơ minh họa từ tập train OULAD; mã sinh viên và kết quả cuối kỳ đã bỏ, mã bài đã thay. Có thể chỉnh dữ liệu để thử; đây không phải đánh giá model trên hồ sơ mới.")
    left, right = st.columns(2)
    modules = list(COURSES)
    module = left.selectbox("Học phần", modules, index=modules.index(defaults.get("code_module", "AAA")), key=f"module_{selected}")
    presentations = list(COURSES[module])
    initial_presentation = defaults.get("code_presentation")
    presentation = right.selectbox("Kỳ học", presentations, index=presentations.index(initial_presentation) if initial_presentation in presentations else 0, key=f"presentation_{selected}_{module}")
    cutoff_day = floor(COURSES[module][presentation] * 0.75)
    context = (selected, module, presentation)
    if st.session_state.get("context") != context:
        st.session_state.pop("result", None)
        st.session_state["context"] = context
    st.caption(f'Chỉ nhập thông tin đến ngày {cutoff_day} — cutoff 75% của học phần dài {COURSES[module][presentation]} ngày. Ngày 0 là ngày bắt đầu; ngày âm là trước khi bắt đầu.')
    prefix = "|".join(context)
    raw = {"code_module": module, "code_presentation": presentation}
    flags = {}
    with st.form("learning_input", clear_on_submit=False):
        st.markdown("**Thông tin người học**")
        left, right = st.columns(2)
        for column, feature, label, choices in (
            (left, "gender", "Giới tính", GENDER), (right, "age_band", "Nhóm tuổi", AGE),
            (left, "highest_education", "Trình độ học vấn theo nhóm của OULAD", EDUCATION),
        ):
            options = list(choices)
            value = defaults.get(feature)
            raw[feature] = column.selectbox(label, options, index=options.index(value) if value in options else None,
                                             format_func=choices.get, placeholder="Chọn giá trị", key=f"{prefix}_{feature}")
        raw["studied_credits"] = right.number_input("Số tín chỉ", min_value=0, max_value=1000, value=int(defaults.get("studied_credits", 0)), step=1, key=f"{prefix}_credits")
        registration = left.text_input("Ngày đăng ký (để trống nếu chưa biết)", value=str(defaults.get("date_registration", "")), key=f"{prefix}_registration")
        st.markdown("**Hoạt động học tập đến cutoff**")
        left, right = st.columns(2)
        for position, (feature, label) in enumerate([
            ("total_clicks_to_t", "Tổng lượt tương tác"),
            ("active_days_to_t", "Số ngày có hoạt động"),
            ("clicks_resource_to_t", "Lượt tương tác tài liệu (resource)"),
            ("clicks_url_to_t", "Lượt tương tác liên kết (url)"),
            ("clicks_recent_7", "Lượt tương tác 7 ngày gần cutoff"),
            ("clicks_recent_30", "Lượt tương tác 30 ngày gần cutoff"),
        ]):
            column = left if position % 2 == 0 else right
            raw[feature] = column.number_input(label, min_value=0, value=int(defaults.get(feature, 0)), step=1, key=f"{prefix}_{feature}")
        last_activity = left.text_input("Ngày hoạt động cuối (trống nếu chưa từng hoạt động)", value=str(defaults.get("last_activity_day", "")), key=f"{prefix}_last_activity")
        st.markdown("**Bài đánh giá**")
        st.caption("Mỗi bài một dòng. Ngày đã nộp để trống nếu chưa nộp; hạn nộp để trống nếu chưa biết. Thêm cả bài chưa đến hạn để nhận diện bài nộp sớm.")
        table = st.data_editor(
            make_assessment_table(sample["assessments"] if sample else []),
            num_rows="dynamic", hide_index=True, key=f"{prefix}_assessments", width="stretch",
            column_config={
                "Mã bài": st.column_config.TextColumn("Mã bài", required=True),
                "Hạn nộp (ngày)": st.column_config.NumberColumn("Hạn nộp (ngày)", min_value=-1000, max_value=2000, step=1, format="%d"),
                "Ngày đã nộp": st.column_config.NumberColumn("Ngày đã nộp", min_value=-1000, max_value=cutoff_day, step=1, format="%d"),
                "Bảo lưu": st.column_config.CheckboxColumn("Bảo lưu", default=False),
                "Được miễn": st.column_config.CheckboxColumn("Được miễn", default=False),
            },
        )
        flags["enrollment_active"] = st.checkbox("Người học còn theo học tại cutoff", value=bool(sample), key=f"{prefix}_enrollment")
        flags["feature_data_confirmed"] = st.checkbox("Thông tin nhập đúng hồ sơ và mốc cutoff đã chọn", value=bool(sample), key=f"{prefix}_confirmed")
        flags["activity_complete"] = st.checkbox("Log hoạt động đầy đủ đến cutoff", value=bool(sample), key=f"{prefix}_activity_complete")
        flags["assessments_complete"] = st.checkbox("Danh sách bài đánh giá đầy đủ, gồm cả bài chưa nộp", value=bool(sample), key=f"{prefix}_assessments_complete")
        submitted = st.form_submit_button("Dự báo và gợi ý", type="primary", width="stretch")
    if submitted:
        st.session_state.pop("result", None)
        try:
            raw["date_registration"] = parse_day(registration, "Ngày đăng ký", maximum=1000)
            raw["last_activity_day"] = parse_day(last_activity, "Ngày hoạt động cuối")
            with st.spinner("Đang kiểm tra dữ liệu và dự báo…"):
                st.session_state["result"] = evaluate(raw, table, flags, artifact)
        except ValueError as error:
            st.session_state["result"] = {"errors": [str(error)]}
        except Exception:
            st.session_state["result"] = {"errors": ["Không hoàn tất dự báo. Kiểm tra phiên bản thư viện nêu ở đầu app.py và dữ liệu nhập; không sử dụng kết quả cũ."]}
    if "result" in st.session_state:
        st.divider()
        render_result(st.session_state["result"])


if __name__ == "__main__":
    main()
