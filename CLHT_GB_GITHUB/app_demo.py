from pathlib import Path
import joblib
import pandas as pd
import streamlit as st

MODEL_PATH = Path(__file__).parent / "mo_hinh" / "model_hco_vnls_hgb_demo.joblib"

@st.cache_resource
def tai_model():
    return joblib.load(MODEL_PATH)

st.set_page_config(page_title="Dự đoán nguy cơ sinh viên", layout="centered")
st.title("Dự đoán nguy cơ sinh viên")
st.caption("Bản demo dùng HCO–VNLS để chọn feature và HistGradientBoosting để dự đoán.")

artifact = tai_model()

with st.form("du_doan"):
    code_module = st.text_input("Mã học phần", "AAA")
    region = st.text_input("Khu vực", "East Anglian Region")
    imd_band = st.text_input("Nhóm IMD", "50-60%")
    age_band = st.text_input("Nhóm tuổi", "35-55")
    studied_credits = st.number_input("Số tín chỉ đăng ký", min_value=0.0, value=60.0)
    cutoff_day = st.number_input("Ngày cutoff", min_value=0.0, value=120.0)
    clicks_forumng_to_t = st.number_input("Click diễn đàn đến cutoff", min_value=0.0, value=10.0)
    clicks_oucontent_to_t = st.number_input("Click nội dung học tập đến cutoff", min_value=0.0, value=100.0)
    clicks_quiz_to_t = st.number_input("Click quiz đến cutoff", min_value=0.0, value=10.0)
    clicks_url_to_t = st.number_input("Click liên kết đến cutoff", min_value=0.0, value=5.0)
    active_days_to_t = st.number_input("Số ngày hoạt động đến cutoff", min_value=0.0, value=20.0)
    last_activity_day = st.number_input("Ngày hoạt động gần nhất", value=100.0)
    late_submissions_to_t = st.number_input("Số bài nộp trễ", min_value=0.0, value=0.0)
    missing_submissions_to_t = st.number_input("Số bài chưa nộp", min_value=0.0, value=1.0)
    submitted = st.form_submit_button("Dự đoán")

if submitted:
    row = pd.DataFrame([{
        "code_module": code_module,
        "region": region,
        "imd_band": imd_band,
        "age_band": age_band,
        "studied_credits": studied_credits,
        "cutoff_day": cutoff_day,
        "clicks_forumng_to_t": clicks_forumng_to_t,
        "clicks_oucontent_to_t": clicks_oucontent_to_t,
        "clicks_quiz_to_t": clicks_quiz_to_t,
        "clicks_url_to_t": clicks_url_to_t,
        "active_days_to_t": active_days_to_t,
        "last_activity_day": last_activity_day,
        "late_submissions_to_t": late_submissions_to_t,
        "missing_submissions_to_t": missing_submissions_to_t,
    }])
    probability = float(artifact["pipeline"].predict_proba(row)[0, 1])
    threshold = float(artifact["threshold"])
    st.metric("Xác suất nguy cơ", f"{probability:.1%}")
    if probability >= threshold:
        st.error("Cần xem xét hỗ trợ sớm.")
    else:
        st.success("Chưa vượt ngưỡng cảnh báo.")
    st.caption("Kết quả chỉ phục vụ demo nghiên cứu, không dùng để đưa ra quyết định học vụ tự động.")