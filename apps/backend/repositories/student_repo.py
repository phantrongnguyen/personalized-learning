import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from models.profile import StudentProfile
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun, MLModel
from models.intervention import InterventionPlan, InterventionTask
from models.help_request import StudentHelpRequest


async def get_student_profile_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[StudentProfile]:
    query = select(StudentProfile).where(StudentProfile.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_student_courses(db: AsyncSession, student_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Lấy danh sách các môn học sinh viên ghi danh"""
    query = (
        select(StudentEnrollment, CoursePresentation, Course)
        .join(CoursePresentation, StudentEnrollment.presentation_id == CoursePresentation.id)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(StudentEnrollment.student_id == student_id)
    )
    result = await db.execute(query)
    rows = result.all()

    courses = []
    for enr, pres, course in rows:
        courses.append({
            "enrollment_id": enr.id,
            "code_module": course.code_module,
            "course_name": course.name,
            "code_presentation": pres.code_presentation,
            "studied_credits": enr.studied_credits,
            "final_result": enr.final_result,
        })
    return courses


async def get_enrollment_prediction(
    db: AsyncSession, enrollment_id: uuid.UUID, student_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """Lấy kết quả dự báo AI cho enrollment của sinh viên (kiểm tra quyền sở hữu)"""
    # Ràng buộc sở hữu
    enr_query = select(StudentEnrollment).where(
        and_(StudentEnrollment.id == enrollment_id, StudentEnrollment.student_id == student_id)
    )
    enr_res = await db.execute(enr_query)
    enr = enr_res.scalars().first()
    if not enr:
        return None

    # Lấy thông tin môn
    pres_query = (
        select(CoursePresentation, Course)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(CoursePresentation.id == enr.presentation_id)
    )
    pres_res = await db.execute(pres_query)
    _, course = pres_res.first()

    # Lấy snapshot và prediction gần nhất
    snap_query = (
        select(StudentFeatureSnapshot)
        .where(StudentFeatureSnapshot.enrollment_id == enr.id)
        .order_by(desc(StudentFeatureSnapshot.created_at))
        .limit(1)
    )
    snap_res = await db.execute(snap_query)
    snap = snap_res.scalars().first()

    if not snap:
        return None

    pred_query = (
        select(PredictionRun, MLModel)
        .join(MLModel, PredictionRun.model_id == MLModel.id)
        .where(PredictionRun.snapshot_id == snap.id)
        .order_by(desc(PredictionRun.created_at))
        .limit(1)
    )
    pred_res = await db.execute(pred_query)
    pred_row = pred_res.first()

    if not pred_row:
        return None

    pred, model = pred_row

    # Sinh khuyến nghị sư phạm dựa trên rủi ro
    recs = []
    if pred.risk_probability >= 0.5:
        recs.append("Cảnh báo nguy cơ không đạt học phần tại mốc 75% thời lượng môn học.")
        if snap.active_days_to_t < 20:
            recs.append("Tăng cường độ chuyên cần: Đăng nhập hệ thống học tập tối thiểu 3 ngày/tuần.")
        if snap.late_submissions_to_t > 0:
            recs.append("Cải thiện tính đúng hạn: Khẩn trương nộp bù các bài tập TMA còn thiếu.")
        if snap.clicks_recent_7 < 15:
            recs.append("Ôn tập kiến thức trọng tâm bài giảng qua tài liệu PDF và slide hướng dẫn.")
    else:
        recs.append("Phong độ học tập ổn định, hãy duy trì lịch nộp bài tập đúng hạn để chuẩn bị thi cuối kỳ.")

    return {
        "enrollment_id": enr.id,
        "code_module": course.code_module,
        "cutoff_stage": snap.cutoff_stage,
        "risk_probability": round(pred.risk_probability, 4),
        "risk_level": "HIGH_RISK" if pred.risk_probability >= 0.5 else "SAFE",
        "model_version": model.version,
        "predicted_at": pred.created_at,
        "pedagogical_recommendations": recs,
    }


async def get_student_intervention_plans(
    db: AsyncSession, student_id: uuid.UUID, status_filter: Optional[str] = None
) -> List[InterventionPlan]:
    """Danh sách kế hoạch can thiệp sư phạm của sinh viên kèm nhiệm vụ."""
    query = (
        select(InterventionPlan)
        .where(InterventionPlan.student_id == student_id)
        .options(selectinload(InterventionPlan.tasks))
        .order_by(desc(InterventionPlan.created_at))
    )
    if status_filter:
        query = query.where(InterventionPlan.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_student_tasks_list(db: AsyncSession, student_id: uuid.UUID) -> List[InterventionTask]:
    """Lấy danh sách nhiệm vụ can thiệp của sinh viên"""
    query = (
        select(InterventionTask)
        .join(InterventionPlan, InterventionTask.plan_id == InterventionPlan.id)
        .where(and_(InterventionPlan.student_id == student_id, InterventionPlan.status == "ACTIVE"))
        .order_by(InterventionTask.is_completed.asc(), InterventionTask.id.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def complete_student_task(
    db: AsyncSession, task_id: uuid.UUID, student_id: uuid.UUID, feedback: Optional[str]
) -> Optional[InterventionTask]:
    """Sinh viên đánh dấu hoàn thành task của mình"""
    query = (
        select(InterventionTask)
        .join(InterventionPlan, InterventionTask.plan_id == InterventionPlan.id)
        .where(and_(InterventionTask.id == task_id, InterventionPlan.student_id == student_id))
    )
    result = await db.execute(query)
    task = result.scalars().first()
    if not task:
        return None

    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)
    if feedback:
        task.student_feedback = feedback

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
