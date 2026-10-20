import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


# -------------------------------------------------------------
# USER MANAGEMENT SCHEMAS
# -------------------------------------------------------------
class AdminUserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone_number: Optional[str] = None
    role_codes: List[str] = Field(..., description="Ví dụ: ['ADMIN'] hoặc ['ADVISOR'] hoặc ['LECTURER'] hoặc ['STUDENT']")
    # Optional profile data
    student_code: Optional[str] = None
    gender: Optional[str] = "M"
    highest_education: Optional[str] = "HE Qualification"
    age_band: Optional[str] = "0-35"
    department: Optional[str] = "Khoa CNTT"
    lecturer_code: Optional[str] = None


class UserStatusUpdateIn(BaseModel):
    is_active: bool


class AdminPasswordResetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_password: SecretStr = Field(..., min_length=6, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: SecretStr):
        password = value.get_secret_value()
        if not password.strip():
            raise ValueError("Mật khẩu không được chỉ chứa khoảng trắng")
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu không được vượt quá 72 byte UTF-8")
        return value


class AdminPasswordResetOut(BaseModel):
    message: str
    user_id: uuid.UUID


class AdminUserUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=20)
    student_code: Optional[str] = Field(None, min_length=1, max_length=50)
    lecturer_code: Optional[str] = Field(None, min_length=1, max_length=50)
    department: Optional[str] = Field(None, min_length=1, max_length=150)
    academic_rank: Optional[str] = Field(None, min_length=1, max_length=50)
    office_location: Optional[str] = Field(None, max_length=100)

    @field_validator("email", "full_name", "student_code", "lecturer_code", "department", "academic_rank", mode="before")
    @classmethod
    def nonempty(cls, value):
        if value is None or not str(value).strip():
            raise ValueError("Trường này không được để trống")
        return str(value).strip()


class UserRolesUpdateIn(BaseModel):
    role_codes: List[str]


# -------------------------------------------------------------
# ACADEMIC MANAGEMENT SCHEMAS
# -------------------------------------------------------------
class CourseCreateIn(BaseModel):
    code_module: str
    name: str
    credits_default: int = Field(30, gt=0)
    description: Optional[str] = None


class CoursePresentationCreateIn(BaseModel):
    course_id: uuid.UUID
    code_presentation: str
    module_presentation_length: int = Field(268, gt=0)
    start_date: Optional[date] = None


class AssignAdvisorIn(BaseModel):
    advisor_id: uuid.UUID
    student_id: uuid.UUID
    academic_year: str = "2026-2027"
    class_name: str


class AssignLecturerIn(BaseModel):
    lecturer_id: uuid.UUID
    presentation_id: uuid.UUID
    role_in_course: str = "GIANG_VIEN_CHINH"


# -------------------------------------------------------------
# MLOPS & BATCH PREDICT SCHEMAS
# -------------------------------------------------------------
class MLModelOut(BaseModel):
    id: uuid.UUID
    model_name: str
    version: str
    threshold: float
    cutoff_fraction: float
    accuracy: Optional[float] = None
    roc_auc: Optional[float] = None
    average_precision: Optional[float] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivateModelIn(BaseModel):
    model_id: uuid.UUID


class BatchPredictResultOut(BaseModel):
    total_snapshots_scanned: int
    predictions_generated: int
    high_risk_count: int
    safe_count: int
    execution_time_ms: int
    model_id: uuid.UUID | None = None
    model_version: str | None = None
    threshold: float | None = None
    model_sha256: str | None = None


# -------------------------------------------------------------
# AUDIT LOG SCHEMAS
# -------------------------------------------------------------
class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_full_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
