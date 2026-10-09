from __future__ import annotations

import hashlib
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix


def verify(root: Path) -> None:
    trees_root = root / "toan_bo_80_cay"
    training = json.loads((trees_root / "kiem_chung.json").read_text(encoding="utf-8"))
    previous_scores = None
    for tree_number in range(1, training["num_trees"] + 1):
        prefix = trees_root / "du_lieu" / f"cay_{tree_number}"
        rows = pd.read_csv(f"{prefix}_dong.csv.gz")
        leaves = pd.read_csv(f"{prefix}_la.csv")
        rows[["gradient", "hessian"]] = rows[["gradient", "hessian"]].astype(np.float32).astype(np.float64)
        assert len(rows) == training["train_rows"]
        np.testing.assert_array_equal(rows["row_id"], np.arange(len(rows)))
        assert len(leaves) == training["leaves_per_tree"]
        assert int(leaves["n"].sum()) == len(rows)
        if previous_scores is None:
            np.testing.assert_allclose(rows["F_before"], training["F0"], atol=1e-12)
        else:
            np.testing.assert_allclose(rows["F_before"], previous_scores, atol=1e-12)
        np.testing.assert_allclose(rows["p_before"], 1 / (1 + np.exp(-rows["F_before"])), atol=1e-12)
        np.testing.assert_allclose(rows["gradient"], (rows["p_before"] - rows["risk"]).astype(np.float32), atol=1e-12)
        np.testing.assert_allclose(rows["hessian"], (rows["p_before"] * (1 - rows["p_before"])).astype(np.float32), atol=1e-12)
        np.testing.assert_allclose(rows["delta_F"], training["learning_rate"] * rows["T"], atol=1e-12)
        np.testing.assert_allclose(rows["F_after"], rows["F_before"] + rows["delta_F"], atol=1e-12)
        np.testing.assert_allclose(rows["p_after"], 1 / (1 + np.exp(-rows["F_after"])), atol=1e-12)
        grouped = rows.groupby("leaf_index").agg(n=("risk", "size"), sum_gradient=("gradient", "sum"), sum_hessian=("hessian", "sum"))
        expected = leaves.set_index("leaf_index").sort_index()
        np.testing.assert_array_equal(grouped["n"], expected["n"])
        np.testing.assert_allclose(grouped[["sum_gradient", "sum_hessian"]], expected[["sum_gradient", "sum_hessian"]], atol=1e-9)
        previous_scores = rows["F_after"].to_numpy()

    booster = lgb.Booster(model_file=str(root / "train_only_lightgbm.txt"))
    features = pd.read_csv(trees_root / "du_lieu_chung" / "dac_trung_30_cot.csv.gz")
    feature_names = booster.feature_name()
    if set(feature_names).issubset(features.columns):
        features = features[feature_names]
    else:
        features = features.drop(columns=["row_id"], errors="ignore")
    assert features.shape == (training["train_rows"], booster.num_feature())
    np.testing.assert_allclose(previous_scores, booster.predict(features.to_numpy(), raw_score=True), atol=1e-10)

    evaluation_root = root / "du_bao_va_danh_gia"
    for prediction_name, summary_name, metrics_key in (
        ("du_bao_validation.csv", "kiem_chung_du_bao.json", "metrics_validation"),
        ("du_doan_test_model_chinh.csv", "kiem_chung_test_model_chinh.json", "metrics"),
    ):
        predictions = pd.read_csv(evaluation_root / prediction_name)
        summary = json.loads((evaluation_root / summary_name).read_text(encoding="utf-8"))
        metrics = summary[metrics_key]
        labels = predictions["risk"].to_numpy()
        probabilities = predictions["p_risk"].to_numpy()
        decisions = (probabilities >= metrics["threshold"]).astype(int)
        np.testing.assert_array_equal(decisions, predictions["prediction_at_0_5"])
        np.testing.assert_array_equal(confusion_matrix(labels, decisions, labels=[0, 1]).ravel(), [metrics[key] for key in ("tn", "fp", "fn", "tp")])
        np.testing.assert_allclose(accuracy_score(labels, decisions), metrics["accuracy"], atol=1e-12)
        np.testing.assert_allclose(average_precision_score(labels, probabilities), metrics["average_precision_risk"], atol=1e-12)

    for name in ("cac_buoc_tinh_AP.csv", "cac_buoc_tinh_AP_test.csv"):
        steps = pd.read_csv(evaluation_root / name)
        np.testing.assert_allclose(steps["AP_contribution"], steps["precision"] * steps["delta_recall"], atol=1e-12)
        expected_ap = training["validation_AP"] if name == "cac_buoc_tinh_AP.csv" else pd.read_csv(evaluation_root / "ket_qua_test_model_chinh.csv")["average_precision_risk"].iloc[0]
        np.testing.assert_allclose(steps["AP_contribution"].sum(), expected_ap, atol=1e-12)

    manifest_path = root / "manifest_sha256.csv"
    if manifest_path.exists():
        for record in pd.read_csv(manifest_path).to_dict("records"):
            path = root / record["path"]
            assert path.stat().st_size == record["bytes"], record["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], record["path"]
    print("PASS: 80 trees, gradients/Hessians, score updates, leaf sums, native predictions, validation/test metrics, AP and checksums.")


if __name__ == "__main__":
    verify(Path(__file__).resolve().parent)
