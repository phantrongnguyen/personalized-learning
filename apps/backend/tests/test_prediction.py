from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXAMPLE = {
    "code_module": "BBB", "code_presentation": "2014J", "gender": "F",
    "highest_education": "A Level or Equivalent", "age_band": "0-35",
    "studied_credits": 60, "date_registration": -53,
    "total_clicks_to_t": 807, "clicks_resource_to_t": 23,
    "clicks_url_to_t": 9, "active_days_to_t": 52,
    "assessments_due_to_t": 5, "assessments_submitted_to_t": 5,
    "late_submissions_to_t": 1, "last_activity_day": 194,
    "clicks_recent_7": 2, "clicks_recent_30": 53,
}


def test_catalog_uses_course_duration_for_cutoff():
    response = client.get("/api/v1/catalog")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) == 22
    course = next(item for item in courses if item["code_module"] == "BBB"
                  and item["code_presentation"] == "2014J")
    assert course["module_presentation_length"] == 262
    assert course["cutoff_day"] == 196


def test_real_artifact_returns_a_valid_probability():
    info = client.get("/api/v1/model").json()
    assert info["feature_count"] == 17
    response = client.post("/api/v1/predict", json=EXAMPLE)
    assert response.status_code == 200
    result = response.json()
    assert 0 <= result["probability_risk"] <= 1
    assert result["above_threshold"] == (result["probability_risk"] >= .5)
    assert result["cutoff_day"] == 196
    assert result["feature_count"] == 17


def test_rejects_future_activity_and_impossible_click_counts():
    future = {**EXAMPLE, "last_activity_day": 197}
    assert client.post("/api/v1/predict", json=future).status_code == 422
    impossible = {**EXAMPLE, "clicks_recent_7": 54}
    assert client.post("/api/v1/predict", json=impossible).status_code == 422


def test_rejects_unknown_course_and_extra_fields():
    unknown = {**EXAMPLE, "code_presentation": "2099J"}
    assert client.post("/api/v1/predict", json=unknown).status_code == 422
    with_student_id = {**EXAMPLE, "id_student": 12345}
    assert client.post("/api/v1/predict", json=with_student_id).status_code == 422
