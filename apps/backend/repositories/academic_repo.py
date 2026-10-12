import uuid
from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.assignment import AdvisorStudent, CourseLecturer
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun, MLModel
from models.intervention import InterventionPlan, InterventionTask, AdvisingNote
from models.help_request import StudentHelpRequest
from services.radar_service import calculate_radar_6d


# -------------------------------------------------------------
# ADVISOR REPOSITORY
# -------------------------------------------------------------
async def get_advisor_profile_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[AdvisorProfile]:
    query = select(AdvisorProfile).where(AdvisorProfile.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_advisor_classes(db: AsyncSession, advisor_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Thống kê danh sách lớp sinh hoạt do GVCN phụ trách"""
    query = (
        select(
            AdvisorStudent.class_name,
            AdvisorStudent.academic_year,
            func.count(AdvisorStudent.student_id).label("total_students")
        )
        .where(AdvisorStudent.advisor_id == advisor_id)
        .group_by(AdvisorStudent.class_name, AdvisorStudent.academic_year)
    )
    result = await db.execute(query)
    rows = result.all()

    classes_summary = []
    for row in rows:
        classes_summary.append({
            "class_name": row.class_name,
            "academic_year": row.academic_year,
            "total_students": row.total_students,
            "high_risk_count": 0,
            "safe_count": row.total_students,
        })
    return classes_summary


async def get_advisor_students(
    db: AsyncSession, advisor_id: uuid.UUID, class_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lấy danh sách sinh viên do GVCN quản lý kèm điểm rủi ro AI gần nhất"""
    query = (
        select(StudentProfile, User, AdvisorStudent.class_name)
        .join(AdvisorStudent, AdvisorStudent.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(AdvisorStudent.advisor_id == advisor_id)
    )
    if class_name:
        query = query.where(AdvisorStudent.class_name == class_name)

    result = await db.execute(query)
    records = result.all()

    students_data = []
    for sp, u, c_name in records:
        # Lấy dự báo gần nhất nếu có
        pred_query = (
            select(PredictionRun)
            .join(StudentFeatureSnapshot, PredictionRun.snapshot_id == StudentFeatureSnapshot.id)
            .join(StudentEnrollment, StudentFeatureSnapshot.enrollment_id == StudentEnrollment.id)
            .where(StudentEnrollment.student_id == sp.id)
            .order_by(desc(PredictionRun.created_at))
            .limit(1)
        )
        pred_res = await db.execute(pred_query)
        pred = pred_res.scalars().first()

        risk_prob = pred.risk_probability if pred else 0.0
        risk_lvl = "HIGH_RISK" if risk_prob >= 0.5 else "SAFE"

        # Kiểm tra kế hoạch can thiệp đang active
        plan_query = (
            select(InterventionPlan)
            .where(and_(InterventionPlan.student_id == sp.id, InterventionPlan.status == "ACTIVE"))
            .options(selectinload(InterventionPlan.tasks))
        )
        plan_res = await db.execute(plan_query)
        active_plan = plan_res.scalars().first()

        uncompleted = 0
        if active_plan and active_plan.tasks:
            uncompleted = sum(1 for t in active_plan.tasks if not t.is_completed)

        students_data.append({
            "student_id": sp.id,
            "student_code": sp.student_code,
            "full_name": u.full_name,
            "gender": sp.gender,
            "class_name": c_name,
            "risk_probability": round(risk_prob, 4),
            "risk_level": risk_lvl,
            "has_active_plan": active_plan is not None,
            "uncompleted_tasks_count": uncompleted,
        })

    return students_data


async def create_intervention_plan_with_tasks(
    db: AsyncSession,
    student_id: uuid.UUID,
    prediction_run_id: uuid.UUID,
    target_completion_date: Optional[date] = None,
    advisor_note_summary: Optional[str] = None,
    tasks_data: Optional[List[Dict[str, Any]]] = None,
) -> InterventionPlan:
    """Tạo mới kế hoạch can thiệp kèm các nhiệm vụ sư phạm"""
    plan = InterventionPlan(
        student_id=student_id,
        prediction_run_id=prediction_run_id,
        status="ACTIVE",
        target_completion_date=target_completion_date,
        advisor_note_summary=advisor_note_summary,
    )
    db.add(plan)
    await db.flush()  # Sinh plan.id

    if tasks_data:
        for t in tasks_data:
            task = InterventionTask(
                plan_id=plan.id,
                category=t.get("category", "HOC_THUAT"),
                priority=t.get("priority", "MEDIUM"),
                title=t["title"],
                description=t["description"],
                target_metric=t.get("target_metric", "Hoàn thành nhiệm vụ"),
            )
            db.add(task)

    await db.commit()
    await db.refresh(plan)
    return plan


# -------------------------------------------------------------
# LECTURER REPOSITORY
# -------------------------------------------------------------
async def get_lecturer_profile_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[LecturerProfile]:
    query = select(LecturerProfile).where(LecturerProfile.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_lecturer_assigned_courses(db: AsyncSession, lecturer_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Lấy danh sách các lớp học phần do GVBM phụ trách"""
    query = (
        select(CoursePresentation, Course, CourseLecturer.role_in_course)
        .join(CourseLecturer, CourseLecturer.presentation_id == CoursePresentation.id)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(CourseLecturer.lecturer_id == lecturer_id)
    )
    result = await db.execute(query)
    rows = result.all()

    courses = []
    for cp, c, role in rows:
        # Đếm sĩ số
        count_query = (
            select(func.count(StudentEnrollment.id))
            .where(StudentEnrollment.presentation_id == cp.id)
        )
        count_res = await db.execute(count_query)
        total_students = count_res.scalar_one()

        courses.append({
            "presentation_id": cp.id,
            "code_module": c.code_module,
            "course_name": c.name,
            "code_presentation": cp.code_presentation,
            "module_length": cp.module_presentation_length,
            "role_in_course": role,
            "total_students": total_students,
        })
    return courses


async def get_course_risk_board(
    db: AsyncSession, presentation_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """Lấy danh sách sinh viên kèm tương tác và nguy cơ trong lớp học phần"""
    query = (
        select(StudentEnrollment, StudentProfile, User)
        .join(StudentProfile, StudentEnrollment.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(StudentEnrollment.presentation_id == presentation_id)
    )
    result = await db.execute(query)
    enrollments = result.all()

    risk_board = []
    for se, sp, u in enrollments:
        # Lấy snapshot đặc trưng
        snap_query = (
            select(StudentFeatureSnapshot)
            .where(StudentFeatureSnapshot.enrollment_id == se.id)
            .order_by(desc(StudentFeatureSnapshot.created_at))
            .limit(1)
        )
        snap_res = await db.execute(snap_query)
        snap = snap_res.scalars().first()

        total_clicks = snap.total_clicks_to_t if snap else 0
        late_sub = snap.late_submissions_to_t if snap else 0
        sub_rate = snap.submission_rate if snap else 0.0

        # Lấy điểm rủi ro
        risk_prob = 0.0
        if snap:
            pred_query = (
                select(PredictionRun)
                .where(PredictionRun.snapshot_id == snap.id)
                .order_by(desc(PredictionRun.created_at))
                .limit(1)
            )
            pred_res = await db.execute(pred_query)
            pred = pred_res.scalars().first()
            if pred:
                risk_prob = pred.risk_probability

        risk_board.append({
            "student_id": sp.id,
            "student_code": sp.student_code,
            "full_name": u.full_name,
            "enrollment_id": se.id,
            "total_clicks": total_clicks,
            "late_submissions": late_sub,
            "submission_rate": round(sub_rate, 2),
            "risk_probability": round(risk_prob, 4),
            "risk_status": "HIGH_RISK" if risk_prob >= 0.5 else "SAFE",
        })

    return risk_board


async def get_course_students(
    db: AsyncSession, presentation_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """Danh sách sinh viên trong lớp học phần (kèm kết quả & mức độ tương tác)"""
    query = (
        select(StudentEnrollment, StudentProfile, User)
        .join(StudentProfile, StudentEnrollment.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(StudentEnrollment.presentation_id == presentation_id)
    )
    result = await db.execute(query)
    enrollments = result.all()

    students = []
    for se, sp, u in enrollments:
        snap_query = (
            select(StudentFeatureSnapshot)
            .where(StudentFeatureSnapshot.enrollment_id == se.id)
            .order_by(desc(StudentFeatureSnapshot.created_at))
            .limit(1)
        )
        snap_res = await db.execute(snap_query)
        snap = snap_res.scalars().first()

        risk_prob = 0.0
        if snap:
            pred_query = (
                select(PredictionRun)
                .where(PredictionRun.snapshot_id == snap.id)
                .order_by(desc(PredictionRun.created_at))
                .limit(1)
            )
            pred_res = await db.execute(pred_query)
            pred = pred_res.scalars().first()
            if pred:
                risk_prob = pred.risk_probability

        students.append({
            "student_id": sp.id,
            "student_code": sp.student_code,
            "full_name": u.full_name,
            "enrollment_id": se.id,
            "gender": sp.gender,
            "final_result": se.final_result,
            "total_clicks": snap.total_clicks_to_t if snap else 0,
            "late_submissions": snap.late_submissions_to_t if snap else 0,
            "submission_rate": round(snap.submission_rate, 2) if snap else 0.0,
            "risk_probability": round(risk_prob, 4),
            "risk_status": "HIGH_RISK" if risk_prob >= 0.5 else "SAFE",
        })

    return students


async def update_course_student_assessment(
    db: AsyncSession,
    presentation_id: uuid.UUID,
    student_id: uuid.UUID,
    assessments_submitted: Optional[int] = None,
    late_submissions: Optional[int] = None,
    submission_rate: Optional[float] = None,
    final_result: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """GVBM cập nhật điểm/tiến độ đánh giá của sinh viên trong lớp học phần.

    Các chỉ số đánh giá được ghi vào bản ghi feature snapshot mới nhất của enrollment,
    kết quả cuối kỳ ghi vào enrollment.final_result.
    """
    enr_query = (
        select(StudentEnrollment, StudentProfile)
        .join(StudentProfile, StudentEnrollment.student_id == StudentProfile.id)
        .where(
            and_(
                StudentEnrollment.presentation_id == presentation_id,
                StudentEnrollment.student_id == student_id,
            )
        )
    )
    enr_res = await db.execute(enr_query)
    row = enr_res.first()
    if not row:
        return None

    enr, sp = row

    snap_query = (
        select(StudentFeatureSnapshot)
        .where(StudentFeatureSnapshot.enrollment_id == enr.id)
        .order_by(desc(StudentFeatureSnapshot.created_at))
        .limit(1)
    )
    snap_res = await db.execute(snap_query)
    snap = snap_res.scalars().first()

    if assessments_submitted is not None and snap:
        snap.assessments_submitted_to_t = assessments_submitted
    if late_submissions is not None and snap:
        snap.late_submissions_to_t = late_submissions
    if submission_rate is not None and snap:
        snap.submission_rate = submission_rate
    if final_result is not None:
        enr.final_result = final_result

    db.add(enr)
    if snap:
        db.add(snap)
    await db.commit()

    return {
        "enrollment_id": enr.id,
        "student_id": sp.id,
        "final_result": enr.final_result,
        "assessments_submitted_to_t": snap.assessments_submitted_to_t if snap else None,
        "late_submissions_to_t": snap.late_submissions_to_t if snap else None,
        "submission_rate": snap.submission_rate if snap else None,
    }


# -------------------------------------------------------------
# ADVISOR DEEP-DIVE REPOSITORY (THỐNG KÊ / 360 / RADAR / KẾ HOẠCH / NOTES)
# -------------------------------------------------------------
async def advisor_owns_student(
    db: AsyncSession, advisor_id: uuid.UUID, student_id: uuid.UUID
) -> bool:
    """Kiểm tra sinh viên có thuộc lớp chủ nhiệm của GVCN hay không (Data Ownership)."""
    query = select(AdvisorStudent.id).where(
        and_(
            AdvisorStudent.advisor_id == advisor_id,
            AdvisorStudent.student_id == student_id,
        )
    )
    res = await db.execute(query)
    return res.scalars().first() is not None


async def get_class_statistics(
    db: AsyncSession, advisor_id: uuid.UUID, class_name: str
) -> Optional[Dict[str, Any]]:
    """Thống kê tổng hợp tình hình rủi ro của một lớp sinh hoạt."""
    students = await get_advisor_students(db, advisor_id, class_name)
    if not students:
        return None

    total = len(students)
    high_risk = sum(1 for s in students if s["risk_level"] == "HIGH_RISK")
    with_plan = sum(1 for s in students if s["has_active_plan"])
    outstanding = sum(s["uncompleted_tasks_count"] for s in students)
    avg_risk = round(sum(s["risk_probability"] for s in students) / total, 4) if total else 0.0

    year_query = select(AdvisorStudent.academic_year).where(
        and_(
            AdvisorStudent.advisor_id == advisor_id,
            AdvisorStudent.class_name == class_name,
        )
    )
    year_res = await db.execute(year_query)
    academic_year = year_res.scalars().first()

    return {
        "class_name": class_name,
        "academic_year": academic_year,
        "total_students": total,
        "high_risk_count": high_risk,
        "safe_count": total - high_risk,
        "avg_risk_probability": avg_risk,
        "students_with_active_plan": with_plan,
        "outstanding_tasks": outstanding,
    }


async def get_advisor_student_overview(
    db: AsyncSession, advisor_id: uuid.UUID, student_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """Báo cáo 360° về một sinh viên lớp chủ nhiệm (hồ sơ, điểm, dự báo, kế hoạch, notes)."""
    row_query = (
        select(StudentProfile, User, AdvisorStudent.class_name)
        .join(User, StudentProfile.user_id == User.id)
        .join(AdvisorStudent, AdvisorStudent.student_id == StudentProfile.id)
        .where(
            and_(
                AdvisorStudent.advisor_id == advisor_id,
                StudentProfile.id == student_id,
            )
        )
    )
    row_res = await db.execute(row_query)
    row = row_res.first()
    if not row:
        return None

    sp, u, class_name = row

    # Danh sách môn học đã ghi danh
    courses_query = (
        select(StudentEnrollment, CoursePresentation, Course)
        .join(CoursePresentation, StudentEnrollment.presentation_id == CoursePresentation.id)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(StudentEnrollment.student_id == sp.id)
    )
    courses_res = await db.execute(courses_query)
    courses = [
        {
            "enrollment_id": str(enr.id),
            "code_module": course.code_module,
            "course_name": course.name,
            "code_presentation": pres.code_presentation,
            "studied_credits": enr.studied_credits,
            "final_result": enr.final_result,
        }
        for enr, pres, course in courses_res.all()
    ]

    # Dự báo rủi ro gần nhất
    pred_query = (
        select(PredictionRun, MLModel)
        .join(MLModel, PredictionRun.model_id == MLModel.id)
        .join(StudentFeatureSnapshot, PredictionRun.snapshot_id == StudentFeatureSnapshot.id)
        .join(StudentEnrollment, StudentFeatureSnapshot.enrollment_id == StudentEnrollment.id)
        .where(StudentEnrollment.student_id == sp.id)
        .order_by(desc(PredictionRun.created_at))
        .limit(1)
    )
    pred_res = await db.execute(pred_query)
    pred_row = pred_res.first()
    risk_prob = round(pred_row[0].risk_probability, 4) if pred_row else 0.0
    model_version = pred_row[1].version if pred_row else None

    # Kế hoạch can thiệp đang hoạt động
    plan_query = (
        select(InterventionPlan)
        .where(and_(InterventionPlan.student_id == sp.id, InterventionPlan.status == "ACTIVE"))
        .options(selectinload(InterventionPlan.tasks))
        .order_by(desc(InterventionPlan.created_at))
        .limit(1)
    )
    plan_res = await db.execute(plan_query)
    active_plan = plan_res.scalars().first()

    # Đếm ghi chép tư vấn theo enrollment của sinh viên
    notes_query = (
        select(func.count(AdvisingNote.id))
        .join(StudentEnrollment, AdvisingNote.enrollment_id == StudentEnrollment.id)
        .where(StudentEnrollment.student_id == sp.id)
    )
    notes_res = await db.execute(notes_query)
    notes_count = notes_res.scalar_one()

    help_query = select(func.count(StudentHelpRequest.id)).where(
        StudentHelpRequest.student_id == sp.id
    )
    help_res = await db.execute(help_query)
    help_count = help_res.scalar_one()

    return {
        "student_id": sp.id,
        "student_code": sp.student_code,
        "full_name": u.full_name,
        "email": u.email,
        "gender": sp.gender,
        "class_name": class_name,
        "highest_education": sp.highest_education,
        "age_band": sp.age_band,
        "courses": courses,
        "latest_risk_probability": risk_prob,
        "latest_risk_level": "HIGH_RISK" if risk_prob >= 0.5 else "SAFE",
        "latest_model_version": model_version,
        "active_plan": active_plan,
        "notes_count": notes_count,
        "help_requests_count": help_count,
    }


async def get_student_radar_for_advisor(
    db: AsyncSession,
    advisor_id: uuid.UUID,
    student_id: uuid.UUID,
    enrollment_id: Optional[uuid.UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Radar 6D năng lực của sinh viên lớp chủ nhiệm (chọn 1 enrollment)."""
    if not await advisor_owns_student(db, advisor_id, student_id):
        return None

    enr_query = select(StudentEnrollment).where(StudentEnrollment.student_id == student_id)
    if enrollment_id:
        enr_query = enr_query.where(StudentEnrollment.id == enrollment_id)
    enr_query = enr_query.order_by(desc(StudentEnrollment.date_registration)).limit(1)
    enr_res = await db.execute(enr_query)
    enr = enr_res.scalars().first()
    if not enr:
        return None

    pres_query = (
        select(CoursePresentation, Course)
        .join(Course, CoursePresentation.course_id == Course.id)
        .where(CoursePresentation.id == enr.presentation_id)
    )
    pres_res = await db.execute(pres_query)
    _, course = pres_res.first()

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

    return {
        "enrollment_id": enr.id,
        "code_module": course.code_module,
        "dimensions": calculate_radar_6d(snap_dict),
    }


async def get_advisor_intervention_plans(
    db: AsyncSession, advisor_id: uuid.UUID, status_filter: Optional[str] = None
) -> List[InterventionPlan]:
    """Danh sách kế hoạch can thiệp của toàn bộ sinh viên lớp chủ nhiệm."""
    query = (
        select(InterventionPlan)
        .join(AdvisorStudent, AdvisorStudent.student_id == InterventionPlan.student_id)
        .where(AdvisorStudent.advisor_id == advisor_id)
        .options(selectinload(InterventionPlan.tasks))
        .order_by(desc(InterventionPlan.created_at))
    )
    if status_filter:
        query = query.where(InterventionPlan.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_advisor_plan(
    db: AsyncSession, advisor_id: uuid.UUID, plan_id: uuid.UUID
) -> Optional[InterventionPlan]:
    """Lấy kế hoạch can thiệp nếu thuộc sinh viên lớp chủ nhiệm của GVCN."""
    query = (
        select(InterventionPlan)
        .join(AdvisorStudent, AdvisorStudent.student_id == InterventionPlan.student_id)
        .where(
            and_(
                InterventionPlan.id == plan_id,
                AdvisorStudent.advisor_id == advisor_id,
            )
        )
        .options(selectinload(InterventionPlan.tasks))
    )
    result = await db.execute(query)
    return result.scalars().first()


async def create_task_for_plan(
    db: AsyncSession,
    plan_id: uuid.UUID,
    category: str,
    priority: str,
    title: str,
    description: str,
    target_metric: str,
) -> InterventionTask:
    task = InterventionTask(
        plan_id=plan_id,
        category=category,
        priority=priority,
        title=title,
        description=description,
        target_metric=target_metric,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_student_advising_notes(
    db: AsyncSession, advisor_id: uuid.UUID, student_id: uuid.UUID
) -> List[AdvisingNote]:
    """Ghi chép tư vấn của sinh viên (chia sẻ giữa các GVCN cùng lớp chủ nhiệm)."""
    if not await advisor_owns_student(db, advisor_id, student_id):
        return []
    query = (
        select(AdvisingNote)
        .join(StudentEnrollment, AdvisingNote.enrollment_id == StudentEnrollment.id)
        .where(StudentEnrollment.student_id == student_id)
        .order_by(desc(AdvisingNote.meeting_date), desc(AdvisingNote.created_at))
    )
    result = await db.execute(query)
    return list(result.scalars().all())
