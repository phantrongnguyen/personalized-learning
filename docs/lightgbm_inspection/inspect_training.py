from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import textwrap
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import average_precision_score, confusion_matrix

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


def sigmoid(scores):
    return 1.0 / (1.0 + np.exp(-np.asarray(scores)))


def short_name(feature_name):
    return feature_name.split("__", maxsplit=1)[-1]


def format_threshold(threshold):
    return "0" if abs(threshold) < 1e-20 else f"{threshold:.6g}"


def read_native_bins(path, num_features, num_rows):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\d+,\s", line):
            continue
        entries = [entry.strip() for entry in line.split(",") if entry.strip()]
        if len(entries) == num_features:
            rows.append([int(entry) for entry in entries])
    result = np.asarray(rows, dtype=np.int32)
    if result.shape != (num_rows, num_features):
        raise ValueError(f"Unexpected bin matrix shape: {result.shape}")
    return result


def walk_tree(node, leaves, splits, path=()):
    if "leaf_index" in node:
        leaves[node["leaf_index"]] = {"node": node, "path": path}
        return
    splits[node["split_index"]] = node
    walk_tree(node["left_child"], leaves, splits, path + ((node["split_index"], True),))
    walk_tree(node["right_child"], leaves, splits, path + ((node["split_index"], False),))


def tree_layout(node, positions, depth=0, next_leaf=None):
    if next_leaf is None:
        next_leaf = [0]
    if "leaf_index" in node:
        vertical = next_leaf[0]
        next_leaf[0] += 1
        positions[("leaf", node["leaf_index"])] = (depth, vertical)
        return vertical
    left_vertical = tree_layout(node["left_child"], positions, depth + 1, next_leaf)
    right_vertical = tree_layout(node["right_child"], positions, depth + 1, next_leaf)
    vertical = (left_vertical + right_vertical) / 2
    positions[("split", node["split_index"])] = (depth, vertical)
    return vertical


def draw_tree(first_tree, feature_names, leaf_table, highlighted_leaf, output):
    structure = first_tree["tree_structure"]
    positions = {}
    tree_layout(structure, positions)
    max_depth = max(position[0] for position in positions.values())
    leaves, splits = {}, {}
    walk_tree(structure, leaves, splits)
    highlighted_path = set(leaves[highlighted_leaf]["path"])
    leaf_records = leaf_table.set_index("leaf_index")
    figure, axis = plt.subplots(figsize=(max(21, 3.7 * (max_depth + 1)), 14))
    axis.set_xlim(-0.7, max_depth + 0.75)
    axis.set_ylim(first_tree["num_leaves"] - 0.3, -0.8)
    axis.axis("off")

    def draw_node(node):
        is_leaf = "leaf_index" in node
        key = ("leaf", node["leaf_index"]) if is_leaf else ("split", node["split_index"])
        horizontal, vertical = positions[key]
        if is_leaf:
            record = leaf_records.loc[node["leaf_index"]]
            label = (
                f"Lá {node['leaf_index']} · n={node['leaf_count']:,}\n"
                f"T₁={record.T1:+.4f} · ΔF={record.delta_F:+.4f}\n"
                f"F₁={record.F1:+.4f} · p₁={record.p1:.2%}"
            )
            highlighted = node["leaf_index"] == highlighted_leaf
            fill = "#fff1d6" if highlighted else "#e7f3ec"
            border = "#c77800" if highlighted else "#44836a"
        else:
            feature_name = short_name(feature_names[node["split_feature"]])
            wrapped_name = "\n".join(textwrap.wrap(feature_name, width=26))
            label = (
                f"Nút {node['split_index']}\n{wrapped_name}\n"
                f"≤ {format_threshold(node['threshold'])}?\nn={node['internal_count']:,}"
            )
            fill, border = "#e8f1fb", "#366caa"
            for goes_left, child in ((True, node["left_child"]), (False, node["right_child"])):
                child_key = ("leaf", child["leaf_index"]) if "leaf_index" in child else ("split", child["split_index"])
                child_horizontal, child_vertical = positions[child_key]
                highlighted = (node["split_index"], goes_left) in highlighted_path
                color = "#c77800" if highlighted else "#9cabb7"
                axis.add_patch(FancyArrowPatch(
                    (horizontal + 0.37, vertical), (child_horizontal - 0.37, child_vertical),
                    arrowstyle="-|>", mutation_scale=12, linewidth=2 if highlighted else 1,
                    color=color, zorder=1,
                ))
                axis.text(
                    horizontal + 0.51, vertical + (child_vertical - vertical) * 0.18,
                    "Có (≤)" if goes_left else "Không (>)", fontsize=7.5,
                    color=color, ha="center", va="center",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
                )
                draw_node(child)
        axis.text(
            horizontal, vertical, label, ha="center", va="center", fontsize=9,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": fill, "edgecolor": border, "linewidth": 1.3},
            zorder=2,
        )

    draw_node(structure)
    figure.suptitle("CÂY 1 · LIGHTGBM TRAIN-ONLY · CUTOFF 75%", fontsize=19, fontweight="bold", y=0.985)
    figure.text(0.5, 0.949, "16.297 dòng train · 30 cột sau tiền xử lý · 15 lá · đường cam đến lá tăng điểm mạnh nhất", ha="center", fontsize=12)
    figure.text(
        0.5, 0.017,
        "T₁: đầu ra cây trước learning rate · ΔF = 0,055 × T₁ · F₁ = F₀ + ΔF · p₁ = sigmoid(F₁)\n"
        "p₁ là xác suất SAU CÂY ĐẦU, không phải xác suất cuối của 80 cây. Biến one-hot có giá trị 0/1.",
        ha="center", fontsize=11,
    )
    figure.subplots_adjust(top=0.91, bottom=0.075, left=0.015, right=0.99)
    figure.savefig(output / "first_tree_full.png", dpi=180, facecolor="white")
    figure.savefig(output / "first_tree_full.svg", facecolor="white")
    plt.close(figure)


def draw_histogram(histogram, split_bin, threshold, feature_name, output, tree_number=1, file_stem="histogram_root_feature"):
    figure, axes = plt.subplots(3, 1, figsize=(15.5, 11))
    figure.suptitle(f"HISTOGRAM VÒNG {tree_number}: {feature_name}", fontsize=17, fontweight="bold", y=0.985)
    figure.text(0.5, 0.943, "Bin ID lấy trực tiếp từ LightGBM Dataset · 16.297 dòng train · Tái dựng thống kê tại nút gốc", ha="center", fontsize=11)
    bin_ids = histogram.bin_id.to_numpy()
    axes[0].bar(bin_ids, histogram.risk_0, color="#739bc5", width=0.85, label="Nhãn thật 0")
    axes[0].bar(bin_ids, histogram.risk_1, bottom=histogram.risk_0, color="#d89348", width=0.85, label="Nhãn thật 1")
    axes[0].set_ylabel("Số dòng train")
    axes[0].set_title(f"Phân bố đầy đủ: {len(histogram)} bin có dữ liệu; KHÔNG tự đặt khoảng bin", loc="left", fontsize=11)
    axes[0].legend(loc="upper right", frameon=False)
    axes[0].set_xlabel("Bin ID gốc của LightGBM; ID không phải giá trị đặc trưng")
    axes[0].axvline(split_bin + 0.5, color="#bd472f", linestyle="--", linewidth=1.6)
    axes[0].annotate(
        f"Nút gốc cây {tree_number}: {feature_name} ≤ {format_threshold(threshold)}",
        xy=(split_bin + 0.5, histogram["count"].max() * 0.65),
        xytext=(0.30, 0.80), textcoords="axes fraction", fontsize=10,
        arrowprops={"arrowstyle": "->", "color": "#bd472f"},
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 3},
    )
    zoom = histogram.loc[histogram.bin_id.between(max(0, split_bin - 4), split_bin + 4)].copy()
    unit = "click" if feature_name.startswith("clicks_") else "ngày" if "days" in feature_name or "activity" in feature_name else ""
    zoom_labels = []
    for row in zoom.itertuples():
        observed_range = format_threshold(row.value_min)
        if row.value_min != row.value_max:
            observed_range += f"–{format_threshold(row.value_max)}"
        zoom_labels.append(f"Bin {row.bin_id}\n{observed_range} {unit}".strip())
    gradients = zoom.sum_gradient.to_numpy()
    axes[1].bar(zoom.bin_id, gradients, color=np.where(gradients >= 0, "#366caa", "#bf692c"), width=0.72)
    axes[1].axhline(0, color="#66717a", linewidth=0.8)
    axes[1].set_ylabel("Tổng gradient G")
    axes[1].set_title("Phóng to quanh phép chia: G = tổng (p trước cây − nhãn thật) trong từng bin", loc="left", fontsize=11)
    axes[1].set_xticks(zoom.bin_id, zoom_labels, fontsize=9)
    axes[2].bar(zoom.bin_id, zoom.sum_hessian, color="#4f947d", width=0.72)
    axes[2].set_ylabel("Tổng Hessian H")
    axes[2].set_title("Cùng các bin đó: H = tổng p(1 − p) trước cây; đây là thống kê, không phải đặc trưng mới", loc="left", fontsize=11)
    axes[2].set_xticks(zoom.bin_id, zoom_labels, fontsize=9)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.17)
        axis.set_axisbelow(True)
    for axis in axes[1:]:
        axis.axvline(split_bin + 0.5, color="#bd472f", linestyle="--", linewidth=1.5)
    figure.text(
        0.5, 0.022,
        "Khoảng giá trị ghi min–max QUAN SÁT trong bin, không phải toàn bộ biên bin nội bộ.\n"
        "Bin ID là dữ liệu native; G/H tái tính theo objective binary của vòng này bằng float32.",
        ha="center", fontsize=10, color="#47535e",
    )
    figure.subplots_adjust(top=0.89, bottom=0.10, left=0.09, right=0.98, hspace=0.62)
    figure.savefig(output / f"{file_stem}.png", dpi=180, facecolor="white")
    figure.savefig(output / f"{file_stem}.svg", facecolor="white")
    plt.close(figure)


def draw_path(feature_names, leaves, splits, leaf_record, initial_score, output):
    decisions = leaves[int(leaf_record.leaf_index)]["path"]
    figure, axis = plt.subplots(figsize=(11, 2.0 + 1.5 * len(decisions)))
    axis.set_xlim(0, 1)
    axis.set_ylim(len(decisions) + 1, -0.8)
    axis.axis("off")
    for position, (split_index, goes_left) in enumerate(decisions):
        node = splits[split_index]
        feature_name = short_name(feature_names[node["split_feature"]])
        relation = "≤" if goes_left else ">"
        label = f"{feature_name} {relation} {format_threshold(node['threshold'])}\nĐi theo nhánh {'trái' if goes_left else 'phải'}"
        axis.text(0.5, position, label, ha="center", va="center", fontsize=12,
                  bbox={"boxstyle": "round,pad=0.6", "facecolor": "#e8f1fb", "edgecolor": "#366caa"})
        axis.annotate("", xy=(0.5, position + 0.66), xytext=(0.5, position + 0.30),
                      arrowprops={"arrowstyle": "->", "color": "#c77800", "lw": 2})
    axis.text(
        0.5, len(decisions),
        f"LÁ {int(leaf_record.leaf_index)} · {int(leaf_record['count']):,} dòng train\n"
        f"T₁(x) = {leaf_record.T1:+.6f}\nΔF = 0,055 × T₁(x) = {leaf_record.delta_F:+.6f}\n"
        f"F₁ = {initial_score:+.6f} + ({leaf_record.delta_F:+.6f}) = {leaf_record.F1:+.6f}\n"
        f"p₁ = {leaf_record.p1:.4%}",
        ha="center", va="center", fontsize=12,
        bbox={"boxstyle": "round,pad=0.7", "facecolor": "#fff1d6", "edgecolor": "#c77800"},
    )
    figure.suptitle("MỘT ĐƯỜNG ĐI TRONG CÂY 1", fontsize=17, fontweight="bold", y=0.98)
    figure.text(0.5, 0.015, "Đây là p sau cây 1; dự báo cuối vẫn phải tổng hợp đủ 80 cây.", ha="center", fontsize=10)
    figure.subplots_adjust(top=0.9, bottom=0.065)
    figure.savefig(output / "first_tree_actual_path.png", dpi=180, facecolor="white")
    plt.close(figure)


def run(source_root, output):
    output.mkdir(parents=True, exist_ok=True)
    artifact_path = source_root / "apps/backend/model_store/model_hco_vnls_lightgbm_cutoff75.joblib"
    dataset_path = source_root / "CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_75.csv"
    artifact = joblib.load(artifact_path)
    frame = pd.read_csv(dataset_path)
    train = frame.loc[frame["split"] == "train"].copy()
    validation = frame.loc[frame["split"] == "validation"].copy()
    selected = artifact["feature_columns"]
    pipeline = clone(artifact["pipeline"])
    pipeline.fit(train[selected], train["risk"])
    estimator = pipeline.named_steps["model"]
    booster = estimator.booster_
    transformed = pipeline.named_steps["preprocess"].transform(train[selected])
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out().tolist()
    validation_probability = pipeline.predict_proba(validation[selected])[:, 1]
    matrix = confusion_matrix(validation["risk"], validation_probability >= 0.5)
    average_precision = average_precision_score(validation["risk"], validation_probability)
    np.testing.assert_array_equal(matrix, [[2180, 68], [362, 805]])
    np.testing.assert_allclose(average_precision, 0.8967566497124569, rtol=0, atol=1e-12)
    if transformed.shape != (16297, 30):
        raise ValueError(f"Unexpected transformed shape {transformed.shape}")
    num_positive = int(train["risk"].sum())
    num_negative = len(train) - num_positive
    initial_probability = num_positive / len(train)
    initial_score = math.log(num_positive / num_negative)
    labels = train["risk"].to_numpy(dtype=np.int32)
    gradients = (initial_probability - labels).astype(np.float32)
    hessians = np.full(len(train), initial_probability * (1 - initial_probability), dtype=np.float32)
    model_dump = booster.dump_model()
    (output / "train_only_model_dump.json").write_text(json.dumps(model_dump, ensure_ascii=False, indent=2), encoding="utf-8")
    booster.save_model(str(output / "train_only_lightgbm.txt"))
    native_dataset = lgb.Dataset(transformed, label=labels, params=booster.params, free_raw_data=False)
    native_dataset.construct()
    native_bin_path = output / "dataset_bins_debug.txt"
    native_dataset._dump_text(native_bin_path)
    bins = read_native_bins(native_bin_path, transformed.shape[1], len(train))
    first_tree = model_dump["tree_info"][0]
    root = first_tree["tree_structure"]
    root_feature_index = root["split_feature"]
    root_feature_name = short_name(feature_names[root_feature_index])
    values = transformed[:, root_feature_index]
    root_bins = bins[:, root_feature_index]
    left_mask = values <= root["threshold"]
    split_bin = int(root_bins[left_mask].max())
    if not np.array_equal(left_mask, root_bins <= split_bin):
        raise ValueError("Native bins do not reproduce trained root split")
    histogram_frame = pd.DataFrame({
        "bin_id": root_bins, "value": values, "risk": labels,
        "gradient": gradients.astype(np.float64), "hessian": hessians.astype(np.float64),
    })
    histogram = histogram_frame.groupby("bin_id", as_index=False).agg(
        value_min=("value", "min"), value_max=("value", "max"),
        count=("risk", "size"), risk_1=("risk", "sum"),
        sum_gradient=("gradient", "sum"), sum_hessian=("hessian", "sum"),
    )
    histogram["risk_0"] = histogram["count"] - histogram["risk_1"]
    histogram.to_csv(output / "histogram_root_feature.csv", index=False, encoding="utf-8-sig")
    leaf_indices = booster.predict(transformed, pred_leaf=True, num_iteration=1).reshape(-1).astype(int)
    score_after_first = booster.predict(transformed, raw_score=True, num_iteration=1)
    leaves, splits = {}, {}
    walk_tree(root, leaves, splits)
    learning_rate = estimator.get_params()["learning_rate"]
    leaf_rows = []
    for leaf_index, leaf in sorted(leaves.items()):
        mask = leaf_indices == leaf_index
        leaf_value = leaf["node"]["leaf_value"]
        delta_score = leaf_value - initial_score
        tree_output = delta_score / learning_rate
        sum_gradient = float(gradients[mask].astype(np.float64).sum())
        sum_hessian = float(hessians[mask].astype(np.float64).sum())
        np.testing.assert_allclose(tree_output, -sum_gradient / sum_hessian, rtol=1e-6, atol=1e-6)
        if int(mask.sum()) != leaf["node"]["leaf_count"]:
            raise ValueError("Leaf counts do not match native predictions")
        leaf_rows.append({
            "leaf_index": leaf_index, "count": int(mask.sum()), "risk_1": int(labels[mask].sum()),
            "sum_gradient": sum_gradient, "sum_hessian": sum_hessian,
            "T1": tree_output, "delta_F": delta_score, "F1": leaf_value, "p1": float(sigmoid(leaf_value)),
        })
    leaf_table = pd.DataFrame(leaf_rows)
    leaf_table.to_csv(output / "first_tree_leaves.csv", index=False, encoding="utf-8-sig")
    leaf_lookup = leaf_table.set_index("leaf_index")
    np.testing.assert_allclose(score_after_first, leaf_lookup.loc[leaf_indices, "F1"].to_numpy(), rtol=0, atol=1e-12)
    training_rows = train[["id_student", "code_module", "code_presentation", "risk", *[column for column in selected if column != "code_module"]]].copy()
    training_rows.insert(0, "source_row_index", train.index)
    training_rows["p0"] = initial_probability
    training_rows["gradient_round1"] = gradients
    training_rows["hessian_round1"] = hessians
    training_rows["root_feature_bin_id"] = root_bins
    training_rows["leaf_index_round1"] = leaf_indices
    training_rows["T1"] = leaf_lookup.loc[leaf_indices, "T1"].to_numpy()
    training_rows["delta_F1"] = score_after_first - initial_score
    training_rows["F1"] = score_after_first
    training_rows["p1"] = sigmoid(score_after_first)
    training_rows.to_csv(output / "training_rows_round1.csv", index=False, encoding="utf-8-sig")
    highlighted_leaf = int(leaf_table.loc[leaf_table.T1.idxmax(), "leaf_index"])
    leaf_record = leaf_table.loc[leaf_table.leaf_index == highlighted_leaf].iloc[0]
    draw_tree(first_tree, feature_names, leaf_table, highlighted_leaf, output)
    draw_histogram(histogram, split_bin, root["threshold"], root_feature_name, output)
    draw_path(feature_names, leaves, splits, leaf_record, initial_score, output)
    split_rows = [{
        "split_index": node["split_index"], "feature": short_name(feature_names[node["split_feature"]]),
        "threshold": node["threshold"], "count": node["internal_count"], "gain": node["split_gain"],
    } for node in splits.values()]
    pd.DataFrame(split_rows).to_csv(output / "first_tree_splits.csv", index=False, encoding="utf-8-sig")
    summary = {
        "source_root": str(source_root), "source_artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "source_dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "policy": "Clone original pipeline and refit train-only. Original artifacts are not modified.",
        "versions": {"lightgbm": lgb.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "train_rows": len(train), "risk_1": num_positive, "risk_0": num_negative,
        "initial_probability": initial_probability, "F0": initial_score,
        "gradient_for_label_1": float(gradients[labels == 1][0]),
        "gradient_for_label_0": float(gradients[labels == 0][0]), "hessian_round1": float(hessians[0]),
        "feature_names": feature_names, "learning_rate": learning_rate,
        "num_trees": booster.num_trees(), "leaves_per_tree": [tree["num_leaves"] for tree in model_dump["tree_info"]],
        "root_split_feature": root_feature_name, "root_split_threshold": root["threshold"],
        "root_split_bin_id": split_bin, "root_feature_num_bins": native_dataset.feature_num_bin(root_feature_index),
        "highlighted_leaf": leaf_record.to_dict(), "first_tree_splits": split_rows,
        "validation_confusion_matrix": matrix.tolist(), "validation_AP": average_precision,
        "root_histogram_bin_source": "Native Dataset._dump_text using transformed train and Booster params.",
        "histogram_bounds_note": "Min/max are observed values per native bin, not full internal mapper boundaries.",
        "first_tree_leaf_note": "First-tree leaf_value includes F0 and learning rate. T1=(leaf_value-F0)/learning_rate.",
        "checks": ["Original validation metrics reproduced", "Native bins reproduce root split", "Leaf counts match traversal", "Leaf T1 matches -G/H", "Leaf values reproduce one-tree raw prediction"],
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = (
        "# Vòng huấn luyện đầu của LightGBM\n\n"
        "Bản train-only của sơ đồ cutoff 75%, không phải bản train + validation của ứng dụng.\n\n"
        f"Train: {len(train)} dòng; p0={initial_probability:.12f}; F0={initial_score:.12f}.\n\n"
        "Cây: first_tree_full.png và .svg. Đường đi: first_tree_actual_path.png.\n"
        "Histogram: histogram_root_feature.png và .svg; toàn bộ bin trong histogram_root_feature.csv.\n"
        "Mỗi dòng: training_rows_round1.csv. Mỗi lá: first_tree_leaves.csv.\n"
        "Bin ID native: dataset_bins_debug.txt. Nguồn và kiểm chứng: summary.json.\n\n"
        "G/H tái dựng theo binary objective vòng 1 bằng float32; min/max bin là giá trị quan sát.\n"
        "T1 là đầu ra trước learning rate; delta_F=0.055*T1. Cây đầu gộp F0 vào leaf_value.\n"
        "p1 là xác suất sau cây đầu, không phải dự báo cuối. Ma trận validation và AP đã tái hiện đúng.\n\n"
        "Chạy inspect_training.py bằng Python trong apps/backend/.venv; truyền --source-root và --output.\n"
    )
    (output / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    arguments = parser.parse_args()
    run(arguments.source_root, arguments.output)
