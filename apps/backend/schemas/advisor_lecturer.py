import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from schemas.prediction import RiskLevel, Ratio


# -------------------------------------------------------------
# SCHEMAS FOR ADVISOR (GVCN)
# -------------------------------------------------------------
class ClassOverviewOut(BaseModel):
    class_name: str
    academic_year: str
    total_students: int
    high_risk_count: int
    safe_count: int
    not_predicted_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdvisorStudentSummaryOut(BaseModel):
    student_id: uuid.UUID
    student_code: str
    full_name: str
    gender: str
    class_name: str
    risk_probability: Ratio | None = None
    risk_level: RiskLevel = "NOT_PREDICTED"
    total_courses: int = 0
    predicted_courses: int = 0
    high_risk_courses: int = 0
    unpredicted_courses: int = 0
    risk_aggregation: str = "ANY_HIGH_ELSE_ALL_SAFE"
    has_active_plan: bool = False
    uncompleted_tasks_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TaskCreateIn(BaseModel):
    category: str = Field(..., description="CHUYEN_CAN, HOC_THUAT, TIEN_DO, TAM_LY")
    priority: Literal['LOW', 'MEDIUM', 'HIGH'] = 'MEDIUM'
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
    not_predicted_count: int = 0
    avg_risk_probability: Ratio | None = None
    students_with_active_plan: int = 0
    outstanding_tasks: int = 0


class PlanUpdateIn(BaseModel):
    status: Literal['ACTIVE', 'COMPLETED', 'CANCELLED'] | None = None
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
    latest_risk_probability: Ratio | None = None
    latest_risk_level: RiskLevel = "NOT_PREDICTED"
    total_courses: int = 0
    predicted_courses: int = 0
    high_risk_courses: int = 0
    unpredicted_courses: int = 0
    risk_aggregation: str = "ANY_HIGH_ELSE_ALL_SAFE"
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
    total_clicks: int | None = None
    late_submissions: int | None = None
    submission_rate: float | None = None
    risk_probability: Ratio | None = None
    risk_status: RiskLevel = "NOT_PREDICTED"

    model_config = ConfigDict(from_attributes=True)


class CourseTaskAssignIn(BaseModel):
    student_id: uuid.UUID
    title: str
    description: str
    priority: Literal['LOW', 'MEDIUM', 'HIGH'] = 'HIGH'
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
    risk_probability: Ratio | None = None
    risk_status: RiskLevel = "NOT_PREDICTED"

    model_config = ConfigDict(from_attributes=True)


class AssessmentUpdateIn(BaseModel):
    assessments_submitted: Optional[int] = Field(None, ge=0)
    late_submissions: Optional[int] = Field(None, ge=0)
    submission_rate: Ratio | None = None
    final_result: Literal['PASS', 'FAIL', 'WITHDRAWN', 'DISTINCTION', 'Pass', 'Fail', 'Withdrawn', 'Distinction'] | None = None


class AlertAdvisorIn(BaseModel):
    presentation_id: uuid.UUID
    subject: str = "Cảnh báo học tập bất thường môn học"
    content: str
