"""Resolve support recipients through assignments, never through arbitrary user IDs."""
from fastapi import HTTPException
from sqlalchemy import select

from models.assignment import AdvisorStudent, CourseLecturer
from models.profile import AdvisorProfile, LecturerProfile
from models.user import User


async def resolve_help_recipient(db, student_id, target_role, presentation_id, target_user_id):
    if target_role == "ADVISOR":
        query = (
            select(User.id)
            .join(AdvisorProfile, AdvisorProfile.user_id == User.id)
            .join(AdvisorStudent, AdvisorStudent.advisor_id == AdvisorProfile.id)
            .where(AdvisorStudent.student_id == student_id)
            .order_by(AdvisorStudent.assigned_at.desc(), AdvisorStudent.id.desc())
        )
    elif target_role == "LECTURER":
        if presentation_id is None:
            raise HTTPException(422, "Vui lòng chọn học phần khi gửi yêu cầu tới giảng viên")
        query = (
            select(User.id)
            .join(LecturerProfile, LecturerProfile.user_id == User.id)
            .join(CourseLecturer, CourseLecturer.lecturer_id == LecturerProfile.id)
            .where(CourseLecturer.presentation_id == presentation_id)
            .order_by(CourseLecturer.assigned_at.desc(), CourseLecturer.id.desc())
        )
    else:
        raise HTTPException(422, "Vai trò nhận yêu cầu không hợp lệ")

    query = query.where(User.is_active.is_(True), User.roles.any(code=target_role))
    if target_user_id is not None:
        query = query.where(User.id == target_user_id)
    recipient = (await db.execute(query.limit(1))).scalar_one_or_none()
    if target_user_id is not None and recipient is None:
        raise HTTPException(403, "Người nhận không được phân công phụ trách hoặc không hoạt động")
    # No explicit recipient and no assignment: retain an unassigned support request.
    return recipient
