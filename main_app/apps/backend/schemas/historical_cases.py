from typing import Literal

from pydantic import BaseModel, Field

from schemas.prediction import StudentFeatures


class HistoricalCasesRequest(BaseModel):
    features: StudentFeatures
    cutoff_fraction: Literal[0.75]


class MatchedFeature(BaseModel):
    feature: str
    current_value: float
    historical_value: float
    current_contribution: float
    historical_contribution: float


class HistoricalSnapshot(BaseModel):
    fraction: float
    day: int
    recent_active_days: int
    recent_clicks: int
    due_assessments: int
    due_assessments_submitted: int
    due_submission_rate: float | None


class HistoricalCase(BaseModel):
    case_id: str
    module: str
    presentation: str
    risk_probability: float
    final_result: Literal["Pass", "Distinction"]
    distance: float
    matching_features: list[MatchedFeature]
    snapshots: list[HistoricalSnapshot]


class HistoricalCasesResponse(BaseModel):
    status: Literal["available", "unavailable", "no_matches", "no_recoveries", "not_at_risk"]
    message: str
    source: str = "OULAD · thư viện tham chiếu cục bộ"
    cutoff_fraction: float = 0.75
    threshold: float | None = None
    current_probability: float | None = None
    reference_count: int = 0
    eligible_count: int = 0
    neighborhood_count: int = 0
    successful_count: int = 0
    unsuccessful_count: int = 0
    risk_drivers: list[str] = Field(default_factory=list)
    cases: list[HistoricalCase] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
