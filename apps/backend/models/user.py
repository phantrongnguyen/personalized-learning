from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, DateTime, SmallInteger, Text, ForeignKey, Table, Column
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# Bảng liên kết trung gian N-N: user_roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", SmallInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_roles, back_populates="roles", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role code={self.code}>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    roles: Mapped[List[Role]] = relationship(
        Role, secondary=user_roles, back_populates="users", lazy="selectin"
    )
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="user", uselist=False, passive_deletes="all", lazy="selectin"
    )
    advisor_profile: Mapped[Optional["AdvisorProfile"]] = relationship(
        "AdvisorProfile", back_populates="user", uselist=False, passive_deletes="all", lazy="selectin"
    )
    lecturer_profile: Mapped[Optional["LecturerProfile"]] = relationship(
        "LecturerProfile", back_populates="user", uselist=False, passive_deletes="all", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User email={self.email} full_name={self.full_name}>"
