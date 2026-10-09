from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source_root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    artifact_path = source_root / "apps/backend/model_store/model_hco_vnls_lightgbm_cutoff75.joblib"
    metadata_path = source_root / "apps/backend/model_store/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"
    dataset_path = source_root / "CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_75.csv"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    hashes_before = {
        "model": sha256(artifact_path),
        "metadata": sha256(metadata_path),
        "dataset": sha256(dataset_path),
    }
    assert hashes_before["model"] == metadata["model_sha256"]
    assert hashes_before["dataset"] == metadata["data_sha256"]
    artifact = joblib.load(artifact_path)
    assert artifact["feature_columns"] == metadata["feature_columns"]
    assert artifact["threshold"] == metadata["threshold"] == 0.5
    assert metadata["training_rows"] == 19712
    assert metadata["test_rows_excluded"] == 3447
    frame = pd.read_csv(dataset_path)
    test = frame.loc[frame["split"].eq("test")].copy()
    train_validation = frame.loc[frame["split"].isin(["train", "validation"])]
    assert len(test) == 3447
    assert len(train_validation) == 19712
    assert not set(test["id_student"]) & set(train_validation["id_student"])
    pipeline = artifact["pipeline"]
    positive_index = list(pipeline.classes_).index(1)
    probabilities = pipeline.predict_proba(test[artifact["feature_columns"]])[:, positive_index]
    threshold = float(artifact["threshold"])
    predictions = (probabilities >= threshold).astype(int)
    labels = test["risk"].to_numpy(dtype=int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    metrics = {
        "model": metadata["model_name"],
        "cutoff_fraction": metadata["cutoff_fraction"],
        "training_policy": metadata["training_policy"],
        "train_validation_rows": len(train_validation),
        "test_rows": len(test),
        "feature_count": len(artifact["feature_columns"]),
        "threshold": threshold,
        "accuracy": accuracy_score(labels, predictions),
        "precision_risk": precision_score(labels, predictions, zero_division=0),
        "recall_risk": recall_score(labels, predictions, zero_division=0),
        "f1_risk": f1_score(labels, predictions, zero_division=0),
        "weighted_f1": f1_score(labels, predictions, average="weighted", zero_division=0),
        "average_precision_risk": average_precision_score(labels, probabilities),
        "roc_auc": roc_auc_score(labels, probabilities),
        "brier_score": brier_score_loss(labels, probabilities),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "alerts": int(predictions.sum()), "actual_risk": int(labels.sum()),
    }
    prediction_rows = test[["id_student", "code_module", "code_presentation", "final_result", "risk"]].copy()
    prediction_rows.insert(0, "source_row_index", test.index)
    prediction_rows["p_risk"] = probabilities
    prediction_rows["p_non_risk"] = 1 - probabilities
    prediction_rows["prediction_at_0_5"] = predictions
    prediction_rows["category"] = np.where(
        labels == 1,
        np.where(predictions == 1, "TP", "FN"),
        np.where(predictions == 1, "FP", "TN"),
    )
    prediction_rows.to_csv(output / "du_doan_test_model_chinh.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([metrics]).to_csv(output / "ket_qua_test_model_chinh.csv", index=False, encoding="utf-8-sig")
    ranked = prediction_rows.sort_values("p_risk", ascending=False, kind="stable").copy()
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1))
    ranked["cumulative_risk"] = ranked["risk"].cumsum()
    ranked["precision_at_rank"] = ranked["cumulative_risk"] / ranked["rank"]
    ranked["recall_at_rank"] = ranked["cumulative_risk"] / labels.sum()
    ranked.to_csv(output / "xep_hang_nguy_co_test.csv", index=False, encoding="utf-8-sig")
    ap_steps = ranked.groupby("p_risk", sort=False)["risk"].agg(["size", "sum"]).reset_index()
    ap_steps.columns = ["threshold_p", "new_rows", "new_positive_rows"]
    ap_steps["cumulative_rows"] = ap_steps["new_rows"].cumsum()
    ap_steps["cumulative_tp"] = ap_steps["new_positive_rows"].cumsum()
    ap_steps["precision"] = ap_steps["cumulative_tp"] / ap_steps["cumulative_rows"]
    ap_steps["recall"] = ap_steps["cumulative_tp"] / labels.sum()
    ap_steps["delta_recall"] = ap_steps["new_positive_rows"] / labels.sum()
    ap_steps["AP_contribution"] = ap_steps["precision"] * ap_steps["delta_recall"]
    reconstructed_ap = float(ap_steps["AP_contribution"].sum())
    np.testing.assert_allclose(reconstructed_ap, metrics["average_precision_risk"], rtol=0, atol=1e-12)
    ap_steps.to_csv(output / "cac_buoc_tinh_AP_test.csv", index=False, encoding="utf-8-sig")
    top_k = []
    for count in (100, 500, metrics["alerts"], 1000, len(ranked)):
        subset = ranked.head(count)
        positives = int(subset["risk"].sum())
        top_k.append({
            "top_k": int(count),
            "risk_rows": positives,
            "precision_at_k": positives / count,
            "recall_at_k": positives / int(labels.sum()),
        })
    pd.DataFrame(top_k).to_csv(output / "xep_hang_top_k_test.csv", index=False, encoding="utf-8-sig")
    hashes_after = {
        "model": sha256(artifact_path),
        "metadata": sha256(metadata_path),
        "dataset": sha256(dataset_path),
    }
    assert hashes_before == hashes_after
    verification = {
        "evaluated_at": "2026-10-09",
        "evaluation_type": "Historical test confirmation; this OULAD test split has appeared in prior project history and is not a newly untouched external holdout.",
        "model_refit_during_evaluation": False,
        "threshold_tuned_on_test": False,
        "student_groups_disjoint": True,
        "input_hashes_unchanged": hashes_after,
        "metrics": metrics,
        "AP_reconstructed_from_probability_ranking": reconstructed_ap,
        "top_k": top_k,
    }
    (output / "kiem_chung_test_model_chinh.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "du_bao_va_danh_gia",
    )
    arguments = parser.parse_args()
    run(arguments.source_root, arguments.output)
