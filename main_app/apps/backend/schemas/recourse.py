from typing import Any, Literal
from pydantic import BaseModel, Field
from schemas.prediction import StudentFeatures


class ActionableTargetItem(BaseModel):
    feature: str
    label: str
    current_value: float | str
    target_value: float | str
    delta: float
    unit: str
    importance_rank: int
    pedagogical_rationale: str


class SRLPhase(BaseModel):
    phase: Literal["forethought", "performance", "reflection"]
    phase_name: str
    timeframe: str
    objective: str
    action_items: list[str]
    stakeholder: Literal["student", "advisor", "collaborative"]


class RecourseScenario(BaseModel):
    id: Literal["quick_win", "sustainable"]
    title: str
    badge: str
    target_probability: float
    probability_reduction: float
    features: dict[str, Any]
    targets: list[ActionableTargetItem]
    srl_plan: list[SRLPhase]
    summary: str


class TheoreticalFoundations(BaseModel):
    frameworks: list[str]
    citations: list[str]
    limitations: list[str]


class ActionableRecourseResponse(BaseModel):
    status: Literal["available", "not_at_risk", "no_feasible_recourse"]
    message: str
    current_probability: float
    threshold: float
    scenarios: list[RecourseScenario] = Field(default_factory=list)
    theoretical_foundations: TheoreticalFoundations
