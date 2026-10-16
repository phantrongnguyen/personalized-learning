import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class CourseReminderOut(BaseModel):
    id: str
    enrollment_id: uuid.UUID
    code_module: str
    course_name: str
    code_presentation: str
    title: str
    message: str
    pending_tasks: int
    due_date: Optional[date] = None
    days_remaining: Optional[int] = None
    state: Literal["pending", "due_soon", "overdue"]
    level: Literal["info", "warning", "danger"]


class StudentProfileDetailOut(BaseModel):
    id: uuid.UUID
    student_code: str
    full_name: str
    email: str
    gender: str
    highest_education: str
    age_band: str
    imd_band: Optional[str] = None
    region: Optional[str] = None
    disability: str
    studied_credits_total: int = 0

    model_config = ConfigDict(from_attributes=True)


class StudentCourseItemOut(BaseModel):
    enrollment_id: uuid.UUID
    code_module: str
    course_name: str
    code_presentation: str
    studied_credits: int
    final_result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RiskPredictionOut(BaseModel):
    enrollment_id: uuid.UUID
    code_module: str
    cutoff_stage: str
    risk_probability: float
    risk_level: str
    model_version: str
    predicted_at: datetime
    pedagogical_recommendations: List[str] = []
    data_source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RadarDimension(BaseModel):
    metric: str
    student_value: float
    benchmark_value: float
    percentile: float


class RadarDataOut(BaseModel):
    enrollment_id: uuid.UUID
    code_module: str
    dimensions: List[RadarDimension]
    data_source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudentTaskItemOut(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    category: str
    priority: str
    title: str
    description: str
    target_metric: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    student_feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskCompleteIn(BaseModel):
    enrollment_id: Optional[uuid.UUID] = None
    student_feedback: Optional[str] = Field(None, description="Ghi chú phản hồi khi hoàn thành")


class HelpRequestCreateIn(BaseModel):
    enrollment_id: Optional[uuid.UUID] = None
    target_role: str = Field(..., description="ADVISOR hoặc LECTURER")
    presentation_id: Optional[uuid.UUID] = None
    target_user_id: Optional[uuid.UUID] = None
    subject: str = Field(..., min_length=3)
    content: str = Field(..., min_length=5)


class HelpRequestOut(BaseModel):
    id: uuid.UUID
    target_role: str
    presentation_id: Optional[uuid.UUID] = None
    target_user_id: Optional[uuid.UUID] = None
    subject: str
    content: str
    status: str
    response_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
