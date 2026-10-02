from pydantic import BaseModel, Field, model_validator

from app.schemas.prediction import PredictionInput


class AssessmentRecord(BaseModel):
    model_config = {"extra": "forbid"}

    assessment_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    due_day: int | None = Field(default=None, ge=-1000, le=2000)
    submitted_day: int | None = Field(default=None, ge=-1000, le=2000)
    is_banked: bool = False
    is_exempt: bool = False

    @model_validator(mode="after")
    def validate_banked(self):
        if self.is_banked and self.submitted_day is None:
            raise ValueError("Bài bảo lưu cần ngày ghi nhận hoàn thành; không tự coi là đã nộp.")
        return self


class LearningEvidence(BaseModel):
    model_config = {"extra": "forbid"}

    snapshot_day: int = Field(ge=0, le=2000)
    enrollment_active: bool | None = None
    feature_data_confirmed: bool = False
    activity_complete: bool = False
    assessments_complete: bool = False
    assessments: list[AssessmentRecord] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_records(self):
        identifiers = [record.assessment_id for record in self.assessments]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Mỗi mã bài chỉ được xuất hiện một lần trong học phần/kỳ này.")
        if any(record.submitted_day is not None and record.submitted_day > self.snapshot_day
               for record in self.assessments):
            raise ValueError("Không được dùng bài nộp sau ngày quan sát.")
        return self


class SupportInput(BaseModel):
    model_config = {"extra": "forbid"}

    features: PredictionInput
    evidence: LearningEvidence
