import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    student_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    highest_education: Mapped[str] = mapped_column(String(100), nullable=False)
    age_band: Mapped[str] = mapped_column(String(20), nullable=False)
    imd_band: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    disability: Mapped[str] = mapped_column(String(10), default="N", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student_profile")

    def __repr__(self) -> str:
        return f"<StudentProfile student_code={self.student_code}>"


class AdvisorProfile(Base):
    __tablename__ = "advisor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    department: Mapped[str] = mapped_column(String(150), nullable=False)
    office_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lms_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="advisor_profile")

    def __repr__(self) -> str:
        return f"<AdvisorProfile department={self.department}>"


class LecturerProfile(Base):
    __tablename__ = "lecturer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    lecturer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(150), nullable=False)
    academic_rank: Mapped[str] = mapped_column(String(50), default="Giảng viên", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="lecturer_profile")

    def __repr__(self) -> str:
        return f"<LecturerProfile lecturer_code={self.lecturer_code}>"
