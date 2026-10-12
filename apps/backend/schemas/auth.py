import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="admin@huit.edu.vn")
    password: str = Field(..., min_length=1, example="123")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RoleOut(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class StudentProfileOut(BaseModel):
    id: uuid.UUID
    student_code: str
    gender: str
    highest_education: str
    age_band: str
    imd_band: Optional[str] = None
    region: Optional[str] = None
    disability: str

    class Config:
        from_attributes = True


class AdvisorProfileOut(BaseModel):
    id: uuid.UUID
    department: str
    office_location: Optional[str] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    roles: List[RoleOut] = []
    student_profile: Optional[StudentProfileOut] = None
    advisor_profile: Optional[AdvisorProfileOut] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
