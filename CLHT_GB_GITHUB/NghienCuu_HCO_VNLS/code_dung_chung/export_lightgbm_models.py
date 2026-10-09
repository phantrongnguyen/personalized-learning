from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import Booster, LGBMClassifier


RESEARCH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH_ROOT.parent))

from clht_code.evaluation import metric_table
from clht_code.models import ModelConfig, make_pipeline
from NghienCuu_HCO_VNLS.code_dung_chung.baseline_artifacts import load_baseline, predict_risk, sha256, source_sha256
from NghienCuu_HCO_VNLS.code_dung_chung.export_baseline_models import METHOD_SLUGS, assert_metrics


def run(verify_only: bool) -> None:
    result_root = RESEARCH_ROOT / "ket_qua"
    model_root = RESEARCH_ROOT / "mo_hinh"
    output = model_root / "lightgbm_50_75"
    output.mkdir(parents=True, exist_ok=True)
    source_path = result_root / "so_sanh_ba_bo_hoc_50_75.csv"
    source_hash = source_sha256(source_path)
    records = pd.read_csv(source_path)
    lightgbm_records = records.loc[records["model"].eq("LightGBM")]
    expected_keys = {(cutoff, method) for cutoff in (0.5, 0.75) for method in METHOD_SLUGS}
    assert len(lightgbm_records) == 8
    assert set(zip(lightgbm_records["cutoff"], lightgbm_records["method"])) == expected_keys
    assert not lightgbm_records.duplicated(["cutoff", "method"]).any()
    protocol = json.loads((result_root / "giao_thuc_xgboost_50_75.json").read_text(encoding="utf-8"))
    versions = {name: importlib.metadata.version(name) for name in (
        "numpy", "pandas", "scikit-learn", "lightgbm", "joblib",
    )}
    for name, expected in protocol["versions"].items():
        assert importlib.metadata.version(name) == expected, name
    if not verify_only and list(output.glob("*.joblib")):
        raise FileExistsError("LightGBM artifacts already exist; use --verify-only")
    exported = []
    for cutoff in (0.5, 0.75):
        data_path = result_root / f"du_lieu_cutoff_{round(cutoff * 100)}.csv"
        data_hash = sha256(data_path)
        assert data_hash == protocol["data_sha256"][str(cutoff)]
        frame = pd.read_csv(data_path)
        train = frame.loc[frame["split"].eq("train")].copy()
        validation = frame.loc[frame["split"].eq("validation")].copy()
        groups = [set(frame.loc[frame["split"].eq(split), "id_student"]) for split in ("train", "validation", "test")]
        assert not (groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
        for method, slug in METHOD_SLUGS.items():
            row = lightgbm_records.loc[lightgbm_records["cutoff"].eq(cutoff) & lightgbm_records["method"].eq(method)].iloc[0]
            columns = row["selected_columns"].split("|")
            assert len(columns) == row["features"] and len(set(columns)) == len(columns)
            assert not set(columns) & {"risk", "final_result", "id_student", "split", "cutoff", "cutoff_mode", "score_policy", "progress_fraction", "module_presentation_length"}
            name = f"lightgbm_cutoff{round(cutoff * 100)}_{slug}"
            model_path = output / f"{name}.joblib"
            native_path = output / f"{name}.txt"
            metadata_path = output / f"{name}.json"
            if verify_only:
                artifact = load_baseline(model_path)
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                assert artifact["model_family"] == "LightGBM" and artifact["cutoff"] == cutoff
                assert artifact["method"] == method and artifact["feature_columns"] == columns
                assert metadata["dataset_sha256"] == data_hash
                assert metadata["source_results_sha256"] == source_hash
                assert metadata["native_sha256"] == sha256(native_path)
                fit_seconds = metadata["export_fit_seconds"]
            else:
                started = time.perf_counter()
                pipeline = make_pipeline(train[columns], ModelConfig("LightGBM", LGBMClassifier(**protocol["lightgbm_params"])))
                pipeline.fit(train[columns], train["risk"])
                fit_seconds = time.perf_counter() - started
                assert len(pipeline.named_steps["preprocess"].get_feature_names_out()) == row["encoded_features"]
                artifact = {
                    "schema_version": 1, "model_family": "LightGBM", "cutoff": cutoff,
                    "method": method, "feature_columns": columns,
                    "categorical_columns": train[columns].select_dtypes(include=["object", "category", "bool"]).columns.tolist(),
                    "threshold": 0.5, "pipeline": pipeline,
                    "training_policy": "Fit train only using the frozen notebook mask; validation is diagnostic; no test evaluation.",
                }
            probabilities = predict_risk(artifact, validation)
            metrics = metric_table(validation["risk"], probabilities, artifact["threshold"])
            assert_metrics(metrics, row.to_dict())
            if not verify_only:
                joblib.dump(artifact, model_path, compress=3)
                artifact["pipeline"].named_steps["model"].booster_.save_model(str(native_path))
                metadata = {
                    **{key: value for key, value in artifact.items() if key != "pipeline"},
                    "created_on": "2026-10-09", "python": platform.python_version(),
                    "artifact_versions": versions, "params": protocol["lightgbm_params"],
                    "training_rows": len(train), "validation_rows": len(validation),
                    "encoded_features": int(row["encoded_features"]), "search_rerun": False,
                    "test_evaluated": False, "production_model_changed": False,
                    "dataset_sha256": data_hash, "source_results_sha256": source_hash,
                    "source_results_hash_policy": "LF-normalized text; model and dataset hashes use exact bytes",
                    "artifact_sha256": sha256(model_path), "native_file": native_path.name,
                    "native_sha256": sha256(native_path), "export_fit_seconds": fit_seconds,
                    "metrics_validation": metrics,
                }
                metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            loaded = load_baseline(model_path)
            np.testing.assert_allclose(predict_risk(loaded, validation), probabilities, rtol=0, atol=1e-12)
            transformed = loaded["pipeline"].named_steps["preprocess"].transform(validation[columns])
            np.testing.assert_allclose(Booster(model_file=str(native_path)).predict(transformed), probabilities, rtol=0, atol=1e-12)
            exported.append({
                "model": "LightGBM", "cutoff": cutoff, "method": method,
                "features": len(columns), "encoded_features": int(row["encoded_features"]),
                "model_file": model_path.name, "native_file": native_path.name,
                "model_sha256": sha256(model_path), "native_sha256": sha256(native_path),
                "bytes": model_path.stat().st_size, "export_fit_seconds": fit_seconds,
                "verified_against_notebook": True, "reload_verified": True,
                "native_reload_verified": True, **metrics,
            })
            print(f"PASS {len(exported):02d}/8 {name}: AP={metrics['average_precision_risk']:.12f}", flush=True)
        assert sha256(data_path) == data_hash
    assert source_sha256(source_path) == source_hash
    baseline_root = model_root / "baselines_50_75"
    baseline_manifest = pd.read_csv(baseline_root / "manifest_sha256.csv")
    for entry in baseline_manifest.to_dict("records"):
        assert sha256(baseline_root / entry["path"]) == entry["sha256"]
    all_exports = pd.concat([pd.read_csv(baseline_root / "DANH_SACH_16_MODEL.csv"), pd.DataFrame(exported)], ignore_index=True)
    comparison = records.merge(all_exports[["model", "cutoff", "method", "model_file", "model_sha256", "verified_against_notebook", "reload_verified", "native_reload_verified", "export_fit_seconds"]], on=["model", "cutoff", "method"], validate="one_to_one")
    assert len(comparison) == 24
    comparison["model_file"] = comparison.apply(lambda row: f"mo_hinh/{'lightgbm_50_75' if row['model'] == 'LightGBM' else 'baselines_50_75'}/{row['model_file']}", axis=1)
    comparison["training_policy"] = "train only"
    comparison["evaluation_split"] = "validation"
    comparison["test_evaluated"] = False
    source_root = RESEARCH_ROOT.parents[1] / "apps/backend/model_store"
    main_name = "model_hco_vnls_lightgbm_cutoff75.joblib"
    metadata_name = "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"
    main_metadata = json.loads((source_root / metadata_name).read_text(encoding="utf-8"))
    assert sha256(source_root / main_name) == main_metadata["model_sha256"]
    main = joblib.load(source_root / main_name)
    assert main["feature_columns"] == main_metadata["feature_columns"]
    assert main["threshold"] == main_metadata["threshold"]
    assert len(main["pipeline"].named_steps["preprocess"].get_feature_names_out()) == 30
    assert main_metadata["training_rows"] == 19712 and main_metadata["test_rows_excluded"] == 3447
    if verify_only:
        for entry in pd.read_csv(output / "manifest_sha256.csv").to_dict("records"):
            assert sha256(output / entry["path"]) == entry["sha256"]
        pd.testing.assert_frame_equal(pd.read_csv(result_root / "so_sanh_tat_ca_model_da_xuat.csv"), comparison, check_dtype=False, atol=1e-12, rtol=0)
    else:
        pd.DataFrame(exported).to_csv(output / "DANH_SACH_8_MODEL.csv", index=False, encoding="utf-8-sig")
        comparison.to_csv(result_root / "so_sanh_tat_ca_model_da_xuat.csv", index=False, encoding="utf-8-sig")
        manifest = [{"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)} for path in sorted(output.iterdir()) if path.is_file() and path.name != "manifest_sha256.csv"]
        pd.DataFrame(manifest).to_csv(output / "manifest_sha256.csv", index=False, encoding="utf-8-sig")
        for name in (main_name, metadata_name):
            shutil.copyfile(source_root / name, model_root / name)
    for name in (main_name, metadata_name):
        hash_file = source_sha256 if name.endswith(".json") else sha256
        assert hash_file(model_root / name) == hash_file(source_root / name)
    print("DONE: 24 train-only comparison artifacts and unchanged production LightGBM copied and verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    run(parser.parse_args().verify_only)
