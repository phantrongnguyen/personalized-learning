"""Replay only from recorded inputs and the checksum-addressed artifact."""
import math
import hashlib
from pathlib import Path

from ml.model_loader import load_model
from ml.predictor import predict
from schemas.prediction import PredictionProvenance


def replay_prediction(run, archive_dir=None):
    if run.inference_context is None:
        raise ValueError("Legacy prediction has no verified inference context")
    context = PredictionProvenance(**run.inference_context)
    archive_dir = archive_dir or Path(__file__).resolve().parents[1] / "artifacts/archive"
    path = archive_dir / f"{context.model_sha256}.joblib"
    if hashlib.sha256(path.read_bytes()).hexdigest() != context.model_sha256:
        raise ValueError("Replay artifact checksum mismatch")
    artifact = load_model(path, archive_dir=archive_dir)
    if artifact["_provenance"]["model_sha256"] != context.model_sha256:
        raise ValueError("Replay artifact checksum mismatch")
    if artifact["threshold"] != context.threshold:
        raise ValueError("Replay threshold mismatch")
    result = predict(artifact, context.features.model_dump())
    return {
        **result,
        "matches_original": result["prediction"] == run.prediction_label and math.isclose(
            result["confidence"], run.risk_probability, rel_tol=0, abs_tol=1e-12),
        "model_version": context.model_version,
        "model_sha256": context.model_sha256,
    }
