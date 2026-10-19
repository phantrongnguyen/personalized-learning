import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.permissions import RequireRoles
from models.user import User
from models.assignment import CourseLecturer, AdvisorStudent
from models.profile import AdvisorProfile
from models.intervention import InterventionPlan, InterventionTask
from models.ml import PredictionRun, MLModel
from models.feature import StudentFeatureSnapshot
from models.academic import StudentEnrollment, CoursePresentation
from models.help_request import StudentHelpRequest
from schemas.advisor_lecturer import (
    LecturerCourseOut,
    StudentRiskInCourseOut,
    CourseStudentOut,
    CourseTaskAssignIn,
    AssessmentUpdateIn,
    AlertAdvisorIn,
    TaskOut,
)
from services.support_suggestions import evaluate_suggestions, RULE_VERSION
from repositories.academic_repo import (
    get_lecturer_profile_by_user_id,
    get_lecturer_assigned_courses,
    get_course_risk_board,
    get_course_students,
    update_course_student_assessment,
)

router = APIRouter()

# Yêu cầu vai trò LECTURER (hoặc ADMIN)
require_lecturer = RequireRoles(["LECTURER"])


async def _ensure_course_ownership(
    db: AsyncSession, current_user: User, presentation_id: uuid.UUID
) -> None:
    """Data Ownership Check: đảm bảo GVBM được phân công phụ trách lớp học phần."""
    user_roles = [r.code for r in current_user.roles]
    if "ADMIN" in user_roles:
        return

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
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    return await get_course_risk_board(db, presentation_id)


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
    snapshot = (await db.execute(select(StudentFeatureSnapshot).where(
        StudentFeatureSnapshot.enrollment_id == enrollment.id,
    ).order_by(StudentFeatureSnapshot.created_at.desc(), StudentFeatureSnapshot.id.desc()).limit(1))).scalars().first()
    prediction = None
    if snapshot is not None:
        row = (await db.execute(select(PredictionRun, MLModel)
            .join(MLModel, MLModel.id == PredictionRun.model_id)
            .where(PredictionRun.snapshot_id == snapshot.id)
            .order_by(PredictionRun.created_at.desc(), PredictionRun.id.desc())
            .limit(1))).first()
        if row:
            run, model = row
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
    if prediction is None:
        warnings.append("Chưa có PredictionRun cho snapshot mới nhất; không phân loại SAFE.")
    return {
        "status": state, "rule_version": RULE_VERSION, "enrollment_id": enrollment.id,
        "prediction": prediction, "cutoff_date": cutoff_date,
        "suggestions": suggestions, "warnings": warnings,
        "assignment": {"can_assign": plan is not None, "plan_id": plan,
                       "message": "Có plan ACTIVE đúng học phần; giảng viên quyết định và bấm giao."
                       if plan else "Chưa có plan ACTIVE đúng học phần. Cố vấn hoặc admin cần lập plan dựa trên PredictionRun thật trước khi giảng viên giao task."},
    }


@router.get("/courses/{presentation_id}/students", response_model=List[CourseStudentOut], summary="Danh sách sinh viên lớp học phần")
async def get_course_student_list(
    presentation_id: uuid.UUID,
    current_user: User = Depends(require_lecturer),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_course_ownership(db, current_user, presentation_id)
    return await get_course_students(db, presentation_id)


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
    if payload.presentation_id is not None:
        await _ensure_course_ownership(db, current_user, payload.presentation_id)
        enrolled = await db.execute(select(StudentEnrollment).where(
            StudentEnrollment.student_id == student_id,
            StudentEnrollment.presentation_id == payload.presentation_id,
        ))
        if enrolled.scalars().first() is None:
            raise HTTPException(404, "Sinh viên không thuộc học phần đã chọn")
    advisor_user = (await db.execute(select(AdvisorProfile.user_id)
        .join(AdvisorStudent, AdvisorStudent.advisor_id == AdvisorProfile.id)
        .where(AdvisorStudent.student_id == student_id)
        .order_by(AdvisorStudent.assigned_at.desc()).limit(1))).scalar_one_or_none()
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
