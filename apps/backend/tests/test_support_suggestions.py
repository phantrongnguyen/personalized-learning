"""The rule layer never infers assignment-level facts from aggregate features."""
from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from services.support_suggestions import evaluate_suggestions, OULAD_SOURCES, validated_assessment_details
from services.support_evidence import REVIEW_VERSION, snapshot_digest


def fixture(**overrides):
    metadata = {"review_version": REVIEW_VERSION, "review_scope": "source_verified",
                "confirmed_by_user_id": str(uuid4()), "snapshot_day": 75, "source": "verified-import", "confirmed_at": "2026-01-01T00:00:00+00:00",
                "activity_complete": True, "assessments_complete": True}
    metadata.update(overrides.pop("metadata", {}))
    snapshot = SimpleNamespace(id=uuid4(), enrollment_id=uuid4(), clicks_resource_to_t=4, clicks_url_to_t=2, active_days_to_t=3, active_day_ratio=.04, cutoff_stage="CUTOFF_75", raw_features_json={"support_evidence": metadata},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc), total_clicks_to_t=12, clicks_recent_7=0,
        clicks_recent_30=4, days_since_last_activity=7, late_submissions_to_t=1, assessments_submitted_to_t=4, submission_rate=.8)
    for key, value in overrides.items():
        setattr(snapshot, key, value)
    presentation = SimpleNamespace(id=uuid4(), start_date=date(2025, 1, 1), module_presentation_length=100)
    metadata["snapshot_sha256"] = snapshot_digest(snapshot, presentation)
    return snapshot, presentation


def test_complete_evidence_yields_aggregate_and_cutoff_activity_only():
    state, suggestions, warnings, cutoff = evaluate_suggestions(*fixture(), today=date(2026, 2, 1))
    assert state == "available"
    assert [item["rule_id"] for item in suggestions] == ["G02_AGGREGATE", "G03"]
    assert cutoff == date(2025, 3, 17)
    assert all(item["rule_version"] and item["evidence"]["snapshot_id"] for item in suggestions)
    assert not any(item["rule_id"] == "G01" for item in suggestions)
    assert any("không xác định" in text for text in warnings)


def test_missing_or_unconfirmed_metadata_abstains():
    for change in ({"raw_features_json": None}, {"raw_features_json": ["invalid"]},
                   {"metadata": {"snapshot_day": 74}},
                   {"metadata": {"activity_complete": False, "assessments_complete": False}},
                   {"metadata": {"source": ""}}):
        state, suggestions, _, _ = evaluate_suggestions(*fixture(**change), today=date(2026, 2, 1))
        assert state == "insufficient_data" and not suggestions


def test_stale_snapshot_and_no_current_activity_claim():
    snapshot, presentation = fixture(clicks_recent_30=0, days_since_last_activity=30, late_submissions_to_t=0)
    state, suggestions, warnings, _ = evaluate_suggestions(snapshot, presentation, today=date(2026, 2, 1))
    assert state == "available" and [item["rule_id"] for item in suggestions] == ["G04"]
    assert "cutoff" in suggestions[0]["observation"]
    assert any("không phản ánh hoạt động hiện tại" in item for item in warnings)
    snapshot.raw_features_json["support_evidence"]["snapshot_day"] = 74
    assert evaluate_suggestions(snapshot, presentation)[0] == "insufficient_data"


def test_window_boundaries_and_inconsistent_counts():
    for age, expected in ((6, "abstained"), (7, "available")):
        snapshot, presentation = fixture(late_submissions_to_t=0, days_since_last_activity=age)
        state, suggestions, _, _ = evaluate_suggestions(snapshot, presentation, today=date(2026, 2, 1))
        assert state == expected
        if suggestions:
            assert suggestions[0]["rule_id"] == "G03"
    snapshot, presentation = fixture(late_submissions_to_t=0, clicks_recent_7=5, clicks_recent_30=4)
    assert evaluate_suggestions(snapshot, presentation)[1] == []


def test_incomplete_log_never_yields_activity_rule():
    snapshot, presentation = fixture(metadata={"activity_complete": False}, late_submissions_to_t=0)
    state, suggestions, _, _ = evaluate_suggestions(snapshot, presentation)
    assert state == "abstained" and not suggestions


def test_thirty_day_and_aggregate_boundaries():
    for age, expected in ((29, "abstained"), (30, "G04")):
        snapshot, presentation = fixture(clicks_recent_30=0, days_since_last_activity=age,
                                         late_submissions_to_t=0)
        state, suggestions, _, _ = evaluate_suggestions(snapshot, presentation, today=date(2026, 2, 1))
        assert [item["rule_id"] for item in suggestions] == ([] if expected == "abstained" else [expected])
        assert state == ("abstained" if age == 29 else "available")
    snapshot, presentation = fixture(late_submissions_to_t=5)
    assert [item["rule_id"] for item in evaluate_suggestions(snapshot, presentation)[1]] == ["G03"]
    snapshot, presentation = fixture(late_submissions_to_t=0)
    assert [item["rule_id"] for item in evaluate_suggestions(snapshot, presentation)[1]] == ["G03"]


async def test_read_endpoint_never_mutates(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from api.v1.endpoints import lecturer
    student_id, presentation_id, enrollment_id = uuid4(), uuid4(), uuid4()
    scalar = lambda value: SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: value),
                                           scalar_one_or_none=lambda: value)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[scalar(SimpleNamespace(id=enrollment_id)),
                                                      scalar(None), scalar(None)]),
                         get=AsyncMock(return_value=SimpleNamespace(module_presentation_length=100)),
                         add=MagicMock(), commit=AsyncMock(), flush=AsyncMock())
    owner = AsyncMock()
    monkeypatch.setattr(lecturer, "_ensure_course_ownership", owner)
    response = await lecturer.get_course_student_suggestions(
        presentation_id, student_id, SimpleNamespace(id=uuid4()), db)
    assert response["status"] == "insufficient_data"
    assert response["prediction"] is None
    assert response["assignment"]["can_assign"] is False
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.flush.assert_not_awaited()
    owner.assert_awaited_once()


def test_confirmation_before_cutoff_is_insufficient():
    snapshot, presentation = fixture(metadata={"confirmed_at": "2025-01-02T00:00:00+00:00"})
    state, suggestions, _, _ = evaluate_suggestions(snapshot, presentation)
    assert state == "insufficient_data" and suggestions == []


def test_relative_oulad_details_show_missing_without_inventing_calendar_or_topic():
    snapshot, presentation = fixture(metadata={
        "timeline": "relative_course_day", "source": "OULAD processed Parquet",
        "source_sha256": {name: "a" * 64 for name in OULAD_SOURCES}, "assessment_records": [
            {"id": 101, "type": "TMA", "due_day": 19, "submitted_day": 18, "score": 70},
            {"id": 102, "type": "TMA", "due_day": 54, "submitted_day": None, "score": None},
            {"id": 103, "type": "TMA", "due_day": 70, "submitted_day": None, "score": None},
            {"id": 104, "type": "TMA", "due_day": 72, "submitted_day": None, "score": None},
        ]}, late_submissions_to_t=0, assessments_submitted_to_t=1, submission_rate=.25)
    presentation.start_date = None
    snapshot.raw_features_json["support_evidence"]["snapshot_sha256"] = snapshot_digest(snapshot, presentation)
    state, suggestions, warnings, cutoff_date = evaluate_suggestions(snapshot, presentation)
    assert state == "available" and cutoff_date is None
    assert [item["rule_id"] for item in suggestions] == ["G01", "G03"]
    assert "3/4" in suggestions[0]["observation"]
    assert "chủ đề" in suggestions[0]["limitation"]
    assert "cutoff_date" not in suggestions[0]["evidence"]
    assert any("OULAD" in warning for warning in warnings)


def test_inconsistent_assessment_detail_never_claims_missing_assignment():
    snapshot, presentation = fixture(metadata={"assessment_records": [
        {"id": 101, "type": "TMA", "due_day": 19, "submitted_day": None, "score": None},
    ]})
    _, suggestions, warnings, _ = evaluate_suggestions(snapshot, presentation)
    assert all(item["rule_id"] != "G01" for item in suggestions)
    assert any("đối chiếu" in warning for warning in warnings)


def test_assessment_records_require_explicit_submission_state():
    valid_records = [
        {"id": 101, "type": "TMA", "due_day": 19, "submitted_day": 18, "score": 70},
        {"id": 102, "type": "TMA", "due_day": 54, "submitted_day": None, "score": None},
    ]
    snapshot, presentation = fixture(metadata={"assessment_records": valid_records},
        late_submissions_to_t=0, assessments_submitted_to_t=1, submission_rate=.5)
    state, suggestions, _, _ = evaluate_suggestions(snapshot, presentation)
    assert state == "available" and any(item["rule_id"] == "G01" for item in suggestions)

    invalid_records = [
        {"id": 102, "type": "TMA", "due_day": 54, "score": None},
        {**valid_records[1], "submitted_day": ""},
        {**valid_records[1], "submitted_day": True},
        {**valid_records[1], "submitted_day": 76},
        {**valid_records[1], "score": 50},
        {**valid_records[1], "id": 101},
    ]
    for invalid in invalid_records:
        snapshot.raw_features_json["support_evidence"]["assessment_records"] = [valid_records[0], invalid]
        _, suggestions, warnings, _ = evaluate_suggestions(snapshot, presentation)
        assert all(item["rule_id"] != "G01" for item in suggestions)
        assert any("không xác định được bài nào" in warning for warning in warnings)

    snapshot.raw_features_json["support_evidence"]["assessment_records"] = valid_records
    for rate in (None, True, float("nan"), 1.5):
        snapshot.submission_rate = rate
        assert validated_assessment_details(snapshot, snapshot.raw_features_json["support_evidence"], 75) is None



def test_unverified_relative_source_cannot_be_labeled_historical():
    snapshot, presentation = fixture(metadata={"timeline": "relative_course_day"})
    presentation.start_date = None
    snapshot.raw_features_json["support_evidence"]["snapshot_sha256"] = snapshot_digest(snapshot, presentation)
    state, suggestions, warnings, _ = evaluate_suggestions(snapshot, presentation)
    assert state == "insufficient_data" and not suggestions
    assert any("nguồn" in item.lower() for item in warnings)


async def test_historical_endpoint_returns_verified_details_and_plan_without_writing(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock
    from api.v1.endpoints import lecturer

    student_id, presentation_id, enrollment_id, plan_id = uuid4(), uuid4(), uuid4(), uuid4()
    records = [
        {"id": 101, "type": "TMA", "due_day": 19, "submitted_day": 18, "score": 70},
        {"id": 102, "type": "TMA", "due_day": 54, "submitted_day": None, "score": None},
        {"id": 103, "type": "TMA", "due_day": 70, "submitted_day": None, "score": None},
        {"id": 104, "type": "TMA", "due_day": 72, "submitted_day": None, "score": None},
    ]
    snapshot, presentation = fixture(metadata={
        "timeline": "relative_course_day", "source": "OULAD processed Parquet",
        "source_sha256": {name: "a" * 64 for name in OULAD_SOURCES},
        "assessment_records": records,
    }, late_submissions_to_t=0, assessments_submitted_to_t=1, submission_rate=.25)
    presentation.start_date = None
    snapshot.raw_features_json["support_evidence"]["snapshot_sha256"] = snapshot_digest(snapshot, presentation)
    enrollment = SimpleNamespace(id=enrollment_id)
    run = SimpleNamespace(id=uuid4(), risk_probability=.989, prediction_label=1,
                          created_at=snapshot.created_at)
    model = SimpleNamespace(id=uuid4(), threshold=.5, version="test", cutoff_fraction=.75)
    scalar = lambda value: SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: value),
                                           scalar_one_or_none=lambda: value)
    db = SimpleNamespace(execute=AsyncMock(side_effect=[scalar(enrollment), scalar(snapshot),
                                                         SimpleNamespace(first=lambda: (run, model)), scalar(plan_id)]),
                         get=AsyncMock(return_value=presentation), add=MagicMock(),
                         commit=AsyncMock(), flush=AsyncMock())
    owner = AsyncMock()
    monkeypatch.setattr(lecturer, "_ensure_course_ownership", owner)
    response = await lecturer.get_course_student_suggestions(
        presentation_id, student_id, SimpleNamespace(id=uuid4()), db)
    assert response["status"] == "available"
    assert response["source_kind"] == "historical_oulad" and response["cutoff_date"] is None
    assert response["assessment_details"] == records and response["cutoff_day"] == 75
    assert response["assignment"] == {"can_assign": True, "plan_id": plan_id,
        "message": "Có plan ACTIVE đúng học phần; giảng viên quyết định và bấm giao."}
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    db.flush.assert_not_awaited()
    owner.assert_awaited_once()
