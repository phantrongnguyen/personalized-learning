"""Portable checks for the archived-score verifier; no OULAD data required."""
import copy
import json

import pandas as pd
import pytest

from reports.model_final import generate_charts


@pytest.fixture
def archived_fixture(tmp_path, monkeypatch):
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"frozen model")
    metadata = tmp_path / "model.json"
    metadata.write_text(json.dumps({
        "model_sha256": generate_charts.sha256(artifact),
        "data_sha256": "dataset-checksum", "cutoff_fraction": 0.75,
        "feature_columns": [f"feature_{index}" for index in range(17)],
    }), encoding="utf-8")
    monkeypatch.setattr(generate_charts, "ARTIFACT", artifact)
    monkeypatch.setattr(generate_charts, "METADATA", metadata)
    predictions = pd.DataFrame({
        "source_row_index": [1, 2, 3, 4], "risk": [0, 0, 1, 1],
        "p_risk": [0.1, 0.6, 0.4, 0.9], "prediction_at_0_5": [0, 1, 0, 1],
    })
    verification = {
        "model_refit_during_evaluation": False, "threshold_tuned_on_test": False,
        "input_hashes_unchanged": {
            "model": generate_charts.sha256(artifact),
            "metadata": generate_charts.sha256(metadata), "dataset": "dataset-checksum",
        },
        "metrics": {
            "threshold": 0.5, "cutoff_fraction": 0.75, "feature_count": 17,
            "test_rows": 4, "accuracy": 0.5, "precision_risk": 0.5,
            "recall_risk": 0.5, "f1_risk": 0.5, "weighted_f1": 0.5,
            "average_precision_risk": 5 / 6, "roc_auc": 0.75, "brier_score": 0.185,
            "tn": 1, "fp": 1, "fn": 1, "tp": 1, "alerts": 2, "actual_risk": 2,
        },
    }
    return predictions, verification, metadata


def test_verifies_archived_scores(archived_fixture):
    predictions, verification, _ = archived_fixture
    _, _, metrics = generate_charts.verify_scores(predictions, verification)
    assert (metrics["tn"], metrics["fp"], metrics["fn"], metrics["tp"]) == (1, 1, 1, 1)


@pytest.mark.parametrize("field, value", [
    ("threshold", 0.4), ("cutoff_fraction", 0.5), ("feature_count", 16), ("tp", 2),
])
def test_rejects_changed_protocol_or_counts(archived_fixture, field, value):
    predictions, verification, _ = archived_fixture
    altered = copy.deepcopy(verification)
    altered["metrics"][field] = value
    with pytest.raises(ValueError):
        generate_charts.verify_scores(predictions, altered)


@pytest.mark.parametrize("column, value", [
    ("p_risk", float("nan")), ("p_risk", 1.1),
    ("prediction_at_0_5", 1), ("source_row_index", 2),
])
def test_rejects_invalid_predictions(archived_fixture, column, value):
    predictions, verification, _ = archived_fixture
    altered = predictions.copy()
    altered.loc[0, column] = value
    with pytest.raises(ValueError):
        generate_charts.verify_scores(altered, verification)


def test_rejects_changed_metadata(archived_fixture):
    predictions, verification, metadata = archived_fixture
    metadata.write_text(metadata.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="metadata"):
        generate_charts.verify_scores(predictions, verification)