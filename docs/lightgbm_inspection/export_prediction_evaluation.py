from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sigmoid(scores):
    return 1 / (1 + np.exp(-np.asarray(scores)))


def metrics(labels, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "threshold": threshold, "n": len(labels),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "alerts": int(predictions.sum()),
        "accuracy": accuracy_score(labels, predictions),
        "precision_risk": precision_score(labels, predictions, zero_division=0),
        "recall_risk": recall_score(labels, predictions, zero_division=0),
        "f1_risk": f1_score(labels, predictions, zero_division=0),
        "average_precision_risk": average_precision_score(labels, probabilities),
    }


def trace_path(tree, values, names, category, source_index, tree_number):
    records = []
    node = tree["tree_structure"]
    while "split_index" in node:
        if node["decision_type"] != "<=":
            raise ValueError("Unexpected split type")
        value = float(values[node["split_feature"]])
        missing = bool(np.isnan(value)) or (node.get("missing_type") == "Zero" and value == 0)
        goes_left = node["default_left"] if missing else value <= float(node["threshold"])
        records.append({
            "category": category, "source_row_index": source_index,
            "tree_number": tree_number, "node_index": node["split_index"],
            "feature": names[node["split_feature"]], "value": value,
            "threshold": node["threshold"], "branch": "left" if goes_left else "right",
        })
        node = node["left_child"] if goes_left else node["right_child"]
    records.append({
        "category": category, "source_row_index": source_index,
        "tree_number": tree_number, "branch": "leaf",
        "leaf_index": node["leaf_index"], "native_leaf_value": node["leaf_value"],
    })
    return records, node


def run(source_root, inspection_root, output):
    output.mkdir(parents=True, exist_ok=True)
    artifact_path = source_root / "apps/backend/model_store/model_hco_vnls_lightgbm_cutoff75.joblib"
    dataset_path = source_root / "CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_75.csv"
    native_path = inspection_root / "train_only_lightgbm.txt"
    hashes_before = {str(path): sha256(path) for path in (artifact_path, dataset_path, native_path)}
    artifact = joblib.load(artifact_path)
    data = pd.read_csv(dataset_path)
    train = data.loc[data["split"].eq("train")]
    validation = data.loc[data["split"].eq("validation")]
    train_ids = set(train["id_student"])
    validation_ids = set(validation["id_student"])
    test_ids = set(data.loc[data["split"].eq("test"), "id_student"])
    assert not (train_ids & validation_ids or train_ids & test_ids or validation_ids & test_ids)
    columns = artifact["feature_columns"]
    pipeline = clone(artifact["pipeline"])
    pipeline.fit(train[columns], train["risk"])
    preprocess = pipeline.named_steps["preprocess"]
    transformed = np.asarray(preprocess.transform(validation[columns]))
    names = preprocess.get_feature_names_out().tolist()
    booster = lgb.Booster(model_file=str(native_path))
    labels = validation["risk"].to_numpy(dtype=int)
    raw_scores = booster.predict(transformed, raw_score=True)
    probabilities = booster.predict(transformed)
    pipeline_probabilities = pipeline.predict_proba(validation[columns])[:, list(pipeline.classes_).index(1)]
    np.testing.assert_allclose(probabilities, pipeline_probabilities, rtol=0, atol=1e-12)
    np.testing.assert_allclose(sigmoid(raw_scores), probabilities, rtol=0, atol=1e-12)
    baseline = metrics(labels, probabilities, 0.5)
    assert (baseline["tn"], baseline["fp"], baseline["fn"], baseline["tp"]) == (2180, 68, 362, 805)
    np.testing.assert_allclose(baseline["average_precision_risk"], 0.8967566497124569, rtol=0, atol=1e-12)
    predictions = (probabilities >= 0.5).astype(int)
    categories = np.where(labels == 1, np.where(predictions == 1, "TP", "FN"), np.where(predictions == 1, "FP", "TN"))
    rows = validation[["id_student", "code_module", "code_presentation", "final_result", "risk"]].copy()
    rows.insert(0, "source_row_index", validation.index)
    rows["F_final"], rows["p_risk"] = raw_scores, probabilities
    rows["prediction_at_0_5"], rows["category"] = predictions, categories

    def write_csv(frame, name):
        frame.to_csv(output / name, index=False, encoding="utf-8-sig")

    write_csv(rows, "du_bao_validation.csv")
    inputs = validation[columns].copy()
    inputs.insert(0, "source_row_index", validation.index)
    write_csv(inputs, "dau_vao_17_bien_validation.csv")
    encoded = pd.DataFrame(transformed, columns=names)
    encoded.insert(0, "source_row_index", validation.index)
    write_csv(encoded, "dau_vao_30_cot_validation.csv")
    threshold_table = pd.DataFrame([metrics(labels, probabilities, threshold) for threshold in (0.3, 0.4, 0.5, 0.6)])
    write_csv(threshold_table, "doi_chieu_nguong_validation.csv")
    ranked = rows.sort_values("p_risk", ascending=False, kind="stable").copy()
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1))
    write_csv(ranked, "xep_hang_nguy_co_validation.csv")
    groups = ranked.groupby("p_risk", sort=False)["risk"].agg(["size", "sum"]).reset_index()
    groups.columns = ["threshold_p", "new_rows", "new_positive_rows"]
    groups["cumulative_rows"] = groups["new_rows"].cumsum()
    groups["cumulative_tp"] = groups["new_positive_rows"].cumsum()
    groups["precision"] = groups["cumulative_tp"] / groups["cumulative_rows"]
    groups["recall"] = groups["cumulative_tp"] / labels.sum()
    groups["delta_recall"] = groups["new_positive_rows"] / labels.sum()
    groups["AP_contribution"] = groups["precision"] * groups["delta_recall"]
    np.testing.assert_allclose(groups["AP_contribution"].sum(), baseline["average_precision_risk"], rtol=0, atol=1e-12)
    write_csv(groups, "cac_buoc_tinh_AP.csv")
    initial_probability = float(train["risk"].mean())
    initial_score = float(np.log(initial_probability / (1 - initial_probability)))
    learning_rate = float(pipeline.named_steps["model"].learning_rate)
    trees = booster.dump_model()["tree_info"]
    native_leaf_indices = booster.predict(transformed, pred_leaf=True)
    samples, contribution_rows, path_rows = [], [], []
    for category, target_probability in (("TP", 0.8), ("TN", 0.1), ("FP", 0.6), ("FN", 0.4)):
        positions = np.flatnonzero(categories == category)
        position = int(positions[np.argmin(np.abs(probabilities[positions] - target_probability))])
        source_index = int(validation.index[position])
        sample = rows.iloc[position].to_dict()
        sample["F0"], sample["p0"] = initial_score, initial_probability
        samples.append(sample)
        score = initial_score
        for tree_number, tree in enumerate(trees, start=1):
            path, leaf = trace_path(tree, transformed[position], names, category, source_index, tree_number)
            assert leaf["leaf_index"] == native_leaf_indices[position, tree_number - 1]
            path_rows.extend(path)
            native_value = float(leaf["leaf_value"])
            contribution = native_value - initial_score if tree_number == 1 else native_value
            before = score
            score += contribution
            contribution_rows.append({
                "category": category, "source_row_index": source_index,
                "tree_number": tree_number, "leaf_index": leaf["leaf_index"],
                "native_leaf_value": native_value,
                "T_before_learning_rate": contribution / learning_rate,
                "delta_F": contribution, "F_before": before, "F_after": score,
                "p_before": float(sigmoid(before)), "p_after": float(sigmoid(score)),
            })
        np.testing.assert_allclose(score, raw_scores[position], rtol=0, atol=1e-12)
    contributions = pd.DataFrame(contribution_rows)
    write_csv(pd.DataFrame(samples), "bon_vi_du_TP_TN_FP_FN.csv")
    write_csv(contributions, "bon_vi_du_dong_gop_80_cay.csv")
    write_csv(pd.DataFrame(path_rows), "bon_vi_du_duong_di_80_cay.csv")
    hashes_after = {str(path): sha256(path) for path in (artifact_path, dataset_path, native_path)}
    assert hashes_before == hashes_after
    summary = {
        "policy": "Use existing train-only native booster matching the diagram. Refit cloned preprocessing on train; verify probabilities against the cloned pipeline. No test evaluation or model selection.",
        "split_rows": {str(key): int(value) for key, value in data["split"].value_counts().items()},
        "disjoint_student_groups": True,
        "F0": initial_score, "p0": initial_probability,
        "learning_rate": learning_rate, "num_trees": len(trees),
        "original_features": len(columns), "encoded_features": len(names),
        "metrics_validation": baseline,
        "AP_reconstructed": float(groups["AP_contribution"].sum()),
        "max_native_pipeline_probability_difference": float(np.max(np.abs(probabilities - pipeline_probabilities))),
        "test_evaluated": False, "input_hashes_unchanged": hashes_after,
        "example_policy": "Pick actual validation rows nearest 0.8/0.1/0.6/0.4 within TP/TN/FP/FN; these are selected examples, not representative prevalence.",
        "examples": samples,
    }
    history_path = source_root.parent / "CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/ket_qua_test_xac_nhan.csv"
    if history_path.exists():
        history = pd.read_csv(history_path)
        write_csv(history, "test_lich_su_cac_model_khac.csv")
        summary["historical_test_source"] = str(history_path)
        summary["historical_test_sha256"] = sha256(history_path)
        summary["historical_test_models"] = history["model"].unique().tolist()
        summary["historical_test_warning"] = "Existing results from other models, not test metrics of the HCO-VNLS LightGBM artifact or a new untouched holdout."
    (output / "kiem_chung_du_bao.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(threshold_table.to_string(index=False))
    print(contributions.loc[contributions["tree_number"].isin([1, 2, 40, 80])].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--inspection-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "du_bao_va_danh_gia")
    arguments = parser.parse_args()
    run(arguments.source_root, arguments.inspection_root, arguments.output)
