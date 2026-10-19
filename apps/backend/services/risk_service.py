"""Current risk always belongs to the newest snapshot of a specific enrollment."""
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

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


async def current_predictions(db, enrollment_ids):
    """Fetch current snapshots/results in one query, regardless of page size."""
    if not enrollment_ids:
        return {}
    snapshots = select(StudentFeatureSnapshot,
        func.row_number().over(partition_by=StudentFeatureSnapshot.enrollment_id,
            order_by=(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc())).label('position')
    ).where(StudentFeatureSnapshot.enrollment_id.in_(enrollment_ids)).subquery()
    snapshot = aliased(StudentFeatureSnapshot, snapshots)
    predictions = select(PredictionRun,
        func.row_number().over(partition_by=PredictionRun.snapshot_id,
            order_by=(PredictionRun.created_at.desc(), PredictionRun.id.desc())).label('position')
    ).join(snapshots, (snapshots.c.id == PredictionRun.snapshot_id) & (snapshots.c.position == 1)).subquery()
    prediction = aliased(PredictionRun, predictions)
    rows = (await db.execute(select(snapshot, prediction).outerjoin(predictions,
        (predictions.c.snapshot_id == snapshot.id) & (predictions.c.position == 1))
        .where(snapshots.c.position == 1))).all()
    return {snap.enrollment_id: (snap, pred) for snap, pred in rows}


def risk_fields(prediction):
    if prediction is None:
        return {"risk_probability": None, "risk_level": "NOT_PREDICTED"}
    return {
        "risk_probability": round(prediction.risk_probability, 4),
        "risk_level": "HIGH_RISK" if prediction.prediction_label == 1 else "SAFE",
    }


async def student_risk_summary(db, student_id):
    return (await student_risk_summaries(db, [student_id]))[student_id]


async def student_risk_summaries(db, student_ids):
    if not student_ids:
        return {}
    rows = (await db.execute(select(StudentEnrollment.student_id, StudentEnrollment.id)
        .where(StudentEnrollment.student_id.in_(student_ids)))).all()
    current = await current_predictions(db, [row.id for row in rows])
    grouped = {student_id: [] for student_id in student_ids}
    for student_id, enrollment_id in rows:
        grouped[student_id].append(current.get(enrollment_id, (None, None))[1])
    return {student_id: summarize_predictions(predictions) for student_id, predictions in grouped.items()}


def summarize_predictions(course_predictions):
    predictions = [prediction for prediction in course_predictions if prediction is not None]
    high = [p for p in predictions if p.prediction_label == 1]
    missing = len(course_predictions) - len(predictions)
    # Any high-risk course wins. SAFE requires complete coverage of all courses.
    candidates = high or (predictions if not missing else [])
    representative = max(candidates, key=lambda p: p.risk_probability) if candidates else None
    return {
        **risk_fields(representative),
        "total_courses": len(course_predictions),
        "predicted_courses": len(predictions),
        "high_risk_courses": len(high),
        "unpredicted_courses": missing,
        "risk_aggregation": "ANY_HIGH_ELSE_ALL_SAFE",
        "representative_prediction": representative,
    }
