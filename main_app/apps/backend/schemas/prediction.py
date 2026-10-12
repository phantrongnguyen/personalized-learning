from typing import Any, Literal

from pydantic import BaseModel, Field


class StudentFeatures(BaseModel):
    """Đặc trưng đầu vào theo đúng thứ tự và tên cột khi huấn luyện model."""

    code_module: str = Field(examples=["AAA"])
    gender: str = Field(examples=["M"])
    highest_education: str = Field(examples=["A Level or Equivalent"])
    age_band: str = Field(examples=["18-23"])
    studied_credits: float = Field(examples=[60.0])
    date_registration: float = Field(examples=[-10.0])
    total_clicks_to_t: float = Field(examples=[1500.0])
    clicks_resource_to_t: float = Field(examples=[400.0])
    clicks_url_to_t: float = Field(examples=[200.0])
    active_days_to_t: float = Field(examples=[45.0])
    assessments_submitted_to_t: float = Field(examples=[5.0])
    late_submissions_to_t: float = Field(examples=[1.0])
    active_day_ratio: float = Field(examples=[0.5])
    submission_rate: float = Field(examples=[0.6])
    days_since_last_activity: float = Field(examples=[3.0])
    clicks_recent_7: float = Field(examples=[80.0])
    clicks_recent_30: float = Field(examples=[350.0])


class PredictionRequest(BaseModel):
    features: StudentFeatures


class FeatureContribution(BaseModel):
    feature: str
    value: str | float
    contribution: float
    direction: Literal["increase", "decrease", "neutral"]


class PredictionExplanation(BaseModel):
    method: str
    unit: Literal["log_odds"]
    baseline_raw_score: float
    baseline_probability: float
    raw_score: float
    reconstructed_probability: float
    contributions: list[FeatureContribution]


class PredictionResponse(BaseModel):
    prediction: Any
    confidence: float | None = None
    threshold: float | None = None
    explanation: PredictionExplanation | None = None
