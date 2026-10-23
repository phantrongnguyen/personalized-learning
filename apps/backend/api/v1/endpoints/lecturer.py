import json
import logging

from anyio import to_thread
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.permissions import RequireRoles
from models.user import User
from models.assignment import CourseLecturer
from models.intervention import InterventionPlan, InterventionTask
from models.audit import AuditLog
from models.ml import PredictionRun, MLModel
from ml.explanation import explain_prediction
from services.model_registry import model_registry, RUNTIME_KEY
from models.feature import StudentFeatureSnapshot
from models.academic import StudentEnrollment, CoursePresentation, Course
from models.profile import StudentProfile
from schemas.prediction import PredictionProvenance
from models.help_request import StudentHelpRequest
from services.help_request_service import resolve_help_recipient
from schemas.advisor_lecturer import (
    LecturerCourseOut,
    StudentRiskInCourseOut,
    CourseStudentOut,
    CourseTaskAssignIn,
    AssessmentUpdateIn,
    AlertAdvisorIn,
    TaskOut,
)
from services.support_suggestions import evaluate_suggestions, validated_assessment_details, is_historical_oulad, RULE_VERSION
from repositories.academic_repo import (
    get_lecturer_profile_by_user_id,
    get_lecturer_assigned_courses,
    get_course_risk_board,
    get_course_students,
    update_course_student_assessment,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Yêu cầu vai trò LECTURER (hoặc ADMIN)
require_lecturer = RequireRoles(["LECTURER"])


async def _ensure_course_ownership(
    db: AsyncSession, current_user: User, presentation_id: uuid.UUID
) -> None:
    """Data Ownership Check: đảm bảo GVBM được phân công phụ trách lớp học phần."""
    profile = await get_lecturer_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không tìm thấy hồ sơ giảng viên")

    check_res = await db.execute(
        select(CourseLecturer).where(
            CourseLecturer.lecturer_id == profile.id,
            CourseLecturer.presentation_id == presentation_id,
        )
    )
    if not check_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không được phân công phụ trách lớp học phần này",
        )


@router.get("/courses", response_model=List[LecturerCourseOut], summary="Danh sách lớp học phần giảng dạy")
async def get_my_courses(
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_lecturer_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_lecturer_assigned_courses(db, profile.id)


@router.get("/courses/{presentation_id}/risk-board", response_model=List[StudentRiskInCourseOut], summary="Bảng cảnh báo nguy cơ học phần")
async def get_course_risk(
    presentation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    return await get_course_risk_board(db, presentation_id, limit=limit, offset=offset)


@router.get("/courses/{presentation_id}/students/{student_id}/suggestions", summary="Gợi ý có căn cứ để giảng viên xem xét")
async def get_course_student_suggestions(
    presentation_id: uuid.UUID,
    student_id: uuid.UUID,
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    enrollment = (await db.execute(select(StudentEnrollment).where(
        StudentEnrollment.student_id == student_id,
        StudentEnrollment.presentation_id == presentation_id,
    ))).scalars().first()
    if enrollment is None:
        raise HTTPException(404, "Sinh viên không thuộc học phần đã chọn")
    presentation = await db.get(CoursePresentation, presentation_id)
    profile = await db.get(StudentProfile, student_id)
    snapshot = (await db.execute(select(StudentFeatureSnapshot).where(
        StudentFeatureSnapshot.enrollment_id == enrollment.id,
    ).order_by(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc()).limit(1))).scalars().first()
    prediction = None
    recorded_inputs = None
    prediction_explanation = None
    if snapshot is not None:
        row = (await db.execute(select(PredictionRun, MLModel)
            .join(MLModel, MLModel.id == PredictionRun.model_id)
            .where(PredictionRun.snapshot_id == snapshot.id)
            .order_by(PredictionRun.created_at.desc(), PredictionRun.id.desc())
            .limit(1))).first()
        if row:
            run, model = row
            if isinstance(run.inference_context, dict):
                try:
                    provenance = PredictionProvenance.model_validate(run.inference_context)
                    recorded_inputs = provenance.features.model_dump()
                    runtime = (getattr(model, "metadata_json", None) or {}).get(RUNTIME_KEY)
                    if (isinstance(runtime, dict) and provenance.model_id == model.id
                            and provenance.model_version == model.version
                            and provenance.model_sha256 == runtime.get("model_sha256")
                            and provenance.threshold == model.threshold
                            and provenance.cutoff_fraction == model.cutoff_fraction
                            and provenance.positive_label == 1):
                        try:
                            artifact = await model_registry._pinned(model)
                            prediction_explanation = await to_thread.run_sync(
                                explain_prediction, artifact, recorded_inputs, run.risk_probability)
                        except Exception:
                            logger.warning("Cannot verify explanation for prediction %s", run.id, exc_info=True)
                except ValidationError:
                    pass
            prediction = {
                "run_id": run.id, "snapshot_id": snapshot.id,
                "risk_probability": run.risk_probability,
                "prediction_label": run.prediction_label,
                "threshold": model.threshold, "model_version": model.version,
                "cutoff_fraction": model.cutoff_fraction,
                "predicted_at": run.created_at,
                "meaning": "Phân loại nguy cơ theo ngưỡng của model; không kết luận cá nhân bỏ học hoặc cần can thiệp.",
            }
    plan = (await db.execute(select(InterventionPlan.id)
        .join(PredictionRun, PredictionRun.id == InterventionPlan.prediction_run_id)
        .join(StudentFeatureSnapshot, StudentFeatureSnapshot.id == PredictionRun.snapshot_id)
        .where(InterventionPlan.student_id == student_id,
               InterventionPlan.status == "ACTIVE",
               StudentFeatureSnapshot.enrollment_id == enrollment.id)
        .order_by(InterventionPlan.created_at.desc(), InterventionPlan.id.desc())
        .limit(1))).scalar_one_or_none()
    state, suggestions, warnings, cutoff_date = evaluate_suggestions(snapshot, presentation)
    history_query = (
        select(InterventionTask, AuditLog)
        .join(InterventionPlan, InterventionPlan.id == InterventionTask.plan_id)
        .join(PredictionRun, PredictionRun.id == InterventionPlan.prediction_run_id)
        .join(StudentFeatureSnapshot, StudentFeatureSnapshot.id == PredictionRun.snapshot_id)
        .join(StudentEnrollment, StudentEnrollment.id == StudentFeatureSnapshot.enrollment_id)
        .join(AuditLog, AuditLog.target_id == InterventionTask.id)
        .where(StudentEnrollment.student_id == student_id,
               StudentEnrollment.presentation_id == presentation_id,
               AuditLog.action == "LECTURER_COURSE_TASK_ASSIGNED",
               AuditLog.target_type == "InterventionTask")
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    )
    history = []
    for task, event in (await db.execute(history_query)).all():
        try:
            provenance = json.loads(event.detail or "{}")
        except (ValueError, TypeError):
            provenance = {}
        history.append({
            "task_id": task.id, "rule_id": provenance.get("rule_id"),
            "snapshot_id": provenance.get("snapshot_id"),
            "observation": provenance.get("observation"),
            "title": task.title, "description": task.description,
            "target_metric": task.target_metric, "assigned_at": event.created_at,
            "is_completed": task.is_completed, "completed_at": task.completed_at,
        })
    if prediction is None:
        warnings.append("Chưa có PredictionRun cho snapshot mới nhất; không phân loại SAFE.")
    metadata = (snapshot.raw_features_json.get("support_evidence")
                if snapshot and isinstance(snapshot.raw_features_json, dict) else None)
    details = None
    if (state != "insufficient_data" and isinstance(metadata, dict)
            and type(metadata.get("snapshot_day")) is int
            and metadata.get("assessments_complete") is True and presentation):
        details = validated_assessment_details(snapshot, metadata, metadata["snapshot_day"])
    observed_features = None
    if snapshot is not None and profile is not None and presentation is not None:
        course = await db.get(Course, presentation.course_id)
        if course is not None:
            observed_features = {
                "code_module": course.code_module,
                "gender": profile.gender,
                "highest_education": profile.highest_education,
                "age_band": profile.age_band,
                "studied_credits": enrollment.studied_credits,
                "date_registration": enrollment.date_registration,
                **{field: getattr(snapshot, field) for field in (
                    "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
                    "active_days_to_t", "active_day_ratio", "days_since_last_activity",
                    "clicks_recent_7", "clicks_recent_30", "assessments_submitted_to_t",
                    "late_submissions_to_t", "submission_rate",
                )},
            }
    return {
        "status": state, "rule_version": RULE_VERSION, "enrollment_id": enrollment.id,
        "snapshot_id": snapshot.id if snapshot else None,
        "prediction": prediction, "prediction_explanation": prediction_explanation, "cutoff_date": cutoff_date,
        "source_kind": "historical_oulad" if state != "insufficient_data" and is_historical_oulad(metadata) else "course",
        "cutoff_day": metadata.get("snapshot_day") if isinstance(metadata, dict) and type(metadata.get("snapshot_day")) is int else None,
        "assessment_details": details or [],
        "student_details": {
            "previous_attempts": enrollment.num_of_prev_attempts,
            "model_inputs": recorded_inputs,
            "observed_features": observed_features,
        },
        "suggestions": suggestions, "history": history, "warnings": warnings,
        "assignment": {"can_assign": plan is not None, "plan_id": plan,
                       "message": "Có plan ACTIVE đúng học phần; giảng viên quyết định và bấm giao."
                       if plan else "Chưa có plan ACTIVE đúng học phần. Cố vấn hoặc admin cần lập plan dựa trên PredictionRun thật trước khi giảng viên giao task."},
    }


@router.get("/courses/{presentation_id}/students", response_model=List[CourseStudentOut], summary="Danh sách sinh viên lớp học phần")
async def get_course_student_list(
    presentation_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    return await get_course_students(db, presentation_id, limit=limit, offset=offset)


@router.put(
    "/courses/{presentation_id}/students/{student_id}/assessment",
    summary="Cập nhật điểm/tiến độ đánh giá của sinh viên trong lớp học phần",
)
async def update_student_assessment(
    presentation_id: uuid.UUID,
    student_id: uuid.UUID,
    payload: AssessmentUpdateIn,
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    updated = await update_course_student_assessment(
        db,
        presentation_id=presentation_id,
        student_id=student_id,
        assessments_submitted=payload.assessments_submitted,
        late_submissions=payload.late_submissions,
        submission_rate=payload.submission_rate,
        final_result=payload.final_result,
        updated_by_user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sinh viên trong lớp học phần này",
        )
    return {"message": "Cập nhật đánh giá sinh viên thành công", **updated}


@router.post("/courses/{presentation_id}/tasks", response_model=TaskOut, summary="Giao bài tập bổ trợ môn học cho sinh viên")
async def assign_course_task(
    presentation_id: uuid.UUID,
    payload: CourseTaskAssignIn,
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    # Select a plan linked to this student's enrollment in this presentation.
    if bool(payload.suggestion_rule_id) != bool(payload.suggestion_snapshot_id):
        raise HTTPException(422, "Gợi ý phải có cả quy tắc và bản dữ liệu tương ứng")
    chosen_suggestion = None
    if payload.suggestion_rule_id:
        latest = (await db.execute(select(StudentFeatureSnapshot, CoursePresentation)
            .join(StudentEnrollment, StudentEnrollment.id == StudentFeatureSnapshot.enrollment_id)
            .join(CoursePresentation, CoursePresentation.id == StudentEnrollment.presentation_id)
            .where(StudentEnrollment.student_id == payload.student_id,
                   StudentEnrollment.presentation_id == presentation_id)
            .order_by(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc())
            .limit(1))).first()
        if latest is None or latest[0].id != payload.suggestion_snapshot_id:
            raise HTTPException(409, "Dữ liệu học tập đã thay đổi; hãy tải lại gợi ý")
        state, suggestions, _, _ = evaluate_suggestions(latest[0], latest[1])
        chosen_suggestion = next((item for item in suggestions if item["rule_id"] == payload.suggestion_rule_id), None)
        if state != "available" or chosen_suggestion is None:
            raise HTTPException(409, "Gợi ý không còn hợp lệ; hãy tải lại hồ sơ")
    plan_query = (
        select(InterventionPlan)
        .join(PredictionRun, PredictionRun.id == InterventionPlan.prediction_run_id)
        .join(StudentFeatureSnapshot, StudentFeatureSnapshot.id == PredictionRun.snapshot_id)
        .join(StudentEnrollment, StudentEnrollment.id == StudentFeatureSnapshot.enrollment_id)
        .where(InterventionPlan.student_id == payload.student_id,
               InterventionPlan.status == "ACTIVE",
               StudentEnrollment.student_id == payload.student_id,
               StudentEnrollment.presentation_id == presentation_id)
        .order_by(InterventionPlan.created_at.desc(), InterventionPlan.id.desc())
        .limit(1)
    )
    plan_res = await db.execute(plan_query)
    plan = plan_res.scalars().first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sinh viên chưa có kế hoạch can thiệp đang hoạt động cho học phần này",
        )

    task = InterventionTask(
        plan_id=plan.id,
        category="HOC_THUAT",
        priority=payload.priority,
        title=payload.title,
        description=payload.description,
        target_metric=payload.target_metric,
    )
    db.add(task)
    await db.flush()
    db.add(AuditLog(
        user_id=current_user.id, action="LECTURER_COURSE_TASK_ASSIGNED",
        target_type="InterventionTask", target_id=task.id,
        detail=json.dumps({
            "snapshot_id": str(payload.suggestion_snapshot_id) if chosen_suggestion else None,
            "rule_id": chosen_suggestion["rule_id"] if chosen_suggestion else None,
            "rule_version": chosen_suggestion["rule_version"] if chosen_suggestion else None,
            "observation": chosen_suggestion["observation"] if chosen_suggestion else None,
            "evidence": chosen_suggestion["evidence"] if chosen_suggestion else None,
            "verified_basis": payload.verified_basis.strip() if payload.verified_basis else None,
        }, ensure_ascii=False),
    ))
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/students/{student_id}/alert-advisor", summary="Gửi cảnh báo học vụ tới Giáo viên chủ nhiệm")
async def alert_advisor(
    student_id: uuid.UUID,
    payload: AlertAdvisorIn,
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, payload.presentation_id)
    enrolled = await db.execute(select(StudentEnrollment).where(
        StudentEnrollment.student_id == student_id,
        StudentEnrollment.presentation_id == payload.presentation_id,
    ))
    if enrolled.scalars().first() is None:
        raise HTTPException(404, "Sinh viên không thuộc học phần đã chọn")
    advisor_user = await resolve_help_recipient(
        db, student_id, "ADVISOR", payload.presentation_id, None,
    )
    alert = StudentHelpRequest(
        student_id=student_id,
        target_role="ADVISOR",
        target_user_id=advisor_user,
        presentation_id=payload.presentation_id,
        subject=payload.subject,
        content=payload.content,
        status="PENDING",
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return {"message": "Đã gửi cảnh báo học vụ tới Giáo viên chủ nhiệm thành công", "alert_id": alert.id}
