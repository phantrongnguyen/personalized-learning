import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from core.database import get_db
from core.permissions import RequireRoles
from models.user import User
from models.academic import StudentEnrollment, CoursePresentation, Course
from models.feature import StudentFeatureSnapshot
from models.help_request import StudentHelpRequest
from schemas.student import (
    StudentProfileDetailOut,
    StudentCourseItemOut,
    RiskPredictionOut,
    RadarDataOut,
    StudentTaskItemOut,
    TaskCompleteIn,
    HelpRequestCreateIn,
    HelpRequestOut,
)
from schemas.advisor_lecturer import PlanOut
from repositories.student_repo import (
    get_student_profile_by_user_id,
    get_student_courses,
    get_enrollment_prediction,
    get_student_tasks_list,
    complete_student_task,
    get_student_intervention_plans,
)
from services.radar_service import calculate_radar_6d

router = APIRouter()

# Yêu cầu vai trò STUDENT (hoặc ADMIN)
require_student = RequireRoles(["STUDENT"])


@router.get("/profile", response_model=StudentProfileDetailOut, summary="Hồ sơ cá nhân sinh viên")
async def get_my_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ sinh viên")

    # Tính tổng số tín chỉ đã đăng ký
    courses = await get_student_courses(db, profile.id)
    credits_total = sum(c["studied_credits"] for c in courses)

    return {
        "id": profile.id,
        "student_code": profile.student_code,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "gender": profile.gender,
        "highest_education": profile.highest_education,
        "age_band": profile.age_band,
        "imd_band": profile.imd_band,
        "region": profile.region,
        "disability": profile.disability,
        "studied_credits_total": credits_total,
    }


@router.get("/courses", response_model=List[StudentCourseItemOut], summary="Danh sách môn học đang theo học")
async def get_my_courses(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_student_courses(db, profile.id)


@router.get("/courses/{enrollment_id}/risk-prediction", response_model=RiskPredictionOut, summary="Dự báo rủi ro học tập môn học tại Cutoff 75%")
async def get_my_course_risk(
    enrollment_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ sinh viên")

    pred = await get_enrollment_prediction(db, enrollment_id, profile.id)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có dữ liệu dự báo cho học phần này hoặc bạn không có quyền xem",
        )
    return pred


@router.get("/courses/{enrollment_id}/radar", response_model=RadarDataOut, summary="Biểu đồ Radar Năng lực 6D đối sánh Benchmark Top 25%")
async def get_my_course_radar(
    enrollment_id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ sinh viên")

    # Kiểm tra quyền sở hữu enrollment
    enr_query = select(StudentEnrollment).where(
        and_(StudentEnrollment.id == enrollment_id, StudentEnrollment.student_id == profile.id)
    )
    enr_res = await db.execute(enr_query)
    enr = enr_res.scalars().first()
    if not enr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy học phần này")

    pres_query = (
        select(CoursePresentation, Course)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(CoursePresentation.id == enr.presentation_id)
    )
    pres_res = await db.execute(pres_query)
    _, course = pres_res.first()

    # Lấy feature snapshot
    snap_query = (
        select(StudentFeatureSnapshot)
        .where(StudentFeatureSnapshot.enrollment_id == enr.id)
        .order_by(desc(StudentFeatureSnapshot.created_at))
        .limit(1)
    )
    snap_res = await db.execute(snap_query)
    snap = snap_res.scalars().first()

    snap_dict = {
        "total_clicks_to_t": snap.total_clicks_to_t if snap else 0,
        "active_days_to_t": snap.active_days_to_t if snap else 0,
        "active_day_ratio": snap.active_day_ratio if snap else 0.0,
        "clicks_recent_7": snap.clicks_recent_7 if snap else 0,
        "submission_rate": snap.submission_rate if snap else 0.0,
        "late_submissions_to_t": snap.late_submissions_to_t if snap else 0,
    }

    dimensions = calculate_radar_6d(snap_dict)
    return {
        "enrollment_id": enr.id,
        "code_module": course.code_module,
        "dimensions": dimensions,
    }


@router.get("/tasks", response_model=List[StudentTaskItemOut], summary="Danh sách nhiệm vụ can thiệp sư phạm cần làm")
async def get_my_tasks(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_student_tasks_list(db, profile.id)


@router.get("/intervention-plans", response_model=List[PlanOut], summary="Danh sách kế hoạch can thiệp sư phạm của bản thân")
async def get_my_intervention_plans(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_student_intervention_plans(db, profile.id, status_filter)


@router.patch("/tasks/{task_id}/complete", response_model=StudentTaskItemOut, summary="Đánh dấu hoàn thành nhiệm vụ can thiệp")
async def complete_task(
    task_id: uuid.UUID,
    payload: TaskCompleteIn,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ sinh viên")

    task = await complete_student_task(db, task_id, profile.id, payload.student_feedback)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhiệm vụ can thiệp của bạn")
    return task


@router.get("/help-requests", response_model=List[HelpRequestOut], summary="Danh sách các yêu cầu trợ giúp đã gửi")
async def get_my_help_requests(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        return []

    query = (
        select(StudentHelpRequest)
        .where(StudentHelpRequest.student_id == profile.id)
        .order_by(desc(StudentHelpRequest.created_at))
    )
    res = await db.execute(query)
    return list(res.scalars().all())


@router.post("/help-requests", response_model=HelpRequestOut, summary="Tạo yêu cầu trợ giúp gửi GVCN hoặc GVBM")
async def create_help_request(
    payload: HelpRequestCreateIn,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy hồ sơ sinh viên")

    req = StudentHelpRequest(
        student_id=profile.id,
        target_role=payload.target_role,
        presentation_id=payload.presentation_id,
        target_user_id=payload.target_user_id,
        subject=payload.subject,
        content=payload.content,
        status="PENDING",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req
