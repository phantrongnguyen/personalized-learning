"""Render aggregate thesis charts from verified, row-level historical test scores.

No model is loaded or fitted. Raw predictions remain outside the repository.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
    f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score,
    roc_curve,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESEARCH = ROOT / "experiments" / "hco_vnls" / "ket_qua"
ARTIFACT = ROOT / "apps" / "backend" / "artifacts" / "model_hco_vnls_lightgbm_cutoff75.joblib"
METADATA = ROOT / "apps" / "backend" / "artifacts" / "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"
NAVY, TEAL, GOLD, RED = "#142A3B", "#008C87", "#D19435", "#B45353"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata_hash_matches(path, expected):
    """Accept only byte-identical metadata or the Git LF/CRLF representation."""
    raw = path.read_bytes()
    lf = raw.replace(b'\r\n', b'\n')
    return expected in {hashlib.sha256(value).hexdigest() for value in (raw, lf, lf.replace(b'\n', b'\r\n'))}


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 14,
        "axes.labelcolor": NAVY, "text.color": NAVY, "axes.edgecolor": "#BCC8CE",
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "axes.spines.top": False,
        "axes.spines.right": False, "grid.alpha": 0.2,
    })


def save(fig, name, note):
    fig.text(0.06, 0.015, note, fontsize=8, color="#566977")
    fig.savefig(HERE / "figures" / name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def verify_scores(predictions, verification):
    expected = verification["metrics"]
    reported_hash = verification["input_hashes_unchanged"]
    if sha256(ARTIFACT) != reported_hash["model"] or not metadata_hash_matches(METADATA, reported_hash["metadata"]):
        raise ValueError("Frozen app model or metadata differs from historical verification")
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    if metadata["model_sha256"] != reported_hash["model"] or metadata["data_sha256"] != reported_hash["dataset"]:
        raise ValueError("Artifact metadata does not match historical verification")
    if (expected.get("threshold") != 0.5 or expected.get("cutoff_fraction") != 0.75
            or expected.get("feature_count") != 17 or metadata.get("cutoff_fraction") != 0.75
            or len(metadata.get("feature_columns", [])) != 17):
        raise ValueError("Locked threshold, cutoff or feature count disagrees")
    if verification.get("model_refit_during_evaluation") is not False or verification.get("threshold_tuned_on_test") is not False:
        raise ValueError("Historical protocol is not the locked-model evaluation")
    required = {"risk", "p_risk", "prediction_at_0_5", "source_row_index"}
    if not required.issubset(predictions.columns) or predictions[sorted(required)].isna().any().any():
        raise ValueError("Missing or null prediction columns")
    actual = predictions["risk"].to_numpy()
    predicted = predictions["prediction_at_0_5"].to_numpy()
    scores = predictions["p_risk"].to_numpy(dtype=float)
    if (len(actual) != expected["test_rows"] or predictions["source_row_index"].duplicated().any()
            or not set(actual).issubset({0, 1}) or not set(predicted).issubset({0, 1})
            or not np.isfinite(scores).all() or not np.all((0 <= scores) & (scores <= 1))
            or not np.array_equal(predicted, (scores >= expected["threshold"]).astype(int))):
        raise ValueError("Test rows, class labels, scores or locked threshold disagree")
    tn, fp, fn, tp = (int(value) for value in confusion_matrix(actual, predicted, labels=[0, 1]).ravel())
    computed = {
        "test_rows": len(actual), "accuracy": accuracy_score(actual, predicted),
        "precision_risk": precision_score(actual, predicted),
        "recall_risk": recall_score(actual, predicted), "f1_risk": f1_score(actual, predicted),
        "weighted_f1": f1_score(actual, predicted, average="weighted"),
        "average_precision_risk": average_precision_score(actual, scores),
        "roc_auc": roc_auc_score(actual, scores), "brier_score": brier_score_loss(actual, scores),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "alerts": int(predicted.sum()), "actual_risk": int(actual.sum()),
    }
    for key, value in computed.items():
        if key not in expected or not np.isclose(value, expected[key], rtol=0, atol=1e-10):
            raise ValueError(f"Historical test result disagrees: {key}")
    return actual, scores, computed


def confusion_chart(computed, note):
    matrix = np.array([[computed["tn"], computed["fp"]], [computed["fn"], computed["tp"]]])
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.imshow(matrix, cmap="BuGn", vmin=0)
    ax.set_xticks([0, 1], ["Predicted non-risk", "Predicted risk"])
    ax.set_yticks([0, 1], ["Actual non-risk", "Actual risk"])
    ax.set_xlabel("Model classification at threshold 0.50")
    ax.set_title("01 / Confusion matrix - historical test", loc="left", fontweight="bold", pad=20)
    for row in range(2):
        for column in range(2):
            count = matrix[row, column]
            ax.text(column, row, f"{count:,}\n{count / matrix[row].sum():.1%} of row",
                    ha="center", va="center", fontsize=12, fontweight="bold",
                    color="white" if count > matrix.max() / 2 else NAVY)
    save(fig, "01_confusion_matrix.png", note + "  |  Row percentages use the true class as denominator.")


def ranking_chart(actual, scores, computed, note):
    fpr, tpr, _ = roc_curve(actual, scores)
    precision, recall, _ = precision_recall_curve(actual, scores)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    axes[0].plot(fpr, tpr, color=TEAL, lw=2.5, label=f"ROC-AUC {computed['roc_auc']:.3f}")
    axes[0].plot([0, 1], [0, 1], color="#9DAFB7", ls="--", label="Random ranking")
    axes[0].set(xlabel="False-positive rate", ylabel="True-positive rate", xlim=(0, 1), ylim=(0, 1))
    axes[1].plot(recall, precision, color=GOLD, lw=2.5, label=f"AP {computed['average_precision_risk']:.3f}")
    axes[1].axhline(actual.mean(), color="#9DAFB7", ls="--", label=f"Risk prevalence {actual.mean():.1%}")
    axes[1].set(xlabel="Recall (risk class)", ylabel="Precision (risk class)", xlim=(0, 1), ylim=(0, 1))
    for ax in axes:
        ax.grid(True)
        ax.legend(frameon=False, loc="lower right")
    fig.suptitle("02 / Ranking quality - historical test", x=0.06, ha="left", fontweight="bold", fontsize=14)
    fig.subplots_adjust(top=0.86, bottom=0.16, wspace=0.3)
    save(fig, "02_roc_precision_recall.png", note + "  |  AP is not ROC-AUC.")


def calibration_chart(actual, scores, computed, note):
    observed, estimated = calibration_curve(actual, scores, n_bins=10, strategy="quantile")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot([0, 1], [0, 1], color="#9DAFB7", ls="--", label="Perfect calibration")
    ax.plot(estimated, observed, marker="o", color=TEAL, lw=2.5,
            label=f"Historical test; Brier {computed['brier_score']:.3f}")
    ax.set(xlabel="Mean predicted risk in quantile bin", ylabel="Observed risk fraction", xlim=(0, 1), ylim=(0, 1))
    ax.set_title("03 / Calibration diagnostic", loc="left", fontweight="bold", pad=20)
    ax.grid(True)
    ax.legend(frameon=False)
    save(fig, "03_calibration.png", note + "  |  Descriptive only; no recalibration performed.")


def threshold_chart(actual, scores, computed, note):
    thresholds = np.round(np.arange(0.05, 0.951, 0.05), 2)
    precision, recall, alerts = [], [], []
    for threshold in thresholds:
        labels = scores >= threshold
        precision.append(precision_score(actual, labels, zero_division=0))
        recall.append(recall_score(actual, labels, zero_division=0))
        alerts.append(int(labels.sum()))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(thresholds, precision, color=TEAL, lw=2.5, label="Precision (risk)")
    ax.plot(thresholds, recall, color=RED, lw=2.5, label="Recall (risk)")
    ax.set(xlabel="Illustrative classification threshold", ylabel="Score", xlim=(0, 1), ylim=(0, 1))
    ax2 = ax.twinx()
    ax2.plot(thresholds, alerts, color=GOLD, ls=":", lw=2, label="Number flagged")
    ax2.set_ylabel("Number flagged", color=GOLD)
    ax.axvline(0.5, color=NAVY, ls="--", lw=1.5)
    ax.annotate(f"App threshold 0.50\n{computed['alerts']} flagged; {computed['fn']} missed",
                xy=(0.5, 0.45), xytext=(0.54, 0.35), color=NAVY,
                arrowprops={"arrowstyle": "->", "color": NAVY})
    ax.set_title("04 / Threshold sensitivity (not tuning)", loc="left", fontweight="bold", pad=20)
    ax.grid(True)
    ax.legend([*ax.lines[:2], ax2.lines[0]], ["Precision", "Recall", "Number flagged"], frameon=False, loc="lower left")
    save(fig, "04_threshold_sensitivity.png", note + "  |  App threshold stays 0.50; no test-set selection.")


def validation_chart(note):
    frame = pd.read_csv(RESEARCH / "so_sanh_ba_bo_hoc_50_75.csv")
    rows = frame.loc[(frame["cutoff"] == 0.75) & (frame["method"] == "HCO-VNLS")]
    rows = rows.set_index("model").loc[["LightGBM", "XGBoost", "CatBoost"]]
    if len(rows) != 3 or not (rows["n"] == 3415).all():
        raise ValueError("Comparison rows do not describe the same 75% validation split")
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    positions = np.arange(3)
    ax.barh(positions - 0.18, rows["average_precision_risk"], height=0.33, color=TEAL, label="Average precision")
    ax.barh(positions + 0.18, rows["recall_risk"], height=0.33, color=GOLD, label="Recall (risk)")
    ax.set_yticks(positions, [f"{model} ({int(row.features)} features)" for model, row in rows.iterrows()])
    ax.invert_yaxis()
    ax.set(xlabel="Validation metric", xlim=(0, 1))
    ax.set_title("05 / Learner comparison at cutoff 75%", loc="left", fontweight="bold", pad=20)
    ax.legend(frameon=False)
    ax.grid(axis="x")
    for row_index, row in enumerate(rows.itertuples()):
        for y, value in ((row_index - 0.18, row.average_precision_risk), (row_index + 0.18, row.recall_risk)):
            ax.text(value + 0.01, y, f"{value:.3f}", va="center", fontsize=9)
    save(fig, "05_validation_comparison.png",
         "Train-only validation, n=3,415; NOT the final app artifact or historical test. Masks differ by learner.")


def ablation_chart():
    frame = pd.read_csv(RESEARCH / "ablation_hybrid_75_train_cv.csv")
    top = frame.reindex(frame["delta_ap_cv"].abs().sort_values(ascending=False).index).head(10)
    fig, ax = plt.subplots(figsize=(9.5, 6))
    ax.barh(top["feature"], top["delta_ap_cv"], color=[TEAL if delta > 0 else RED for delta in top["delta_ap_cv"]])
    ax.invert_yaxis()
    ax.axvline(0, color=NAVY, lw=1)
    ax.set_xlabel("AP with all selected features minus AP without one feature (train CV)")
    ax.set_title("06 / Feature ablation - train CV", loc="left", fontweight="bold", pad=20)
    ax.grid(axis="x")
    save(fig, "06_feature_ablation.png",
         "Train CV only; small deltas are descriptive and do not prove causal feature importance.")


def split_chart(actual, verification):
    frame = pd.read_csv(RESEARCH / "tong_quan_cac_moc.csv")
    row = frame.loc[frame["cutoff"] == 0.75].iloc[0]
    counts = [int(row["train"]), int(row["validation"]), int(row["test"])]
    if counts[0] + counts[1] != verification["metrics"]["train_validation_rows"] or counts[2] != len(actual):
        raise ValueError("Locked model split differs from research overview")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    axes[0].bar(["Train", "Validation", "Test"], counts, color=[NAVY, TEAL, GOLD])
    for index, count in enumerate(counts):
        axes[0].text(index, count + 250, f"{count:,}", ha="center", fontweight="bold")
    axes[0].set(ylim=(0, 18500), ylabel="Course enrollments", title="Frozen 75% split")
    risk_count = int(actual.sum())
    axes[1].bar(["Non-risk", "Risk"], [len(actual) - risk_count, risk_count], color=[TEAL, RED])
    for index, count in enumerate((len(actual) - risk_count, risk_count)):
        axes[1].text(index, count + 35, f"{count:,}", ha="center", fontweight="bold")
    axes[1].set(ylim=(0, 2600), ylabel="Historical test enrollments", title="Test class balance")
    fig.suptitle("00 / Split and observed classes", x=0.05, ha="left", fontsize=14, fontweight="bold")
    fig.subplots_adjust(top=0.82, bottom=0.18, wspace=0.35)
    save(fig, "00_split_and_classes.png",
         "OULAD cutoff 75%; train + validation = 19,712 for final fit; test = 3,447 held out from fit, not new externally unseen data.")


def reduction_chart():
    frame = pd.read_csv(RESEARCH / "so_sanh_ba_bo_hoc_50_75.csv")
    rows = frame.loc[(frame["model"] == "LightGBM") & (frame["cutoff"] == 0.75)]
    full = rows.loc[rows["method"] == "Full features"].iloc[0]
    selected = rows.loc[rows["method"] == "HCO-VNLS"].iloc[0]
    if (int(full.features), int(selected.features), int(full.n), int(selected.n)) != (38, 17, 3415, 3415):
        raise ValueError("Frozen feature selection does not match validation comparison")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    axes[0].bar(["Full", "HCO-VNLS"], [full.features, selected.features], color=["#A8B9C0", TEAL])
    axes[0].set(ylabel="Original features", ylim=(0, 45), title="38 to 17 original features")
    axes[0].text(1, selected.features + 1, "55.3% fewer", ha="center", fontweight="bold")
    positions = np.arange(2)
    axes[1].bar(positions - 0.18, [full.average_precision_risk, selected.average_precision_risk],
                width=0.35, color=TEAL, label="Average precision")
    axes[1].bar(positions + 0.18, [full.recall_risk, selected.recall_risk],
                width=0.35, color=GOLD, label="Recall (risk)")
    axes[1].set(xticks=positions, xticklabels=["Full", "HCO-VNLS"], ylim=(0, 1), title="Validation trade-off")
    axes[1].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2)
    fig.suptitle("07 / Feature reduction is a trade-off", x=0.05, ha="left", fontsize=14, fontweight="bold")
    fig.subplots_adjust(top=0.82, bottom=0.25, wspace=0.35)
    save(fig, "07_feature_reduction.png",
         "Train-only LightGBM validation (n=3,415); NOT the refitted app model test. 17 original features become 30 encoded columns.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="Local, untracked historical test CSV")
    parser.add_argument("--verification", required=True, type=Path, help="Historical checksum/metric JSON")
    args = parser.parse_args()
    verification = json.loads(args.verification.read_text(encoding="utf-8"))
    predictions = pd.read_csv(args.predictions)
    actual, scores, computed = verify_scores(predictions, verification)
    style()
    (HERE / "figures").mkdir(parents=True, exist_ok=True)
    note = f"OULAD historical test, n={len(actual):,}; frozen model SHA {sha256(ARTIFACT)[:12]}; not a new external holdout."
    split_chart(actual, verification)
    confusion_chart(computed, note)
    ranking_chart(actual, scores, computed, note)
    calibration_chart(actual, scores, computed, note)
    threshold_chart(actual, scores, computed, note)
    validation_chart(note)
    ablation_chart()
    reduction_chart()
    summary = {
        "scope": "historical OULAD test, not a new external holdout",
        "evaluated_at": verification["evaluated_at"],
        "model_sha256": sha256(ARTIFACT), "metadata_sha256": sha256(METADATA),
        "dataset_sha256_reported": verification["input_hashes_unchanged"]["dataset"],
        "predictions_sha256": sha256(args.predictions),
        "threshold_unchanged": verification["metrics"]["threshold"],
        "metrics": computed,
        "note": "Recomputed from archived predictions; this script does not load or fit the model.",
    }
    (HERE / "verified_metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified {len(actual)} rows and generated 8 charts; app model unchanged.")


if __name__ == "__main__":
    main()
