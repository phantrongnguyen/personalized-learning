import uuid
from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class InterventionPlan(Base):
    __tablename__ = "intervention_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prediction_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prediction_runs.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advisor_note_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    tasks: Mapped[List["InterventionTask"]] = relationship(
        "InterventionTask", back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<InterventionPlan id={self.id} status={self.status}>"


class InterventionTask(Base):
    __tablename__ = "intervention_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intervention_plans.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_metric: Mapped[str] = mapped_column(String(100), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    student_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    plan: Mapped[InterventionPlan] = relationship("InterventionPlan", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<InterventionTask title={self.title} is_completed={self.is_completed}>"


class AdvisingNote(Base):
    __tablename__ = "advising_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_enrollments.id", ondelete="CASCADE"), nullable=False
    )
    advisor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("advisor_profiles.id", ondelete="CASCADE"), nullable=False
    )
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_type: Mapped[str] = mapped_column(String(50), default="ONLINE", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agreed_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AdvisingNote id={self.id} date={self.meeting_date}>"
