from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def prepare_categories(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    prepared = frame.copy()
    for column in columns:
        prepared[column] = prepared[column].fillna("THIEU").astype(str)
    return prepared


def load_baseline(path: str | Path) -> dict:
    model_path = Path(path)
    metadata = json.loads(model_path.with_suffix(".json").read_text(encoding="utf-8"))
    if sha256(model_path) != metadata["artifact_sha256"]:
        raise ValueError(f"Model checksum mismatch: {model_path.name}")
    for name, expected in metadata["artifact_versions"].items():
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise RuntimeError(f"Use the recorded environment: {name} {expected}, found {actual}")
    artifact = joblib.load(model_path)
    if artifact["schema_version"] != 1:
        raise ValueError("Unsupported baseline artifact schema")
    if artifact["feature_columns"] != metadata["feature_columns"]:
        raise ValueError("Artifact feature order differs from metadata")
    if artifact["threshold"] != metadata["threshold"]:
        raise ValueError("Artifact threshold differs from metadata")
    for field in ("model_family", "cutoff", "method", "categorical_columns"):
        if artifact[field] != metadata[field]:
            raise ValueError(f"Artifact {field} differs from metadata")
    return artifact


def predict_risk(artifact: dict, frame: pd.DataFrame) -> np.ndarray:
    columns = artifact["feature_columns"]
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing input features: {missing}")
    selected = frame[columns]
    if artifact["model_family"] == "CatBoost":
        selected = prepare_categories(selected, artifact["categorical_columns"])
        estimator = artifact["model"]
    elif artifact["model_family"] in ("XGBoost", "LightGBM"):
        estimator = artifact["pipeline"]
    else:
        raise ValueError("Unsupported baseline model family")
    positive_index = list(estimator.classes_).index(1)
    return np.asarray(estimator.predict_proba(selected)[:, positive_index])
