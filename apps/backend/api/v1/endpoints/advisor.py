import io
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openpyxl import Workbook

from core.database import get_db
from core.permissions import RequireRoles
from models.user import User
from models.intervention import InterventionPlan, InterventionTask, AdvisingNote
from models.academic import StudentEnrollment
from services.risk_service import current_prediction
from schemas.advisor_lecturer import (
    ClassOverviewOut,
    AdvisorStudentSummaryOut,
    ClassStatisticsOut,
    StudentOverviewOut,
    PlanCreateIn,
    PlanUpdateIn,
    PlanOut,
    TaskCreateIn,
    TaskOut,
    NoteCreateIn,
    NoteOut,
)
from schemas.student import RadarDataOut
from repositories.student_repo import get_owned_enrollment
from repositories.academic_repo import (
    get_advisor_profile_by_user_id,
    get_advisor_classes,
    get_advisor_students,
    create_intervention_plan_with_tasks,
    advisor_owns_student,
    get_class_statistics,
    get_advisor_student_overview,
    get_student_radar_for_advisor,
    get_advisor_intervention_plans,
    get_advisor_plan,
    create_task_for_plan,
    get_student_advising_notes,
)

router = APIRouter()

# Yêu cầu vai trò ADVISOR (hoặc ADMIN)
require_advisor = RequireRoles(["ADVISOR"])


@router.get("/classes", response_model=List[ClassOverviewOut], summary="Danh sách lớp sinh hoạt phụ trách")
async def get_my_classes(
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_advisor_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_advisor_classes(db, profile.id)


@router.get("/students", response_model=List[AdvisorStudentSummaryOut], summary="Danh sách sinh viên lớp chủ nhiệm")
async def get_my_students(
    class_name: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_advisor_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_advisor_students(db, profile.id, class_name, limit=limit, offset=offset)


@router.post("/interventions", response_model=PlanOut, summary="Lập kế hoạch can thiệp cho sinh viên")
async def create_intervention_plan(
    payload: PlanCreateIn,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    await _require_owned_student(db, profile.id, payload.student_id)
    enrollment_id = payload.enrollment_id
    if enrollment_id is None:
        enrollments = (await db.execute(select(StudentEnrollment.id).where(
            StudentEnrollment.student_id == payload.student_id,
        ))).scalars().all()
        if len(enrollments) != 1:
            raise HTTPException(422, "Vui lòng chọn học phần khi lập kế hoạch can thiệp")
        enrollment_id = enrollments[0]
    if await get_owned_enrollment(db, payload.student_id, enrollment_id) is None:
        raise HTTPException(404, "Đăng ký học phần không thuộc sinh viên")
    _, latest_pred = await current_prediction(db, enrollment_id)

    if not latest_pred:
        # Nếu chưa có prediction_run, kiểm tra xem có model active để sinh snapshot hoặc từ chối
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Snapshot hiện tại của học phần chưa có dự báo; vui lòng chạy lại dự báo",
        )

    tasks_dicts = [t.model_dump() for t in payload.tasks]
    plan = await create_intervention_plan_with_tasks(
        db=db,
        student_id=payload.student_id,
        prediction_run_id=latest_pred.id,
        target_completion_date=payload.target_completion_date,
        advisor_note_summary=payload.advisor_note_summary,
        tasks_data=tasks_dicts,
    )
    return plan


@router.post("/advising-notes", response_model=NoteOut, summary="Ghi chép sổ tay tư vấn sinh viên")
async def create_advising_note(
    payload: NoteCreateIn,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    enrollment = await db.get(StudentEnrollment, payload.enrollment_id)
    if enrollment is None:
        raise HTTPException(404, "Không tìm thấy đăng ký học phần")
    await _require_owned_student(db, profile.id, enrollment.student_id)

    note = AdvisingNote(
        enrollment_id=payload.enrollment_id,
        advisor_id=profile.id,
        meeting_date=payload.meeting_date,
        meeting_type=payload.meeting_type,
        content=payload.content,
        agreed_actions=payload.agreed_actions,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ==============================================================================
# PHÂN TÍCH CHUYÊN SÂU LỚP CHỦ NHIỆM
# ==============================================================================
def _require_advisor_profile(profile):
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản chưa có hồ sơ Cố vấn học tập (AdvisorProfile)",
        )
    return profile


async def _require_owned_student(db: AsyncSession, advisor_id: uuid.UUID, student_id: uuid.UUID):
    if not await advisor_owns_student(db, advisor_id, student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sinh viên này không thuộc lớp chủ nhiệm của bạn",
        )


@router.get(
    "/classes/{class_name}/statistics",
    response_model=ClassStatisticsOut,
    summary="Thống kê tình hình rủi ro của một lớp sinh hoạt",
)
async def get_class_stats(
    class_name: str,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    stats = await get_class_statistics(db, profile.id, class_name)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy lớp này hoặc bạn không được phân công chủ nhiệm",
        )
    return stats


@router.get(
    "/students/{student_id}/overview",
    response_model=StudentOverviewOut,
    summary="Báo cáo 360° về sinh viên lớp chủ nhiệm",
)
async def get_student_overview(
    student_id: uuid.UUID,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    overview = await get_advisor_student_overview(db, profile.id, student_id)
    if not overview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sinh viên không tồn tại trong lớp chủ nhiệm của bạn",
        )
    return overview


@router.get(
    "/students/{student_id}/radar",
    response_model=RadarDataOut,
    summary="Radar hành vi tại snapshot so với mốc tham khảo minh họa",
)
async def get_student_radar(
    student_id: uuid.UUID,
    enrollment_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    radar = await get_student_radar_for_advisor(db, profile.id, student_id, enrollment_id)
    if not radar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy dữ liệu radar cho sinh viên/học phần yêu cầu",
        )
    return radar


# ==============================================================================
# QUẢN LÝ KẾ HOẠCH CAN THIỆP & GHI CHÉP TƯ VẤN
# ==============================================================================
@router.get("/interventions", response_model=List[PlanOut], summary="Danh sách kế hoạch can thiệp của lớp chủ nhiệm")
async def list_intervention_plans(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_advisor_profile_by_user_id(db, current_user.id)
    if not profile:
        return []
    return await get_advisor_intervention_plans(db, profile.id, status_filter)


@router.put("/interventions/{plan_id}", response_model=PlanOut, summary="Cập nhật kế hoạch can thiệp")
async def update_intervention_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdateIn,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    plan = await get_advisor_plan(db, profile.id, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kế hoạch can thiệp không tồn tại hoặc không thuộc lớp chủ nhiệm của bạn",
        )

    if payload.status is not None:
        plan.status = payload.status
    if payload.target_completion_date is not None:
        plan.target_completion_date = payload.target_completion_date
    if payload.advisor_note_summary is not None:
        plan.advisor_note_summary = payload.advisor_note_summary

    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/interventions/{plan_id}/tasks", response_model=TaskOut, summary="Bổ sung nhiệm vụ vào kế hoạch can thiệp")
async def add_plan_task(
    plan_id: uuid.UUID,
    payload: TaskCreateIn,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    plan = await get_advisor_plan(db, profile.id, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kế hoạch can thiệp không tồn tại hoặc không thuộc lớp chủ nhiệm của bạn",
        )

    return await create_task_for_plan(
        db,
        plan_id=plan.id,
        category=payload.category,
        priority=payload.priority,
        title=payload.title,
        description=payload.description,
        target_metric=payload.target_metric,
    )


@router.get(
    "/students/{student_id}/notes",
    response_model=List[NoteOut],
    summary="Ghi chép sổ tay tư vấn của sinh viên",
)
async def list_student_notes(
    student_id: uuid.UUID,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))
    await _require_owned_student(db, profile.id, student_id)
    return await get_student_advising_notes(db, profile.id, student_id)


# ==============================================================================
# XUẤT BÁO CÁO NGUY CƠ RA EXCEL
# ==============================================================================
@router.get("/export/risk-report", summary="Xuất báo cáo nguy cơ của lớp chủ nhiệm ra Excel (.xlsx)")
async def export_risk_report(
    class_name: Optional[str] = None,
    current_user: User = Depends(require_advisor),
    db: AsyncSession = Depends(get_db),
):
    profile = _require_advisor_profile(await get_advisor_profile_by_user_id(db, current_user.id))

    if class_name:
        class_names = [class_name]
    else:
        class_names = [c["class_name"] for c in await get_advisor_classes(db, profile.id)]

    rows: List[dict] = []
    for c_name in class_names:
        rows.extend(await get_advisor_students(db, profile.id, c_name))

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "BaoCaoNguyCo"
    sheet.append([
        "Lớp",
        "Mã SV",
        "Họ tên",
        "Giới tính",
        "Xác suất rủi ro",
        "Mức độ",
        "Có kế hoạch can thiệp",
        "Nhiệm vụ chưa hoàn thành",
        "Số học phần chưa dự báo",
    ])
    for s in rows:
        sheet.append([
            s["class_name"],
            s["student_code"],
            s["full_name"],
            s["gender"],
            s["risk_probability"],
            s["risk_level"],
            "Có" if s["has_active_plan"] else "Không",
            s["uncompleted_tasks_count"],
            s["unpredicted_courses"],
        ])

    # Giãn cột cho dễ đọc
    for idx, width in zip("ABCDEFGHI", [16, 14, 28, 10, 16, 20, 22, 24, 24]):
        sheet.column_dimensions[idx].width = width

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)

    filename = f"bao_cao_nguy_co_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
