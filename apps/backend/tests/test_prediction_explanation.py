"""Verify local explanations against the shipped model, not fabricated examples."""
import math
from pathlib import Path

import pytest

from ml.explanation import explain_prediction
from ml.model_loader import load_model
from ml.predictor import predict
from schemas.prediction import StudentFeatures


ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts/model_hco_vnls_lightgbm_cutoff75.joblib"


@pytest.fixture(scope="module")
def artifact():
    return load_model(ARTIFACT)


@pytest.mark.parametrize("code_module,clicks,submitted", [
    ("AAA", 0, 0), ("CCC", 165, 3), ("GGG", 4200, 5),
])
def test_all_17_contributions_reconstruct_prediction(artifact, code_module, clicks, submitted):
    features = StudentFeatures(
        code_module=code_module, gender="M", highest_education="HE Qualification",
        age_band="0-35", studied_credits=60, date_registration=-10,
        total_clicks_to_t=clicks, clicks_resource_to_t=0, clicks_url_to_t=0,
        active_days_to_t=3, assessments_submitted_to_t=submitted,
        late_submissions_to_t=0, active_day_ratio=.15, submission_rate=.5,
        days_since_last_activity=4, clicks_recent_7=0, clicks_recent_30=2,
    ).model_dump()
    expected = predict(artifact, features)["confidence"]
    explanation = explain_prediction(artifact, features, expected)
    assert list(explanation["contributions"]) == artifact["feature_columns"]
    assert len(explanation["contributions"]) == 17
    margin = explanation["base_margin"] + sum(explanation["contributions"].values())
    assert 1 / (1 + math.exp(-margin)) == pytest.approx(expected, abs=1e-6)
    assert 0 <= explanation["base_probability"] <= 1


def test_mismatched_recorded_probability_is_rejected(artifact):
    features = StudentFeatures(
        code_module="AAA", gender="F", highest_education="HE Qualification",
        age_band="35-55", studied_credits=60, date_registration=-10,
        **{key: 0 for key in artifact["feature_columns"][6:]},
    ).model_dump()
    probability = predict(artifact, features)["confidence"]
    with pytest.raises(ValueError, match="recorded prediction"):
        explain_prediction(artifact, features, min(probability + .01, .99999))
