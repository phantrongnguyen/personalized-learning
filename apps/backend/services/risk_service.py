"""Current risk always belongs to the newest snapshot of a specific enrollment."""
from sqlalchemy import select

from models.academic import StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun


async def latest_snapshot(db, enrollment_id):
    return (await db.execute(select(StudentFeatureSnapshot)
        .where(StudentFeatureSnapshot.enrollment_id == enrollment_id)
        .order_by(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc())
        .limit(1))).scalars().first()


async def current_prediction(db, enrollment_id):
    snapshot = await latest_snapshot(db, enrollment_id)
    if snapshot is None:
        return None, None
    prediction = (await db.execute(select(PredictionRun)
        .where(PredictionRun.snapshot_id == snapshot.id)
        .order_by(PredictionRun.created_at.desc(), PredictionRun.id.desc())
        .limit(1))).scalars().first()
    return snapshot, prediction


def risk_fields(prediction):
    if prediction is None:
        return {"risk_probability": None, "risk_level": "NOT_PREDICTED"}
    return {
        "risk_probability": round(prediction.risk_probability, 4),
        "risk_level": "HIGH_RISK" if prediction.prediction_label == 1 else "SAFE",
    }


async def student_risk_summary(db, student_id):
    enrollment_ids = (await db.execute(select(StudentEnrollment.id)
        .where(StudentEnrollment.student_id == student_id))).scalars().all()
    predictions = []
    for enrollment_id in enrollment_ids:
        _, prediction = await current_prediction(db, enrollment_id)
        if prediction is not None:
            predictions.append(prediction)
    high = [p for p in predictions if p.prediction_label == 1]
    missing = len(enrollment_ids) - len(predictions)
    # Any high-risk course wins. SAFE requires complete coverage of all courses.
    candidates = high or (predictions if not missing else [])
    representative = max(candidates, key=lambda p: p.risk_probability) if candidates else None
    return {
        **risk_fields(representative),
        "total_courses": len(enrollment_ids),
        "predicted_courses": len(predictions),
        "high_risk_courses": len(high),
        "unpredicted_courses": missing,
        "risk_aggregation": "ANY_HIGH_ELSE_ALL_SAFE",
        "representative_prediction": representative,
    }
