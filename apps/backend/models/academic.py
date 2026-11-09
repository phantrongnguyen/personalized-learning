import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import String, Integer, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code_module: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits_default: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    presentations: Mapped[List["CoursePresentation"]] = relationship(
        "CoursePresentation", back_populates="course", passive_deletes="all"
    )

    def __repr__(self) -> str:
        return f"<Course code_module={self.code_module}>"


class CoursePresentation(Base):
    __tablename__ = "course_presentations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    code_presentation: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    module_presentation_length: Mapped[int] = mapped_column(Integer, default=260, nullable=False)

    # Relationships
    course: Mapped[Course] = relationship("Course", back_populates="presentations")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="presentation", passive_deletes="all"
    )

    def __repr__(self) -> str:
        return f"<CoursePresentation {self.code_presentation}>"


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    presentation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_presentations.id", ondelete="RESTRICT"), nullable=False
    )
    date_registration: Mapped[int] = mapped_column(Integer, default=-10, nullable=False)
    date_unregistration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    studied_credits: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    num_of_prev_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    presentation: Mapped[CoursePresentation] = relationship("CoursePresentation", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<StudentEnrollment student={self.student_id} presentation={self.presentation_id}>"
