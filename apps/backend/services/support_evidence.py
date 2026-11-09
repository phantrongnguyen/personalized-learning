"""Review database snapshots without treating aggregate consistency as source completeness."""
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from math import floor
from uuid import uuid4

from fastapi import HTTPException
from schemas.prediction import BehaviorFeatures
from models.feature import StudentFeatureSnapshot
from services.audit_service import write_audit_log

REVIEW_VERSION = 'database-snapshot-review-1'
FEATURE_KEYS = tuple(BehaviorFeatures.model_fields)


def snapshot_digest(snapshot, presentation):
    values = {key: getattr(snapshot, key, None) for key in FEATURE_KEYS}
    values.update(snapshot_id=str(snapshot.id), enrollment_id=str(snapshot.enrollment_id),
        cutoff_stage=snapshot.cutoff_stage, presentation_id=str(presentation.id),
        start_date=str(presentation.start_date), length=presentation.module_presentation_length)
    return hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def inspection(snapshot, presentation):
    values = {key: getattr(snapshot, key, None) for key in FEATURE_KEYS}
    issues = []
    try:
        BehaviorFeatures(**values)
    except ValueError:
        issues.append('Chỉ số thiếu hoặc ngoài miền hợp lệ.')
    if values['late_submissions_to_t'] > values['assessments_submitted_to_t']:
        issues.append('Số bài trễ vượt số bài đã nộp.')
    total, recent7, recent30, age = (values[key] for key in
        ('total_clicks_to_t', 'clicks_recent_7', 'clicks_recent_30', 'days_since_last_activity'))
    if (not 0 <= recent7 <= recent30 <= total or (recent7 > 0 and age >= 7)
            or (recent30 > 0 and age >= 30) or (recent7 == 0 < recent30 and age < 7)
            or (recent30 == 0 < total and age < 30)):
        issues.append('Số click và cửa sổ 7/30 ngày mâu thuẫn.')
    cutoff_day = floor(presentation.module_presentation_length * .75) if presentation.module_presentation_length else None
    cutoff_date = presentation.start_date + timedelta(days=cutoff_day) if presentation.start_date and cutoff_day is not None else None
    if snapshot.cutoff_stage != 'CUTOFF_75' or cutoff_date is None:
        issues.append('Thiếu thời điểm quan sát hợp lệ tại cutoff 75%.')
    elif cutoff_date > datetime.now(timezone.utc).date() or snapshot.created_at.date() < cutoff_date or snapshot.created_at > datetime.now(timezone.utc):
        issues.append('Snapshot được ghi trước cutoff hoặc cutoff ở tương lai.')
    raw = snapshot.raw_features_json if isinstance(snapshot.raw_features_json, dict) else {}
    return {'snapshot_id': snapshot.id, 'snapshot_sha256': snapshot_digest(snapshot, presentation),
        'recorded_at': snapshot.created_at, 'cutoff_date': cutoff_date, 'snapshot_day': cutoff_day,
        'data_source': raw.get('data_source'), 'features': values, 'issues': issues,
        'existing_review': raw.get('support_evidence'),
        'limitations': ['Database chỉ có chỉ số tổng hợp; không tự xác nhận log hoặc lịch bài đầy đủ.',
            'Giảng viên phụ trách phải đối chiếu nguồn trước khi xác nhận từng phạm vi dữ liệu.']}


async def review_snapshot(db, snapshot, presentation, payload, actor_id):
    preview = inspection(snapshot, presentation)
    if payload.snapshot_sha256 != preview['snapshot_sha256']:
        raise HTTPException(409, 'Snapshot hoặc học phần đã thay đổi; tải lại trước khi xác nhận')
    if preview['issues']:
        raise HTTPException(422, detail=preview['issues'])
    if payload.review_scope == 'source_verified' and preview['data_source'] == 'synthetic_demo':
        raise HTTPException(422, 'Dữ liệu minh họa không thể được xác nhận là nguồn thực')
    now = datetime.now(timezone.utc)
    metadata = deepcopy(snapshot.raw_features_json) if isinstance(snapshot.raw_features_json, dict) else {}
    reviewed = StudentFeatureSnapshot(id=uuid4(), enrollment_id=snapshot.enrollment_id,
        cutoff_stage=snapshot.cutoff_stage, created_at=now,
        **preview['features'])
    if payload.review_scope == 'demonstration':
        metadata['data_source'] = 'synthetic_demo'
    metadata['support_evidence'] = {
        'review_version': REVIEW_VERSION, 'review_scope': payload.review_scope,
        'source': payload.source_reference, 'confirmed_by_user_id': str(actor_id),
        'confirmed_at': now.isoformat(), 'review_note': payload.review_note,
        'snapshot_day': preview['snapshot_day'], 'previous_snapshot_id': str(snapshot.id),
        'previous_snapshot_sha256': preview['snapshot_sha256'],
        'snapshot_sha256': snapshot_digest(reviewed, presentation),
        'activity_complete': payload.activity_complete,
        'assessments_complete': payload.assessments_complete,
    }
    reviewed.raw_features_json = metadata
    db.add(reviewed)
    await db.flush()
    await write_audit_log(db, user_id=actor_id, action='REVIEW_SUPPORT_EVIDENCE',
        target_type='student_feature_snapshot', target_id=reviewed.id,
        detail=json.dumps(metadata['support_evidence'], ensure_ascii=False))
    await db.commit()
    return {'snapshot_id': reviewed.id, 'previous_snapshot_id': snapshot.id,
        'review_scope': payload.review_scope,
        'message': 'Đã lưu snapshot mới và audit. Không tự chạy dự báo hoặc tạo kế hoạch/nhiệm vụ.'}
