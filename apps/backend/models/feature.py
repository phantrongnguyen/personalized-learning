import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class StudentFeatureSnapshot(Base):
    __tablename__ = "student_feature_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_enrollments.id", ondelete="RESTRICT"), nullable=False
    )
    cutoff_stage: Mapped[str] = mapped_column(String(30), default="CUTOFF_75", nullable=False)

    # 17 biến đặc trưng hành vi OULAD
    total_clicks_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_resource_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_url_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_days_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_day_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    days_since_last_activity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_recent_7: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_recent_30: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assessments_submitted_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    late_submissions_to_t: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submission_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    raw_features_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<StudentFeatureSnapshot id={self.id} cutoff={self.cutoff_stage}>"
