from functools import lru_cache
from hashlib import sha256
import json
from math import floor, isfinite
from pathlib import Path

from fastapi import HTTPException
import joblib
import pandas as pd

from app.schemas.prediction import PredictionInput

BACKEND = Path(__file__).resolve().parents[2]
MODEL_DIR = BACKEND / "model_store"
MODEL_PATH = MODEL_DIR / "model_hco_vnls_lightgbm_cutoff75.joblib"
INFO_PATH = MODEL_DIR / "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"
CATALOG_PATH = BACKEND / "app" / "core" / "course_catalog.json"


@lru_cache(maxsize=1)
def catalog():
    courses = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [
        {**course, "cutoff_day": floor(course["module_presentation_length"] * .75)}
        for course in courses
    ]


@lru_cache(maxsize=1)
def _metadata():
    return json.loads(INFO_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _artifact():
    metadata = _metadata()
    if sha256(MODEL_PATH.read_bytes()).hexdigest() != metadata["model_sha256"]:
        raise RuntimeError("Model và metadata không khớp SHA-256.")
    artifact = joblib.load(MODEL_PATH)
    if artifact["feature_columns"] != metadata["feature_columns"] or artifact["cutoff_fraction"] != .75:
        raise RuntimeError("Schema/cutoff của model không khớp metadata.")
    return artifact


def model_info():
    metadata = _metadata()
    return {
        "name": metadata["model_name"],
        "cutoff_fraction": metadata["cutoff_fraction"],
        "feature_count": len(metadata["feature_columns"]),
        "feature_columns": metadata["feature_columns"],
        "threshold": metadata["threshold"],
        "validation_reference_train_only": metadata["validation_reference_train_only"],
        "notice": "Validation là số của thí nghiệm fit trên train, không phải điểm của artifact fit train + validation. Đây là demo nghiên cứu, chưa xác nhận trên kỳ học mới.",
    }


def validate_course(payload: PredictionInput):
    course = next(
        (course for course in catalog() if course["code_module"] == payload.code_module
         and course["code_presentation"] == payload.code_presentation), None,
    )
    if course is None:
        raise HTTPException(422, "Học phần và kỳ học không tồn tại trong bảng courses của OULAD.")
    cutoff_day = course["cutoff_day"]
    if payload.last_activity_day is not None and payload.last_activity_day > cutoff_day:
        raise HTTPException(422, "Ngày hoạt động cuối không thể sau cutoff.")
    if payload.date_registration is not None and payload.date_registration > cutoff_day:
        raise HTTPException(422, "Ngày đăng ký không thể sau cutoff của người đang theo học.")
    if payload.last_activity_day is not None:
        age = cutoff_day - payload.last_activity_day
        if (payload.clicks_recent_7 > 0 and age >= 7) or (payload.clicks_recent_30 > 0 and age >= 30):
            raise HTTPException(422, "Click gần đây không khớp ngày hoạt động cuối; kiểm tra lại cửa sổ thời gian.")
    return course


def predict(payload: PredictionInput):
    course = validate_course(payload)
    cutoff_day = course["cutoff_day"]

    values = payload.model_dump(exclude={"code_presentation", "assessments_due_to_t", "last_activity_day"})
    values["active_day_ratio"] = payload.active_days_to_t / max(cutoff_day, 1)
    values["submission_rate"] = payload.assessments_submitted_to_t / max(payload.assessments_due_to_t, 1)
    values["days_since_last_activity"] = (
        cutoff_day + 1 if payload.last_activity_day is None
        else max(cutoff_day - payload.last_activity_day, 0)
    )
    artifact = _artifact()
    features = artifact["feature_columns"]
    row = pd.DataFrame([{column: values[column] for column in features}], columns=features)
    score = float(artifact["pipeline"].predict_proba(row)[0, 1])
    if not isfinite(score):
        raise HTTPException(500, "Model không trả về xác suất hợp lệ.")
    return {
        "probability_risk": score,
        "above_threshold": score >= artifact["threshold"],
        "threshold": artifact["threshold"],
        "cutoff_fraction": .75,
        "cutoff_day": cutoff_day,
        "module_presentation_length": course["module_presentation_length"],
        "feature_count": len(features),
        "observations": {
            "active_days": payload.active_days_to_t,
            "submitted": payload.assessments_submitted_to_t,
            "due": payload.assessments_due_to_t,
            "recent_clicks": payload.clicks_recent_30,
        },
        "notice": "Tín hiệu hỗ trợ xem xét; không phải kết luận hay quyết định học vụ tự động.",
    }
