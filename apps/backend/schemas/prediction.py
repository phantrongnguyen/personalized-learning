from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field

Count = Annotated[int, Field(ge=0)]
Ratio = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
RiskLevel = Literal["SAFE", "HIGH_RISK", "NOT_PREDICTED"]


class BehaviorFeatures(BaseModel):
    """Numeric observation contract shared by snapshot updates and inference."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    total_clicks_to_t: Count
    clicks_resource_to_t: Count
    clicks_url_to_t: Count
    active_days_to_t: Count
    assessments_submitted_to_t: Count
    late_submissions_to_t: Count
    active_day_ratio: Ratio
    submission_rate: Ratio
    days_since_last_activity: Count
    clicks_recent_7: Count
    clicks_recent_30: Count


class StudentFeatures(BehaviorFeatures):
    """Shared contract for manual and database inference at cutoff 75%."""
    code_module: Literal["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"]
    gender: Literal["M", "F"]
    highest_education: Literal[
        "A Level or Equivalent", "HE Qualification", "Lower Than A Level",
        "No Formal quals", "Post Graduate Qualification",
    ]
    age_band: Literal["0-35", "35-55", "55<="]
    studied_credits: float = Field(gt=0)
    date_registration: int = Field(description="Days relative to course start; may be negative")


class PredictionProvenance(BaseModel):
    features: StudentFeatures
    model_version: str
    threshold: Ratio
    model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_id: uuid.UUID | None = None
    cutoff_fraction: Ratio | None = None
    positive_label: Literal[1] | None = None


class PredictionRequest(BaseModel):
    features: StudentFeatures


class PredictionResponse(BaseModel):
    prediction: Literal[0, 1]
    confidence: Ratio
    provenance: PredictionProvenance | None = None
