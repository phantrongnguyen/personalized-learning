from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from xgboost import XGBClassifier


RESEARCH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH_ROOT.parent))

from clht_code.evaluation import metric_table
from clht_code.models import ModelConfig, make_pipeline
from NghienCuu_HCO_VNLS.code_dung_chung.baseline_artifacts import (
    load_baseline, predict_risk, prepare_categories, sha256, source_sha256,
)


METHOD_SLUGS = {"Full features": "full_features", "HCO": "hco", "VNLS": "vnls", "HCO-VNLS": "hco_vnls"}
LIBRARIES = ("numpy", "pandas", "scikit-learn", "joblib", "xgboost", "catboost")


def assert_metrics(actual: dict, expected: dict) -> None:
    for name, value in actual.items():
        np.testing.assert_allclose(value, float(expected[name]), rtol=0, atol=1e-12, err_msg=name)


def run(output: Path, verify_only: bool) -> None:
    result_root = RESEARCH_ROOT / "ket_qua"
    protocols = {
        family: json.loads((result_root / f"giao_thuc_{family.lower()}_50_75.json").read_text(encoding="utf-8"))
        for family in ("CatBoost", "XGBoost")
    }
    records = pd.read_csv(result_root / "so_sanh_ba_bo_hoc_50_75.csv")
    records = records.loc[records["model"].isin(protocols)].copy()
    assert len(records) == 16
    assert not records.duplicated(["model", "cutoff", "method"]).any()
    expected_keys = {(family, cutoff, method) for family in protocols for cutoff in (0.5, 0.75) for method in METHOD_SLUGS}
    assert set(zip(records["model"], records["cutoff"], records["method"])) == expected_keys
    versions = {name: importlib.metadata.version(name) for name in LIBRARIES}
    for protocol in protocols.values():
        for name, expected in protocol["versions"].items():
            assert importlib.metadata.version(name) == expected, name
        assert protocol["threshold"] == 0.5 and not protocol["test_evaluated"]
    repo_root = RESEARCH_ROOT.parents[1]
    main_paths = [repo_root / "apps/backend/model_store" / name for name in (
        "model_hco_vnls_lightgbm_cutoff75.joblib", "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json",
    )]
    input_paths = [result_root / "so_sanh_ba_bo_hoc_50_75.csv", *main_paths]
    input_paths += [result_root / f"giao_thuc_{family.lower()}_50_75.json" for family in protocols]
    input_paths += [result_root / f"du_lieu_cutoff_{cutoff}.csv" for cutoff in (50, 75)]
    before = {str(path): sha256(path) for path in input_paths}
    source_hash = source_sha256(result_root / "so_sanh_ba_bo_hoc_50_75.csv")
    output.mkdir(parents=True, exist_ok=True)
    if not verify_only and list(output.glob("*.joblib")):
        raise FileExistsError("Output already contains models; use --verify-only or a new output directory")
    exported = []
    for cutoff in (0.5, 0.75):
        dataset_path = result_root / f"du_lieu_cutoff_{round(cutoff * 100)}.csv"
        data_hash = sha256(dataset_path)
        assert all(protocol["data_sha256"][str(cutoff)] == data_hash for protocol in protocols.values())
        frame = pd.read_csv(dataset_path)
        train = frame.loc[frame["split"].eq("train")].copy()
        validation = frame.loc[frame["split"].eq("validation")].copy()
        train_ids = set(train["id_student"])
        validation_ids = set(validation["id_student"])
        test_ids = set(frame.loc[frame["split"].eq("test"), "id_student"])
        assert not (train_ids & validation_ids or train_ids & test_ids or validation_ids & test_ids)
        for family in ("CatBoost", "XGBoost"):
            protocol = protocols[family]
            for method, method_slug in METHOD_SLUGS.items():
                row = records.loc[records["model"].eq(family) & records["cutoff"].eq(cutoff) & records["method"].eq(method)].iloc[0]
                columns = row["selected_columns"].split("|")
                assert len(columns) == row["features"] and len(columns) == len(set(columns))
                assert not set(columns) & {"risk", "final_result", "id_student", "split", "cutoff", "cutoff_mode", "score_policy", "progress_fraction", "module_presentation_length"}
                categorical = train[columns].select_dtypes(include=["object", "category", "bool"]).columns.tolist()
                name = f"{family.lower()}_cutoff{round(cutoff * 100)}_{method_slug}"
                artifact_path = output / f"{name}.joblib"
                native_path = output / f"{name}{'.cbm' if family == 'CatBoost' else '.ubj'}"
                metadata_path = artifact_path.with_suffix(".json")
                artifact = {
                    "schema_version": 1, "model_family": family, "cutoff": cutoff,
                    "method": method, "feature_columns": columns, "categorical_columns": categorical,
                    "threshold": 0.5, "training_policy": "Fit train only using the frozen notebook mask; validation is diagnostic; no test evaluation.",
                }
                if verify_only:
                    artifact = load_baseline(artifact_path)
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    assert artifact["model_family"] == family and artifact["cutoff"] == cutoff
                    assert artifact["method"] == method and artifact["feature_columns"] == columns
                    assert metadata["dataset_sha256"] == data_hash
                    assert metadata["source_results_sha256"] == source_hash
                    assert sha256(native_path) == metadata["native_sha256"]
                    fit_seconds = metadata["export_fit_seconds"]
                else:
                    started = time.perf_counter()
                    if family == "CatBoost":
                        model = CatBoostClassifier(**protocol["params"])
                        model.fit(prepare_categories(train[columns], categorical), train["risk"], cat_features=categorical)
                        artifact["model"] = model
                        encoded_features = len(columns)
                    else:
                        pipeline = make_pipeline(train[columns], ModelConfig("XGBoost", XGBClassifier(**protocol["params"])))
                        pipeline.fit(train[columns], train["risk"])
                        artifact["pipeline"] = pipeline
                        encoded_features = len(pipeline.named_steps["preprocess"].get_feature_names_out())
                    fit_seconds = time.perf_counter() - started
                    assert encoded_features == row["encoded_features"]
                probabilities = predict_risk(artifact, validation)
                actual_metrics = metric_table(validation["risk"], probabilities, artifact["threshold"])
                assert_metrics(actual_metrics, row.to_dict())
                if not verify_only:
                    joblib.dump(artifact, artifact_path, compress=3)
                    estimator = artifact["model"] if family == "CatBoost" else artifact["pipeline"].named_steps["model"]
                    estimator.save_model(str(native_path))
                    metadata = {
                        "schema_version": 1, "created_on": "2026-10-09", "model_family": family,
                        "cutoff": cutoff, "method": method, "feature_columns": columns,
                        "categorical_columns": categorical, "encoded_features": int(row["encoded_features"]),
                        "threshold": 0.5, "training_rows": len(train), "validation_rows": len(validation),
                        "training_policy": artifact["training_policy"], "search_rerun": False,
                        "test_evaluated": False, "production_model_changed": False,
                        "python": platform.python_version(), "artifact_versions": versions,
                        "params": protocol["params"], "dataset_sha256": data_hash,
                        "source_results_sha256": source_hash,
                        "source_results_hash_policy": "LF-normalized text; model and dataset hashes use exact bytes",
                        "artifact_sha256": sha256(artifact_path), "native_file": native_path.name,
                        "native_sha256": sha256(native_path), "export_fit_seconds": fit_seconds,
                        "historical_search_seconds": float(row["search_seconds"]),
                        "historical_fit_seconds": float(row["fit_seconds"]),
                        "historical_predict_seconds": float(row["predict_seconds"]),
                        "metrics_validation": actual_metrics,
                    }
                    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                loaded = load_baseline(artifact_path)
                np.testing.assert_allclose(predict_risk(loaded, validation), probabilities, rtol=0, atol=1e-12)
                if family == "CatBoost":
                    native = CatBoostClassifier()
                    native.load_model(str(native_path))
                    native_probabilities = native.predict_proba(prepare_categories(validation[columns], categorical))[:, list(native.classes_).index(1)]
                else:
                    native = XGBClassifier()
                    native.load_model(str(native_path))
                    transformed = loaded["pipeline"].named_steps["preprocess"].transform(validation[columns])
                    native_probabilities = native.predict_proba(transformed)[:, list(native.classes_).index(1)]
                np.testing.assert_allclose(native_probabilities, probabilities, rtol=0, atol=1e-12)
                exported.append({
                    "model": family, "cutoff": cutoff, "method": method, "features": len(columns),
                    "encoded_features": int(row["encoded_features"]), "model_file": artifact_path.name,
                    "native_file": native_path.name, "model_sha256": sha256(artifact_path),
                    "native_sha256": sha256(native_path), "bytes": artifact_path.stat().st_size,
                    "export_fit_seconds": fit_seconds, "historical_search_seconds": float(row["search_seconds"]),
                    "historical_fit_seconds": float(row["fit_seconds"]),
                    "historical_predict_seconds": float(row["predict_seconds"]),
                    "verified_against_notebook": True, "reload_verified": True, "native_reload_verified": True,
                    **actual_metrics,
                })
                print(f"PASS {len(exported):02d}/16 {name}: AP={actual_metrics['average_precision_risk']:.12f}, {artifact_path.stat().st_size:,} bytes", flush=True)
    assert before == {str(path): sha256(path) for path in input_paths}, "Source or production artifacts changed"
    if not verify_only:
        pd.DataFrame(exported).to_csv(output / "DANH_SACH_16_MODEL.csv", index=False, encoding="utf-8-sig")
        (output / "KIEM_CHUNG.json").write_text(json.dumps({
            "model_count": len(exported), "evaluated_on_test": False, "search_rerun": False,
            "input_hashes_unchanged": {Path(path).relative_to(repo_root).as_posix(): digest for path, digest in before.items()}, "max_metric_tolerance": 1e-12,
            "checks": ["all historical validation metrics", "joblib reload predictions", "native reload predictions", "disjoint student groups", "frozen mask order", "production model unchanged"],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path = output / "manifest_sha256.csv"
    if verify_only:
        for entry in pd.read_csv(manifest_path).to_dict("records"):
            assert sha256(output / entry["path"]) == entry["sha256"]
    else:
        with manifest_path.open("w", encoding="utf-8-sig", newline="") as manifest:
            writer = csv.writer(manifest)
            writer.writerow(["path", "bytes", "sha256"])
            for path in sorted(output.iterdir()):
                if path.is_file() and path != manifest_path:
                    writer.writerow([path.name, path.stat().st_size, sha256(path)])
    print(f"DONE: {len(exported)} verified baseline artifacts; source data and production model unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=RESEARCH_ROOT / "mo_hinh/baselines_50_75")
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    run(arguments.output, arguments.verify_only)
