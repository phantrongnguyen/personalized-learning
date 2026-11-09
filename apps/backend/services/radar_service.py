"""Illustrative reference scores, never population percentiles or ability scores."""
import json
from math import floor, isfinite
from pathlib import Path
from typing import Any

RADAR_REFERENCE = json.loads((Path(__file__).resolve().parents[3] /
    "packages/shared/constants/radar-reference.json").read_text(encoding="utf-8"))


def _number(value):
    return type(value) in (int, float) and isfinite(value) and value >= 0


def calculate_radar_6d(snap_data: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions = []
    for spec in RADAR_REFERENCE["dimensions"]:
        key, reference = spec["key"], spec["reference"]
        value = snap_data.get(key)
        valid = _number(value)
        if key in ("active_day_ratio", "submission_rate"):
            valid = valid and value <= 1
        if key == "late_submissions_to_t":
            submitted = snap_data.get("assessments_submitted_to_t")
            valid = valid and _number(submitted) and submitted > 0 and value <= submitted
            # No submissions is not evidence of perfect submission discipline.
            value = max(0, 1 - value * RADAR_REFERENCE["late_submission_penalty"]) * 100 if valid else None
        if not valid:
            value = None
        score = floor(min(100, max(0, value / reference * 100)) * 10 + 0.5) / 10 if value is not None else None
        dimensions.append({"metric": spec["metric"], "student_value": value,
                           "benchmark_value": reference, "reference_score": score,
                           "unit": spec["unit"]})
    return dimensions


def snapshot_radar(snapshot, enrollment_id, code_module):
    keys = [spec["key"] for spec in RADAR_REFERENCE["dimensions"]] + ["assessments_submitted_to_t"]
    source = snapshot.raw_features_json
    return {
        "enrollment_id": enrollment_id, "code_module": code_module,
        "dimensions": calculate_radar_6d({key: getattr(snapshot, key, None) for key in keys}),
        "reference_version": RADAR_REFERENCE["version"], "reference_status": RADAR_REFERENCE["status"],
        "snapshot_id": snapshot.id, "cutoff_stage": snapshot.cutoff_stage,
        "recorded_at": snapshot.created_at,
        "data_source": source.get("data_source") if isinstance(source, dict) else None,
    }
