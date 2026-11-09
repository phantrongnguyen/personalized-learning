import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class CourseLecturer(Base):
    __tablename__ = "course_lecturers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lecturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lecturer_profiles.id", ondelete="CASCADE"), nullable=False
    )
    presentation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_presentations.id", ondelete="CASCADE"), nullable=False
    )
    role_in_course: Mapped[str] = mapped_column(String(50), default="GIANG_VIEN_CHINH", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("lecturer_id", "presentation_id", name="uq_lecturer_presentation"),
    )

    def __repr__(self) -> str:
        return f"<CourseLecturer lecturer={self.lecturer_id} presentation={self.presentation_id}>"


class AdvisorStudent(Base):
    __tablename__ = "advisor_students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    advisor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("advisor_profiles.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("advisor_id", "student_id", name="uq_advisor_student"),
    )

    def __repr__(self) -> str:
        return f"<AdvisorStudent advisor={self.advisor_id} student={self.student_id} class={self.class_name}>"
