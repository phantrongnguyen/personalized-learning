from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PredictionInput(BaseModel):
    model_config = {"extra": "forbid"}

    code_module: str = Field(min_length=3, max_length=3)
    code_presentation: str = Field(min_length=5, max_length=5)
    gender: Literal["F", "M"]
    highest_education: Literal[
        "HE Qualification", "Lower Than A Level", "A Level or Equivalent",
        "Post Graduate Qualification", "No Formal quals",
    ]
    age_band: Literal["0-35", "35-55", "55<="]
    studied_credits: float = Field(ge=0, le=1000)
    date_registration: float | None = Field(default=None, ge=-1000, le=1000)
    total_clicks_to_t: int = Field(ge=0)
    clicks_resource_to_t: int = Field(ge=0)
    clicks_url_to_t: int = Field(ge=0)
    active_days_to_t: int = Field(ge=0, le=5000)
    assessments_due_to_t: int = Field(ge=0)
    assessments_submitted_to_t: int = Field(ge=0)
    late_submissions_to_t: int = Field(ge=0)
    last_activity_day: int | None = Field(default=None, ge=-1000)
    clicks_recent_7: int = Field(ge=0)
    clicks_recent_30: int = Field(ge=0)

    @model_validator(mode="after")
    def check_counts(self):
        if self.total_clicks_to_t > 0 and (self.last_activity_day is None or self.active_days_to_t == 0):
            raise ValueError("Đã có click thì cần số ngày hoạt động và ngày cuối để giữ đúng định nghĩa đặc trưng.")
        if self.total_clicks_to_t == 0 and (self.active_days_to_t != 0 or self.last_activity_day is not None):
            raise ValueError("Không có lịch sử click thì số ngày hoạt động phải bằng 0 và ngày cuối để trống.")
        if self.clicks_recent_7 > self.clicks_recent_30 or self.clicks_recent_30 > self.total_clicks_to_t:
            raise ValueError("Click 7 ngày ≤ click 30 ngày ≤ tổng click đến cutoff.")
        if self.clicks_resource_to_t + self.clicks_url_to_t > self.total_clicks_to_t:
            raise ValueError("Click theo loại không thể vượt tổng click.")
        if self.late_submissions_to_t > self.assessments_submitted_to_t:
            raise ValueError("Số bài nộp trễ không thể vượt số bài đã nộp.")
        return self
