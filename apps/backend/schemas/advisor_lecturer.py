import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------------
# SCHEMAS FOR ADVISOR (GVCN)
# -------------------------------------------------------------
class ClassOverviewOut(BaseModel):
    class_name: str
    academic_year: str
    total_students: int
    high_risk_count: int
    safe_count: int

    model_config = ConfigDict(from_attributes=True)


class AdvisorStudentSummaryOut(BaseModel):
    student_id: uuid.UUID
    student_code: str
    full_name: str
    gender: str
    class_name: str
    risk_probability: Optional[float] = 0.0
    risk_level: str = "SAFE"  # 'SAFE' hoặc 'HIGH_RISK'
    has_active_plan: bool = False
    uncompleted_tasks_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TaskCreateIn(BaseModel):
    category: str = Field(..., description="CHUYEN_CAN, HOC_THUAT, TIEN_DO, TAM_LY")
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    title: str
    description: str
    target_metric: str = "Tăng lượt tương tác / Hoàn thành bài tập"


class TaskOut(BaseModel):
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


class PlanCreateIn(BaseModel):
    enrollment_id: Optional[uuid.UUID] = None
    student_id: uuid.UUID
    target_completion_date: Optional[date] = None
    advisor_note_summary: Optional[str] = None
    tasks: List[TaskCreateIn] = []


class PlanOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    prediction_run_id: uuid.UUID
    status: str
    target_completion_date: Optional[date] = None
    advisor_note_summary: Optional[str] = None
    created_at: datetime
    tasks: List[TaskOut] = []

    model_config = ConfigDict(from_attributes=True)


class NoteCreateIn(BaseModel):
    enrollment_id: uuid.UUID
    meeting_date: date
    meeting_type: str = "ONLINE"
    content: str
    agreed_actions: Optional[str] = None


class NoteOut(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    advisor_id: uuid.UUID
    meeting_date: date
    meeting_type: str
    content: str
    agreed_actions: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassStatisticsOut(BaseModel):
    class_name: str
    academic_year: Optional[str] = None
    total_students: int
    high_risk_count: int
    safe_count: int
    avg_risk_probability: float = 0.0
    students_with_active_plan: int = 0
    outstanding_tasks: int = 0


class PlanUpdateIn(BaseModel):
    status: Optional[str] = Field(None, description="ACTIVE, COMPLETED, CANCELLED")
    target_completion_date: Optional[date] = None
    advisor_note_summary: Optional[str] = None


class StudentOverviewOut(BaseModel):
    student_id: uuid.UUID
    student_code: str
    full_name: str
    email: str
    gender: str
    class_name: Optional[str] = None
    highest_education: Optional[str] = None
    age_band: Optional[str] = None
    courses: List[Dict[str, Any]] = []
    latest_risk_probability: float = 0.0
    latest_risk_level: str = "SAFE"
    latest_model_version: Optional[str] = None
    active_plan: Optional[PlanOut] = None
    notes_count: int = 0
    help_requests_count: int = 0


# -------------------------------------------------------------
# SCHEMAS FOR LECTURER (GVBM)
# -------------------------------------------------------------
class LecturerCourseOut(BaseModel):
    presentation_id: uuid.UUID
    code_module: str
    course_name: str
    code_presentation: str
    module_length: int
    role_in_course: str
    total_students: int

    model_config = ConfigDict(from_attributes=True)


class StudentRiskInCourseOut(BaseModel):
    student_id: uuid.UUID
    student_code: str
    full_name: str
    enrollment_id: uuid.UUID
    total_clicks: int = 0
    late_submissions: int = 0
    submission_rate: float = 0.0
    risk_probability: float = 0.0
    risk_status: str = "SAFE"

    model_config = ConfigDict(from_attributes=True)


class CourseTaskAssignIn(BaseModel):
    student_id: uuid.UUID
    title: str
    description: str
    priority: str = "HIGH"
    target_metric: str = "Hoàn thành bài tập ôn tập môn học"


class CourseStudentOut(BaseModel):
    student_id: uuid.UUID
    student_code: str
    full_name: str
    enrollment_id: uuid.UUID
    gender: str = "M"
    final_result: Optional[str] = None
    total_clicks: int = 0
    late_submissions: int = 0
    submission_rate: float = 0.0
    risk_probability: float = 0.0
    risk_status: str = "SAFE"

    model_config = ConfigDict(from_attributes=True)


class AssessmentUpdateIn(BaseModel):
    assessments_submitted: Optional[int] = Field(None, ge=0)
    late_submissions: Optional[int] = Field(None, ge=0)
    submission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    final_result: Optional[str] = Field(None, description="PASS, FAIL, WITHDRAWN, DISTINCTION")


class AlertAdvisorIn(BaseModel):
    presentation_id: uuid.UUID
    subject: str = "Cảnh báo học tập bất thường môn học"
    content: str
