from copy import deepcopy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.support import SupportInput
from app.services.support import assessment_evidence, demo_cases, recommend
from test_prediction import EXAMPLE

client = TestClient(app)


def payload():
    return {
        "features": {**EXAMPLE, "assessments_due_to_t": 2, "assessments_submitted_to_t": 2},
        "evidence": {
            "snapshot_day": 196, "enrollment_active": True, "feature_data_confirmed": False,
            "activity_complete": True, "assessments_complete": True,
            "assessments": [
                {"assessment_id": "A", "due_day": 100, "submitted_day": 110},
                {"assessment_id": "B", "due_day": 170, "submitted_day": None},
                {"assessment_id": "C", "due_day": 220, "submitted_day": 190},
            ],
        },
    }


def test_early_future_submission_does_not_cancel_missing_due_assignment():
    response = client.post("/api/v1/support", json=payload())
    assert response.status_code == 200
    output = response.json()
    assert output["assessment_summary"]["missing_ids"] == ["B"]
    assert output["assessment_summary"]["completed_due"] == 1
    assert output["assessment_summary"]["early_future"] == 1
    assert [item["rule_id"] for item in output["suggestions"]] == ["G01", "G02"]
    assert output["prediction"] is None


def test_low_risk_does_not_suppress_evidence_based_suggestions():
    request = payload()
    request["evidence"]["feature_data_confirmed"] = True
    with patch("app.services.support.predict", return_value={"probability_risk": .01}) as predictor:
        response = client.post("/api/v1/support", json=request)
    assert response.status_code == 200
    assert response.json()["suggestions"][0]["rule_id"] == "G01"
    predictor.assert_called_once()


@pytest.mark.parametrize("active", [False, None])
def test_inactive_or_unconfirmed_enrollment_abstains(active):
    request = payload()
    request["evidence"]["enrollment_active"] = active
    request["evidence"]["feature_data_confirmed"] = True
    with patch("app.services.support.predict") as predictor:
        output = client.post("/api/v1/support", json=request).json()
    assert output["status"] == "abstained"
    assert output["prediction"] is None
    predictor.assert_not_called()


def test_incomplete_sources_do_not_generate_specific_advice():
    request = payload()
    request["evidence"].update(activity_complete=False, assessments_complete=False)
    output = client.post("/api/v1/support", json=request).json()
    assert output["suggestions"] == []
    assert output["assessment_summary"] is None
    assert len(output["warnings"]) >= 3


@pytest.mark.parametrize("recent30,expected", [(53, "G03"), (0, "G04")])
def test_activity_rules_are_mutually_exclusive(recent30, expected):
    request = payload()
    request["features"].update(clicks_recent_7=0, clicks_recent_30=recent30, last_activity_day=150 if recent30 == 0 else 180)
    output = client.post("/api/v1/support", json=request).json()
    rules = [item["rule_id"] for item in output["suggestions"]]
    assert expected in rules
    assert not ({"G03", "G04"} <= set(rules))


def test_no_history_is_not_called_inactivity():
    request = payload()
    request["features"].update(total_clicks_to_t=0, clicks_resource_to_t=0, clicks_url_to_t=0,
                               active_days_to_t=0, last_activity_day=None, clicks_recent_7=0, clicks_recent_30=0)
    request["evidence"]["assessments_complete"] = False
    output = client.post("/api/v1/support", json=request).json()
    assert not output["suggestions"]
    assert any("lịch sử" in text for text in output["warnings"])


def test_banked_and_exempt_assignments_do_not_generate_incorrect_nudges():
    request = payload()
    request["evidence"]["assessments"][0]["is_banked"] = True
    request["evidence"]["assessments"][1]["is_exempt"] = True
    evidence = SupportInput.model_validate(request)
    assert assessment_evidence(evidence.evidence)["missing"] == 0
    assert assessment_evidence(evidence.evidence)["late"] == 0
    assert not recommend(evidence)["suggestions"]


def test_unknown_deadline_is_not_assigned_a_fake_due_date():
    request = payload()
    request["evidence"]["assessments"].append({"assessment_id": "Exam", "due_day": None})
    output = client.post("/api/v1/support", json=request).json()
    assert output["assessment_summary"]["unknown_deadlines"] == 1
    assert output["assessment_summary"]["missing_ids"] == ["B"]


@pytest.mark.parametrize("mutation", [
    lambda request: request["evidence"].update(snapshot_day=130),
    lambda request: request["evidence"]["assessments"][0].update(submitted_day=197),
    lambda request: request["evidence"]["assessments"].append({"assessment_id": "A", "due_day": 100}),
    lambda request: request["features"].update(assessments_due_to_t=3),
    lambda request: request["features"].update(date_registration=197),
    lambda request: request["features"].update(last_activity_day=189),
    lambda request: request["features"].update(final_result="Pass"),
    lambda request: request["evidence"]["assessments"][1].update(is_banked=True),
])
def test_rejects_inconsistent_future_or_leaking_input(mutation):
    request = payload()
    mutation(request)
    assert client.post("/api/v1/support", json=request).status_code == 422


@pytest.mark.parametrize("age,recent7,expected_status", [(6, 1, 200), (7, 0, 200), (7, 1, 422), (29, 0, 200), (30, 0, 422)])
def test_window_boundaries(age, recent7, expected_status):
    request = payload()
    request["features"].update(last_activity_day=196-age, clicks_recent_7=recent7)
    assert client.post("/api/v1/support", json=request).status_code == expected_status


def test_no_due_assignments_does_not_become_a_zero_completion_warning():
    request = payload()
    request["features"].update(assessments_due_to_t=0, assessments_submitted_to_t=0, late_submissions_to_t=0)
    request["evidence"]["assessments"] = [{"assessment_id": "future", "due_day": 220}]
    output = client.post("/api/v1/support", json=request).json()
    assert output["assessment_summary"]["missing"] == 0
    assert not output["suggestions"]


def test_pre_course_activity_preserves_historical_feature_semantics():
    request = {**EXAMPLE, "last_activity_day": -1, "clicks_recent_7": 0, "clicks_recent_30": 0, "active_days_to_t": 200}
    response = client.post("/api/v1/predict", json=request)
    assert response.status_code == 200


def test_all_demo_cases_run_real_model_without_identifiers_or_labels():
    cases = demo_cases()
    assert len(cases) == 7
    for case in cases:
        assert not {"id_student", "risk", "final_result"} & case["payload"]["features"].keys()
        response = client.post("/api/v1/support/cases/" + case["id"])
        assert response.status_code == 200, response.text
        output = response.json()
        if case["source_kind"] == "synthetic_test":
            assert output["prediction"] is None
            assert output["status"] == "abstained"
        else:
            assert 0 <= output["prediction"]["probability_risk"] <= 1
    assert client.post("/api/v1/support/cases/unknown").status_code == 404


def test_recommendations_are_deterministic_and_do_not_mutate_payload():
    request = SupportInput.model_validate(payload())
    original = deepcopy(request.model_dump())
    assert recommend(request) == recommend(request)
    assert request.model_dump() == original


@pytest.mark.parametrize("changes", [
    {"last_activity_day": None},
    {"active_days_to_t": 0},
    {"total_clicks_to_t": 0, "clicks_resource_to_t": 0, "clicks_url_to_t": 0, "clicks_recent_7": 0, "clicks_recent_30": 0},
])
def test_missing_activity_is_not_silently_turned_into_imputed_evidence(changes):
    request = payload()
    request["features"].update(changes)
    assert client.post("/api/v1/support", json=request).status_code == 422


def test_optional_registration_date_and_true_no_history_still_predict():
    request = {**EXAMPLE, "date_registration": None, "total_clicks_to_t": 0,
               "clicks_resource_to_t": 0, "clicks_url_to_t": 0, "clicks_recent_7": 0,
               "clicks_recent_30": 0, "active_days_to_t": 0, "last_activity_day": None}
    response = client.post("/api/v1/predict", json=request)
    assert response.status_code == 200
    assert 0 <= response.json()["probability_risk"] <= 1
