import math
import time
from copy import deepcopy
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select, func
from ml.model_loader import load_model
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.profile import StudentProfile
from models.ml import MLModel, PredictionRun
from schemas.prediction import StudentFeatures, PredictionProvenance


from ml.predictor import predict
from schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)


class PredictionService:

    @staticmethod
    def execute(model, data: PredictionRequest) -> PredictionResponse:
        features = data.features.model_dump()
        result = predict(
            model=model,
            features=features,
        )

        provenance = PredictionProvenance(features=features, **model["_provenance"])
        return PredictionResponse(**result, provenance=provenance)

BEHAVIOR_FIELDS = (
    "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
    "active_days_to_t", "active_day_ratio", "days_since_last_activity",
    "clicks_recent_7", "clicks_recent_30", "assessments_submitted_to_t",
    "late_submissions_to_t", "submission_rate",
)


def database_features(snapshot, enrollment, profile, course):
    values = {name: getattr(snapshot, name) for name in BEHAVIOR_FIELDS}
    for name, value in values.items():
        if value is None or not math.isfinite(value) or value < 0:
            raise ValueError(f"Chỉ số {name} phải hữu hạn và không âm")
    for name in ("submission_rate", "active_day_ratio"):
        if values[name] > 1:
            raise ValueError(f"Chỉ số {name} phải trong [0, 1]")
    if enrollment.studied_credits <= 0:
        raise ValueError("Số tín chỉ phải lớn hơn 0")
    values.update(
        code_module=course.code_module, gender=profile.gender,
        highest_education=profile.highest_education, age_band=profile.age_band,
        studied_credits=enrollment.studied_credits,
        date_registration=enrollment.date_registration,
    )
    return StudentFeatures(**values).model_dump()


def artifact_path(model_record):
    candidate = Path(model_record.model_file_path)
    if candidate.is_absolute():
        return candidate
    backend = Path(__file__).resolve().parents[1]
    for base in (backend, backend.parents[1]):
        resolved = base / candidate
        if resolved.is_file():
            return resolved
    raise FileNotFoundError("Không tìm thấy artifact của mô hình active")


def infer_record(artifact, features, snapshot_id, model_id, user_id, model_version=None):
    features = StudentFeatures(**features).model_dump()
    started = time.perf_counter()
    result = predict(artifact, features)
    probability = float(result["confidence"])
    label = int(result["prediction"])
    if not math.isfinite(probability) or not 0 <= probability <= 1 or label not in (0, 1):
        raise ValueError("Kết quả mô hình không hợp lệ")
    identity = dict(artifact["_provenance"])
    if model_version is not None:
        identity["model_version"] = model_version
    context = PredictionProvenance(features=features, **identity).model_dump()
    return PredictionRun(
        snapshot_id=snapshot_id, model_id=model_id,
        prediction_label=label, risk_probability=probability,
        execution_time_ms=round((time.perf_counter() - started) * 1000),
        triggered_by_user_id=user_id,
        inference_context=deepcopy(context),
    )


async def generate_database_predictions(db, user_id, enrollment_id=None):
    model_rows = (await db.execute(select(MLModel).where(MLModel.is_active == True))).scalars().all()
    if len(model_rows) != 1:
        raise HTTPException(400, "Cần đúng một mô hình ML đang active")
    record = model_rows[0]
    artifact = load_model(artifact_path(record))
    if not math.isclose(float(artifact["threshold"]), record.threshold):
        raise HTTPException(400, "Ngưỡng mô hình trong database khác artifact")
    if not math.isclose(record.cutoff_fraction, 0.75):
        raise HTTPException(400, "Luồng hiện chỉ hỗ trợ mô hình Cutoff 75%")
    ranked = select(
        StudentFeatureSnapshot.id.label("id"),
        func.row_number().over(
            partition_by=StudentFeatureSnapshot.enrollment_id,
            order_by=(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc()),
        ).label("position"),
    ).subquery()
    query = (
        select(StudentFeatureSnapshot, StudentEnrollment, StudentProfile, Course)
        .join(ranked, ranked.c.id == StudentFeatureSnapshot.id)
        .join(StudentEnrollment, StudentEnrollment.id == StudentFeatureSnapshot.enrollment_id)
        .join(StudentProfile, StudentProfile.id == StudentEnrollment.student_id)
        .join(CoursePresentation, CoursePresentation.id == StudentEnrollment.presentation_id)
        .join(Course, Course.id == CoursePresentation.course_id)
        .where(ranked.c.position == 1)
    )
    if enrollment_id is not None:
        query = query.where(StudentEnrollment.id == enrollment_id)
    rows = (await db.execute(query)).all()
    if enrollment_id is not None and not rows:
        raise HTTPException(404, "Đăng ký học phần chưa có snapshot")
    runs = []
    for snapshot, enrollment, profile, course in rows:
        if snapshot.cutoff_stage != "CUTOFF_75":
            raise HTTPException(422, f"Snapshot {snapshot.id} không ở mốc CUTOFF_75")
        features = database_features(snapshot, enrollment, profile, course)
        runs.append(infer_record(artifact, features, snapshot.id, record.id, user_id, record.version))
    # Add only after every inference succeeds; caller commits data and audit together.
    db.add_all(runs)
    return record, runs
