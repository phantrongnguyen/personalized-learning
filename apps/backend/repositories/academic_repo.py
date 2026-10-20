import uuid
from datetime import date, datetime, timezone
from copy import deepcopy
from fastapi import HTTPException
from pydantic import ValidationError
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.user import User
from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.assignment import AdvisorStudent, CourseLecturer
from models.feature import StudentFeatureSnapshot
from models.intervention import InterventionPlan, InterventionTask, AdvisingNote
from models.help_request import StudentHelpRequest
from services.radar_service import calculate_radar_6d
from services.risk_service import current_prediction, latest_snapshot, risk_fields, student_risk_summary, student_risk_summaries, current_predictions
from services.prediction_service import BEHAVIOR_FIELDS
from schemas.prediction import BehaviorFeatures


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
        students = await get_advisor_students(db, advisor_id, row.class_name, row.academic_year)
        classes_summary.append({
            "class_name": row.class_name,
            "academic_year": row.academic_year,
            "total_students": row.total_students,
            "high_risk_count": sum(s["risk_level"] == "HIGH_RISK" for s in students),
            "safe_count": sum(s["risk_level"] == "SAFE" for s in students),
            "not_predicted_count": sum(s["risk_level"] == "NOT_PREDICTED" for s in students),
        })
    return classes_summary


async def get_advisor_students(
    db: AsyncSession, advisor_id: uuid.UUID, class_name: Optional[str] = None,
    academic_year: Optional[str] = None, limit: Optional[int] = None, offset: int = 0,
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
    if academic_year:
        query = query.where(AdvisorStudent.academic_year == academic_year)

    query = query.order_by(StudentProfile.student_code, StudentProfile.id)
    if limit is not None:
        query = query.limit(limit).offset(offset)
    records = (await db.execute(query)).all()
    ids = [sp.id for sp, _, _ in records]
    summaries = await student_risk_summaries(db, ids)
    plan_counts = {}
    if ids:
        counts = await db.execute(select(InterventionPlan.student_id,
            func.count(func.distinct(InterventionPlan.id)),
            func.count(InterventionTask.id).filter(InterventionTask.is_completed.is_(False)))
            .outerjoin(InterventionTask, InterventionTask.plan_id == InterventionPlan.id)
            .where(InterventionPlan.student_id.in_(ids), InterventionPlan.status == "ACTIVE")
            .group_by(InterventionPlan.student_id))
        plan_counts = {student_id: (plans, tasks) for student_id, plans, tasks in counts}
    students_data = []
    for sp, u, c_name in records:
        summary = dict(summaries[sp.id])
        summary.pop("representative_prediction")
        active_plans, uncompleted = plan_counts.get(sp.id, (0, 0))

        students_data.append({
            "student_id": sp.id,
            "student_code": sp.student_code,
            "full_name": u.full_name,
            "gender": sp.gender,
            "class_name": c_name,
            **summary,
            "has_active_plan": bool(active_plans),
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
    counts = select(StudentEnrollment.presentation_id,
        func.count(StudentEnrollment.id).label("total_students")).group_by(StudentEnrollment.presentation_id).subquery()
    query = (select(CoursePresentation, Course, CourseLecturer.role_in_course,
                    func.coalesce(counts.c.total_students, 0))
        .join(CourseLecturer, CourseLecturer.presentation_id == CoursePresentation.id)
        .join(Course, CoursePresentation.course_id == Course.id)
        .outerjoin(counts, counts.c.presentation_id == CoursePresentation.id)
        .where(CourseLecturer.lecturer_id == lecturer_id)
        .order_by(CoursePresentation.id))
    rows = (await db.execute(query)).all()
    courses = []
    for cp, c, role, total_students in rows:
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
    db: AsyncSession, presentation_id: uuid.UUID, limit: Optional[int] = None, offset: int = 0
) -> List[Dict[str, Any]]:
    """Lấy danh sách sinh viên kèm tương tác và nguy cơ trong lớp học phần"""
    query = (
        select(StudentEnrollment, StudentProfile, User)
        .join(StudentProfile, StudentEnrollment.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(StudentEnrollment.presentation_id == presentation_id)
    )
    query = query.order_by(StudentProfile.student_code, StudentEnrollment.id)
    if limit is not None:
        query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    enrollments = result.all()

    current = await current_predictions(db, [se.id for se, _, _ in enrollments])
    risk_board = []
    for se, sp, u in enrollments:
        snap, pred = current.get(se.id, (None, None))

        total_clicks = snap.total_clicks_to_t if snap else None
        late_sub = snap.late_submissions_to_t if snap else None
        sub_rate = snap.submission_rate if snap else None

        risk = risk_fields(pred)

        risk_board.append({
            "student_id": sp.id,
            "student_code": sp.student_code,
            "full_name": u.full_name,
            "enrollment_id": se.id,
            "total_clicks": total_clicks,
            "late_submissions": late_sub,
            "submission_rate": round(sub_rate, 2) if sub_rate is not None else None,
            "risk_probability": risk["risk_probability"],
            "risk_status": risk["risk_level"],
        })

    return risk_board


async def get_course_students(
    db: AsyncSession, presentation_id: uuid.UUID, limit: Optional[int] = None, offset: int = 0
) -> List[Dict[str, Any]]:
    """Danh sách sinh viên trong lớp học phần (kèm kết quả & mức độ tương tác)"""
    query = (
        select(StudentEnrollment, StudentProfile, User)
        .join(StudentProfile, StudentEnrollment.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(StudentEnrollment.presentation_id == presentation_id)
    )
    query = query.order_by(StudentProfile.student_code, StudentEnrollment.id)
    if limit is not None:
        query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    enrollments = result.all()

    current = await current_predictions(db, [se.id for se, _, _ in enrollments])
    students = []
    for se, sp, u in enrollments:
        snap, pred = current.get(se.id, (None, None))
        risk = risk_fields(pred)

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
            "risk_probability": risk["risk_probability"],
            "risk_status": risk["risk_level"],
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
    updated_by_user_id: Optional[uuid.UUID] = None,
) -> Optional[Dict[str, Any]]:
    """GVBM cập nhật điểm/tiến độ đánh giá của sinh viên trong lớp học phần.

    Create a new snapshot for metric updates; old predictions retain their inputs.
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
        .with_for_update(of=StudentEnrollment)
    )
    enr_res = await db.execute(enr_query)
    row = enr_res.first()
    if not row:
        return None

    enr, sp = row

    snap = await latest_snapshot(db, enr.id)
    updates = {name: value for name, value in {
        "assessments_submitted_to_t": assessments_submitted,
        "late_submissions_to_t": late_submissions,
        "submission_rate": submission_rate,
    }.items() if value is not None}
    if updates:
        if snap is None:
            raise HTTPException(409, "Chưa có snapshot nền để cập nhật tiến độ; cần nhập đủ dữ liệu ban đầu")
        # Validate numeric metrics using the same fields as inference, without
        # rejecting a real course simply because it is outside the OULAD model.
        values = {name: getattr(snap, name) for name in BEHAVIOR_FIELDS}
        values.update(updates)
        try:
            values = BehaviorFeatures(**values).model_dump()
        except ValidationError as exc:
            raise HTTPException(422, "Chỉ số snapshot không hợp lệ") from exc
        metadata = deepcopy(snap.raw_features_json or {})
        metadata["snapshot_metadata"] = {
            "source": "lecturer_assessment", "previous_snapshot_id": str(snap.id),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "updated_by_user_id": str(updated_by_user_id) if updated_by_user_id else None,
        }
        snap = StudentFeatureSnapshot(
            enrollment_id=enr.id, cutoff_stage=snap.cutoff_stage,
            raw_features_json=metadata, **values,
        )
        db.add(snap)
    if final_result is not None:
        enr.final_result = final_result

    db.add(enr)
    await db.commit()

    return {
        "enrollment_id": enr.id,
        "student_id": sp.id,
        "snapshot_id": snap.id if snap else None,
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
    probabilities = [s["risk_probability"] for s in students if s["risk_probability"] is not None]
    avg_risk = round(sum(probabilities) / len(probabilities), 4) if probabilities else None

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
        "safe_count": sum(s["risk_level"] == "SAFE" for s in students),
        "not_predicted_count": sum(s["risk_level"] == "NOT_PREDICTED" for s in students),
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

    summary = await student_risk_summary(db, sp.id)
    representative = summary.pop("representative_prediction")
    model_version = (representative.inference_context or {}).get("model_version") if representative else None

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
        "latest_risk_probability": summary["risk_probability"],
        "latest_risk_level": summary["risk_level"],
        **{key: value for key, value in summary.items() if key not in ("risk_probability", "risk_level")},
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
        .order_by(desc(StudentFeatureSnapshot.created_at), desc(StudentFeatureSnapshot.id))
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
