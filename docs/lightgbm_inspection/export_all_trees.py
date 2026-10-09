from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import textwrap
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, log_loss

from inspect_training import (
    FancyArrowPatch, draw_histogram, format_threshold, plt, read_native_bins,
    short_name, sigmoid, tree_layout, walk_tree,
)


def render_tree(tree, feature_names, leaf_table, tree_number, output):
    positions = {}
    tree_layout(tree["tree_structure"], positions)
    depth = max(position[0] for position in positions.values())
    leaves, splits = {}, {}
    walk_tree(tree["tree_structure"], leaves, splits)
    strongest_leaf = int(leaf_table.loc[leaf_table.delta_F.abs().idxmax(), "leaf_index"])
    emphasized_path = set(leaves[strongest_leaf]["path"])
    leaf_lookup = leaf_table.set_index("leaf_index")
    figure, axis = plt.subplots(figsize=(max(21, 3.7 * (depth + 1)), 14))
    axis.set_xlim(-0.7, depth + 0.75)
    axis.set_ylim(tree["num_leaves"] - 0.3, -0.8)
    axis.axis("off")

    def render_node(node):
        is_leaf = "leaf_index" in node
        key = ("leaf", node["leaf_index"]) if is_leaf else ("split", node["split_index"])
        horizontal, vertical = positions[key]
        if is_leaf:
            record = leaf_lookup.loc[node["leaf_index"]]
            label = (
                f"Lá {node['leaf_index']} · n={node['leaf_count']:,}\n"
                f"T{tree_number}={record['T']:+.5f}\nΔF={record.delta_F:+.5f}\n"
                f"p TB: {record.p_before_mean:.2%} → {record.p_after_mean:.2%}"
            )
            emphasized = node["leaf_index"] == strongest_leaf
            fill = "#fff1d6" if emphasized else "#e7f3ec" if record.delta_F >= 0 else "#f4eaf0"
            border = "#c77800" if emphasized else "#44836a" if record.delta_F >= 0 else "#986478"
        else:
            feature = short_name(feature_names[node["split_feature"]])
            feature = "\n".join(textwrap.wrap(feature, width=26))
            label = f"Nút {node['split_index']}\n{feature}\n≤ {format_threshold(node['threshold'])}?\nn={node['internal_count']:,}"
            fill, border = "#e8f1fb", "#366caa"
            for goes_left, child in ((True, node["left_child"]), (False, node["right_child"])):
                child_key = ("leaf", child["leaf_index"]) if "leaf_index" in child else ("split", child["split_index"])
                child_horizontal, child_vertical = positions[child_key]
                emphasized = (node["split_index"], goes_left) in emphasized_path
                color = "#c77800" if emphasized else "#9cabb7"
                axis.add_patch(FancyArrowPatch(
                    (horizontal + 0.37, vertical), (child_horizontal - 0.37, child_vertical),
                    arrowstyle="-|>", mutation_scale=12, linewidth=2 if emphasized else 1, color=color,
                ))
                axis.text(
                    horizontal + 0.51, vertical + (child_vertical - vertical) * 0.18,
                    "Có (≤)" if goes_left else "Không (>)", fontsize=7.5,
                    color=color, ha="center", va="center",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
                )
                render_node(child)
        axis.text(
            horizontal, vertical, label, ha="center", va="center", fontsize=9,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": fill, "edgecolor": border, "linewidth": 1.3},
            zorder=2,
        )

    render_node(tree["tree_structure"])
    figure.suptitle(f"CÂY {tree_number} · LIGHTGBM TRAIN-ONLY · CUTOFF 75%", fontsize=19, fontweight="bold", y=0.985)
    figure.text(0.5, 0.949, f"16.297 dòng train · 30 cột sau tiền xử lý · {tree['num_leaves']} lá · đường cam: lá có |ΔF| lớn nhất", ha="center", fontsize=12)
    figure.text(
        0.5, 0.017,
        f"T{tree_number}: đầu ra trước learning rate · ΔF = 0,055 × T{tree_number} · F sau = F trước + ΔF\n"
        "p TB là TRUNG BÌNH xác suất của các dòng trong lá; không phải mọi dòng có cùng p. "
        "Giá trị cây đã học không được sửa khi học cây tiếp theo.", ha="center", fontsize=10,
    )
    figure.subplots_adjust(top=0.91, bottom=0.075, left=0.015, right=0.99)
    figure.savefig(output / f"cay_{tree_number}.png", dpi=160, facecolor="white")
    figure.savefig(output / f"cay_{tree_number}.svg", facecolor="white")
    plt.close(figure)


def histogram_for_node(indices, feature_index, node_index, threshold, features, bins, labels, gradients, hessians, feature_names):
    rows = pd.DataFrame({
        "bin_id": bins[indices, feature_index], "value": features[indices, feature_index],
        "risk": labels[indices], "gradient": gradients[indices].astype(np.float64),
        "hessian": hessians[indices].astype(np.float64),
    })
    table = rows.groupby("bin_id", as_index=False).agg(
        value_min=("value", "min"), value_max=("value", "max"), count=("risk", "size"),
        risk_1=("risk", "sum"), sum_gradient=("gradient", "sum"), sum_hessian=("hessian", "sum"),
    )
    table["risk_0"] = table["count"] - table["risk_1"]
    table.insert(0, "feature", short_name(feature_names[feature_index]))
    table.insert(0, "node_index", node_index)
    table["threshold"] = threshold
    table["side"] = np.where(table.value_max <= threshold, "left", "right")
    if ((table.value_min <= threshold) & (table.value_max > threshold)).any():
        raise ValueError("A native bin crosses the trained threshold")
    return table


def inspect_nodes(tree, features, bins, labels, gradients, hessians, scores_before, scores_after, feature_names):
    node_rows, histograms = [], []
    probabilities_before, probabilities_after = sigmoid(scores_before), sigmoid(scores_after)

    def inspect_node(node, indices, parent_id="", edge="root"):
        is_leaf = "leaf_index" in node
        identifier = f"la_{node['leaf_index']}" if is_leaf else f"nut_{node['split_index']}"
        expected_count = node["leaf_count"] if is_leaf else node["internal_count"]
        if len(indices) != expected_count:
            raise ValueError(f"Traversal count mismatch at {identifier}")
        node_rows.append({
            "node_id": identifier, "parent_id": parent_id, "edge": edge,
            "kind": "leaf" if is_leaf else "split", "n": len(indices),
            "feature": "" if is_leaf else short_name(feature_names[node["split_feature"]]),
            "threshold": None if is_leaf else node["threshold"],
            "split_gain": None if is_leaf else node["split_gain"],
            "sum_gradient": float(gradients[indices].astype(np.float64).sum()),
            "sum_hessian": float(hessians[indices].astype(np.float64).sum()),
            "risk_1": int(labels[indices].sum()), "risk_0": int(len(indices) - labels[indices].sum()),
            "F_before_mean": float(scores_before[indices].mean()), "F_after_mean": float(scores_after[indices].mean()),
            "p_before_mean": float(probabilities_before[indices].mean()), "p_after_mean": float(probabilities_after[indices].mean()),
        })
        if is_leaf:
            return
        feature_index = node["split_feature"]
        histograms.append(histogram_for_node(
            indices, feature_index, node["split_index"], node["threshold"], features, bins,
            labels, gradients, hessians, feature_names,
        ))
        left_mask = features[indices, feature_index] <= node["threshold"]
        inspect_node(node["left_child"], indices[left_mask], identifier, "left")
        inspect_node(node["right_child"], indices[~left_mask], identifier, "right")

    inspect_node(tree["tree_structure"], np.arange(len(labels)))
    return pd.DataFrame(node_rows), pd.concat(histograms, ignore_index=True)


def metric_row(tree_number, labels, scores, validation_labels, validation_scores):
    probability, validation_probability = sigmoid(scores), sigmoid(validation_scores)
    return {
        "tree_number": tree_number,
        "train_log_loss": log_loss(labels, probability, labels=[0, 1]),
        "validation_log_loss": log_loss(validation_labels, validation_probability, labels=[0, 1]),
        "train_accuracy_at_0_5": accuracy_score(labels, probability >= 0.5),
        "validation_accuracy_at_0_5": accuracy_score(validation_labels, validation_probability >= 0.5),
        "train_AP": average_precision_score(labels, probability),
        "validation_AP": average_precision_score(validation_labels, validation_probability),
    }


def render_curves(metrics, output):
    figure, axes = plt.subplots(1, 3, figsize=(17, 5))
    for axis, suffix, title in zip(axes, ["log_loss", "accuracy_at_0_5", "AP"], ["Log-loss: thấp hơn tốt hơn", "Accuracy tại ngưỡng 0,5", "Average Precision"]):
        axis.plot(metrics.tree_number, metrics[f"train_{suffix}"], label="Train", color="#366caa")
        axis.plot(metrics.tree_number, metrics[f"validation_{suffix}"], label="Validation", color="#c77800")
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("Số cây đã dùng")
        axis.grid(alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(frameon=False)
    figure.suptitle("CHỈ SỐ THEO SỐ CÂY · KHÔNG DÙNG TEST ĐỂ VẼ", fontsize=16, fontweight="bold")
    figure.text(0.5, 0.01, "Cây 0 là mức nền. Validation chỉ để đối chiếu, không dùng sửa cây hoặc tự chọn lại cấu hình.", ha="center", fontsize=10)
    figure.tight_layout(rect=(0, 0.055, 1, 0.93))
    figure.savefig(output / "chi_so_theo_so_cay.png", dpi=170, facecolor="white")
    plt.close(figure)


def write_gallery(output, manifest):
    sections = []
    for record in manifest:
        number = record["tree_number"]
        summary = html.escape(f"Cây {number} · {record['num_leaves']} lá · gốc: {record['root_feature']} ≤ {format_threshold(record['root_threshold'])}")
        sections.append(
            f'<details><summary>{summary}</summary><p>'
            f'<a href="anh_cay/cay_{number}.svg">Ảnh vector</a> · '
            f'<a href="anh_bin/cay_{number}_bin_goc.png">Histogram gốc</a> · '
            f'<a href="du_lieu/cay_{number}_nut.csv">Nút</a> · '
            f'<a href="du_lieu/cay_{number}_la.csv">Lá</a> · '
            f'<a href="du_lieu/cay_{number}_bin.csv">Bin ở từng nút</a> · '
            f'<a href="du_lieu/cay_{number}_dong.csv.gz">Từng dòng (CSV nén)</a></p>'
            f'<img loading="lazy" src="anh_cay/cay_{number}.png" alt="Cây {number}"></details>'
        )
    page = (
        '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>80 cây LightGBM — cutoff 75%</title><style>'
        'body{font:16px/1.6 system-ui,sans-serif;max-width:1600px;margin:28px auto;padding:0 18px;color:#22313d}'
        'details{border:1px solid #ccd6dd;border-radius:8px;margin:12px 0;padding:12px}'
        'summary{cursor:pointer;font-weight:650}img{width:100%;height:auto}a{color:#235f96}'
        '</style><h1>80 cây LightGBM — train-only, cutoff 75%</h1>'
        '<p>Mở từng cây để xem ảnh và tệp đối chiếu. n là số dòng train qua nút hoặc lá. '
        'T là đóng góp trước learning rate; ΔF là phần cộng vào điểm; p TB là trung bình xác suất trong lá.</p>'
        '<p><a href="chi_so_theo_so_cay.csv">Chỉ số theo số cây</a> · '
        '<a href="vi_du_10_dong_qua_80_cay.csv">10 dòng qua 80 cây</a> · <a href="README.md">Hướng dẫn tệp</a></p>'
        '<img src="chi_so_theo_so_cay.png" alt="Chỉ số train và validation theo số cây">'
        + ''.join(sections) + '</html>'
    )
    (output / "muc_luc.html").write_text(page, encoding="utf-8")


def export(source_root, output):
    image_directory, histogram_directory = output / "anh_cay", output / "anh_bin"
    data_directory, common_directory = output / "du_lieu", output / "du_lieu_chung"
    for directory in [output, image_directory, histogram_directory, data_directory, common_directory]:
        directory.mkdir(parents=True, exist_ok=True)
    artifact_path = source_root / "apps/backend/model_store/model_hco_vnls_lightgbm_cutoff75.joblib"
    data_path = source_root / "CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_75.csv"
    artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    artifact = joblib.load(artifact_path)
    frame = pd.read_csv(data_path)
    train, validation = frame.loc[frame.split == "train"], frame.loc[frame.split == "validation"]
    selected = artifact["feature_columns"]
    pipeline = clone(artifact["pipeline"])
    pipeline.fit(train[selected], train.risk)
    estimator, preprocess = pipeline.named_steps["model"], pipeline.named_steps["preprocess"]
    booster = estimator.booster_
    features, validation_features = preprocess.transform(train[selected]), preprocess.transform(validation[selected])
    feature_names = preprocess.get_feature_names_out().tolist()
    labels, validation_labels = train.risk.to_numpy(dtype=int), validation.risk.to_numpy(dtype=int)
    if features.shape != (16297, 30) or booster.num_trees() != 80 or not np.isfinite(features).all():
        raise ValueError("Unexpected training data or tree count")
    model_dump = booster.dump_model()
    if any(tree["num_leaves"] != 15 for tree in model_dump["tree_info"]):
        raise ValueError("Expected 15 leaves in every tree")
    native_dataset = lgb.Dataset(features, label=labels, params=booster.params, free_raw_data=False)
    native_dataset.construct()._dump_text(common_directory / "bin_id_native.txt")
    bins = read_native_bins(common_directory / "bin_id_native.txt", features.shape[1], len(train))
    metadata_columns = ["id_student", "code_module", "code_presentation", "risk", *[column for column in selected if column != "code_module"]]
    raw_rows = train[metadata_columns].copy()
    raw_rows.insert(0, "source_row_index", train.index)
    raw_rows.insert(0, "row_id", np.arange(len(train)))
    raw_rows.to_csv(common_directory / "dac_trung_goc_train.csv.gz", index=False, encoding="utf-8-sig", compression="gzip")
    transformed_rows = pd.DataFrame(features, columns=[short_name(name) for name in feature_names])
    transformed_rows.insert(0, "row_id", np.arange(len(train)))
    transformed_rows.to_csv(common_directory / "dac_trung_30_cot.csv.gz", index=False, encoding="utf-8-sig", compression="gzip")
    bin_rows = pd.DataFrame(bins, columns=[short_name(name) for name in feature_names])
    bin_rows.insert(0, "row_id", np.arange(len(train)))
    bin_rows.to_csv(common_directory / "bin_id_tung_dong.csv.gz", index=False, encoding="utf-8-sig", compression="gzip")
    global_bins = []
    for feature_index, feature_name in enumerate(feature_names):
        table = pd.DataFrame({"bin_id": bins[:, feature_index], "value": features[:, feature_index]})
        table = table.groupby("bin_id", as_index=False).agg(value_min=("value", "min"), value_max=("value", "max"), n=("value", "size"))
        table.insert(0, "feature", short_name(feature_name))
        table.insert(0, "feature_index", feature_index)
        global_bins.append(table)
    pd.concat(global_bins, ignore_index=True).to_csv(common_directory / "bang_bin_30_cot.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"feature_index": np.arange(len(feature_names)), "pipeline_name": feature_names, "feature": [short_name(name) for name in feature_names]}).to_csv(common_directory / "ten_30_cot.csv", index=False, encoding="utf-8-sig")
    leaf_indices = booster.predict(features, pred_leaf=True, num_threads=4)
    validation_leaf_indices = booster.predict(validation_features, pred_leaf=True, num_threads=4)
    initial_probability = float(labels.mean())
    initial_score = math.log(initial_probability / (1 - initial_probability))
    scores, validation_scores = np.full(len(train), initial_score), np.full(len(validation), initial_score)
    learning_rate = estimator.get_params()["learning_rate"]
    example_indices = np.concatenate([np.flatnonzero(labels == 0)[:5], np.flatnonzero(labels == 1)[:5]])
    metrics = [metric_row(0, labels, scores, validation_labels, validation_scores)]
    manifest, examples, max_newton_error = [], [], 0.0

    for tree_number, tree in enumerate(model_dump["tree_info"], start=1):
        scores_before = scores.copy()
        probability_before = sigmoid(scores_before)
        gradients = (probability_before - labels).astype(np.float32)
        hessians = (probability_before * (1 - probability_before)).astype(np.float32)
        leaves, splits = {}, {}
        walk_tree(tree["tree_structure"], leaves, splits)
        contributions = np.empty(tree["num_leaves"])
        for leaf_index, leaf in leaves.items():
            contributions[leaf_index] = leaf["node"]["leaf_value"] - (initial_score if tree_number == 1 else 0)
        current_leaves = leaf_indices[:, tree_number - 1].astype(int)
        delta_scores = contributions[current_leaves]
        scores = scores_before + delta_scores
        validation_scores += contributions[validation_leaf_indices[:, tree_number - 1].astype(int)]
        probability_after = sigmoid(scores)
        leaf_records = []
        for leaf_index, leaf in sorted(leaves.items()):
            mask = current_leaves == leaf_index
            count = int(mask.sum())
            if count != leaf["node"]["leaf_count"]:
                raise ValueError(f"Leaf count mismatch in tree {tree_number}")
            sum_gradient = float(gradients[mask].astype(np.float64).sum())
            sum_hessian = float(hessians[mask].astype(np.float64).sum())
            tree_output = contributions[leaf_index] / learning_rate
            newton_output = -sum_gradient / sum_hessian
            np.testing.assert_allclose(tree_output, newton_output, rtol=5e-6, atol=2e-6)
            max_newton_error = max(max_newton_error, abs(tree_output - newton_output))
            leaf_records.append({
                "tree_number": tree_number, "leaf_index": leaf_index, "n": count,
                "risk_1": int(labels[mask].sum()), "risk_0": int(count - labels[mask].sum()),
                "sum_gradient": sum_gradient, "sum_hessian": sum_hessian,
                "T": tree_output, "delta_F": contributions[leaf_index],
                "native_leaf_value": leaf["node"]["leaf_value"],
                "F_before_mean": float(scores_before[mask].mean()), "F_after_mean": float(scores[mask].mean()),
                "p_before_mean": float(probability_before[mask].mean()), "p_after_mean": float(probability_after[mask].mean()),
                "p_before_min": float(probability_before[mask].min()), "p_before_max": float(probability_before[mask].max()),
                "p_after_min": float(probability_after[mask].min()), "p_after_max": float(probability_after[mask].max()),
            })
        leaf_table = pd.DataFrame(leaf_records)
        nodes, histograms = inspect_nodes(tree, features, bins, labels, gradients, hessians, scores_before, scores, feature_names)
        nodes.insert(0, "tree_number", tree_number)
        histograms.insert(0, "tree_number", tree_number)
        leaf_table.to_csv(data_directory / f"cay_{tree_number}_la.csv", index=False, encoding="utf-8-sig")
        nodes.to_csv(data_directory / f"cay_{tree_number}_nut.csv", index=False, encoding="utf-8-sig")
        histograms.to_csv(data_directory / f"cay_{tree_number}_bin.csv", index=False, encoding="utf-8-sig")
        (data_directory / f"cay_{tree_number}_cau_truc.json").write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
        row_table = pd.DataFrame({
            "row_id": np.arange(len(train)), "risk": labels, "F_before": scores_before,
            "p_before": probability_before, "gradient": gradients, "hessian": hessians,
            "leaf_index": current_leaves, "T": delta_scores / learning_rate, "delta_F": delta_scores,
            "F_after": scores, "p_after": probability_after,
        })
        row_table.to_csv(data_directory / f"cay_{tree_number}_dong.csv.gz", index=False, encoding="utf-8-sig", compression="gzip")
        example_table = row_table.iloc[example_indices].copy()
        example_table.insert(0, "tree_number", tree_number)
        examples.append(example_table)
        render_tree(tree, feature_names, leaf_table, tree_number, image_directory)
        root = tree["tree_structure"]
        root_histogram = histograms.loc[histograms.node_index == root["split_index"]].copy()
        split_bin = int(root_histogram.loc[root_histogram.side == "left", "bin_id"].max())
        draw_histogram(root_histogram, split_bin, root["threshold"], short_name(feature_names[root["split_feature"]]), histogram_directory, tree_number=tree_number, file_stem=f"cay_{tree_number}_bin_goc")
        record = {
            "tree_number": tree_number, "num_leaves": tree["num_leaves"],
            "root_feature": short_name(feature_names[root["split_feature"]]), "root_threshold": root["threshold"],
            "max_depth": None, "leaf_updates_positive": int((leaf_table.delta_F > 0).sum()),
            "leaf_updates_negative": int((leaf_table.delta_F < 0).sum()),
            "png": f"anh_cay/cay_{tree_number}.png", "bins": f"du_lieu/cay_{tree_number}_bin.csv",
        }
        positions = {}
        tree_layout(root, positions)
        record["max_depth"] = max(position[0] for position in positions.values())
        manifest.append(record)
        metrics.append(metric_row(tree_number, labels, scores, validation_labels, validation_scores))
        if tree_number in [1, 2, 40, 80]:
            np.testing.assert_allclose(scores, booster.predict(features, raw_score=True, num_iteration=tree_number, num_threads=4), rtol=0, atol=1e-12)
            np.testing.assert_allclose(validation_scores, booster.predict(validation_features, raw_score=True, num_iteration=tree_number, num_threads=4), rtol=0, atol=1e-12)
        if tree_number % 10 == 0 or tree_number == 1:
            print(f"Exported {tree_number}/80 trees", flush=True)

    metric_table = pd.DataFrame(metrics)
    metric_table.to_csv(output / "chi_so_theo_so_cay.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(manifest).to_csv(output / "danh_sach_80_cay.csv", index=False, encoding="utf-8-sig")
    pd.concat(examples, ignore_index=True).to_csv(output / "vi_du_10_dong_qua_80_cay.csv", index=False, encoding="utf-8-sig")
    render_curves(metric_table, output)
    write_gallery(output, manifest)
    matrix = confusion_matrix(validation_labels, sigmoid(validation_scores) >= 0.5)
    np.testing.assert_array_equal(matrix, [[2180, 68], [362, 805]])
    np.testing.assert_allclose(average_precision_score(validation_labels, sigmoid(validation_scores)), 0.8967566497124569, atol=1e-12, rtol=0)
    if hashlib.sha256(artifact_path.read_bytes()).hexdigest() != artifact_hash:
        raise ValueError("Original artifact was unexpectedly modified")
    expected_files = []
    for tree_number in range(1, 81):
        expected_files.extend([
            image_directory / f"cay_{tree_number}.png", image_directory / f"cay_{tree_number}.svg",
            histogram_directory / f"cay_{tree_number}_bin_goc.png", histogram_directory / f"cay_{tree_number}_bin_goc.svg",
            *[data_directory / f"cay_{tree_number}_{suffix}.csv" for suffix in ["nut", "la", "bin"]],
            data_directory / f"cay_{tree_number}_dong.csv.gz", data_directory / f"cay_{tree_number}_cau_truc.json",
        ])
    if not all(path.is_file() and path.stat().st_size > 0 for path in expected_files):
        raise ValueError("Missing output files")
    check_leaf_counts = [pd.read_csv(data_directory / f"cay_{number}_la.csv")["n"].sum() for number in range(1, 81)]
    if any(count != len(train) for count in check_leaf_counts):
        raise ValueError("Exported leaf counts do not sum to training row count")
    summary = {
        "output_directory": str(output.resolve()), "num_trees": 80, "leaves_per_tree": 15,
        "train_rows": len(train), "validation_rows": len(validation), "F0": initial_score,
        "initial_probability": initial_probability, "learning_rate": learning_rate,
        "source_artifact_sha256": artifact_hash, "source_dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "model_policy": "Refit original configuration on train only; validation used only for diagnostics; test labels not used.",
        "max_leaf_newton_reconstruction_error": max_newton_error,
        "validation_confusion_matrix": matrix.tolist(), "validation_AP": float(metric_table.iloc[-1].validation_AP),
        "best_observed_validation_AP_tree": int(metric_table.loc[metric_table.validation_AP.idxmax(), "tree_number"]),
        "best_observed_validation_AP": float(metric_table.validation_AP.max()),
        "best_observed_validation_accuracy_tree": int(metric_table.loc[metric_table.validation_accuracy_at_0_5.idxmax(), "tree_number"]),
        "validation_AP_decrease_steps": int((metric_table.validation_AP.diff() < 0).sum()),
        "validation_accuracy_decrease_steps": int((metric_table.validation_accuracy_at_0_5.diff() < 0).sum()),
        "checked_tree_files": len(expected_files), "training_row_ids": "0-based row_id in common data; source_row_index links original cutoff CSV",
        "histogram_scope": "Each split node exports histogram for its selected feature over exactly the rows visiting that node.",
        "bin_bounds": "Native bin IDs; min/max are observed values, not full internal mapper boundaries.",
        "gradients": "Recomputed from scores before each tree, cast to float32; verified against all 1200 native leaf outputs.",
        "leaf_probability": "p_before_mean/p_after_mean are means of individual probabilities, not sigmoid(mean F).",
        "versions": {"lightgbm": lgb.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "files_total_bytes": sum(path.stat().st_size for path in output.rglob("*") if path.is_file()),
    }
    (output / "kiem_chung.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    readme = (
        "# Toàn bộ 80 cây LightGBM — cutoff 75%\n\n"
        "Đây là bản train-only khớp sơ đồ validation, không phải model train + validation của ứng dụng.\n\n"
        "## Bắt đầu\n\nMở muc_luc.html để xem từng cây và liên kết dữ liệu.\n\n"
        "- anh_cay/cay_1.png đến cay_80.png, kèm SVG để phóng to.\n"
        "- anh_bin/cay_1_bin_goc.png đến cay_80_bin_goc.png: histogram tại nút gốc từng vòng.\n"
        "- du_lieu/cay_N_nut.csv: mọi nút/lá, n, thuộc tính, ngưỡng, G/H và xác suất trung bình.\n"
        "- du_lieu/cay_N_la.csv: T, delta_F, thống kê và khoảng xác suất ở từng lá.\n"
        "- du_lieu/cay_N_bin.csv: histogram của thuộc tính được chọn tại từng nút chia. Lọc node_index theo ảnh.\n"
        "- du_lieu/cay_N_dong.csv.gz: từng dòng với p/F trước và sau cây, g/h, lá và đóng góp.\n"
        "- du_lieu/cay_N_cau_truc.json: cấu trúc native của từng cây.\n"
        "- du_lieu_chung: đặc trưng gốc/30 cột, bin ID từng dòng, ánh xạ tên cột và min/max bin.\n"
        "- vi_du_10_dong_qua_80_cay.csv: 5 dòng đầu mỗi nhãn qua tất cả cây để dễ đối chiếu.\n"
        "- chi_so_theo_so_cay.csv/.png: train/validation log-loss, Accuracy và AP theo số cây.\n\n"
        "## Ý nghĩa số liệu\n\n"
        "n là số dòng train đến nút/lá của cây đó. T là đầu ra trước learning rate; delta_F=0.055*T.\n"
        "F_after=F_before+delta_F; p_after=sigmoid(F_after). Nhiều dòng cùng lá nhận cùng delta_F, nhưng p có thể khác.\n"
        "Ảnh dùng p TB (trung bình của p từng dòng), không khẳng định một xác suất chung cho lá.\n"
        "Ở cây đầu, native leaf_value gồm F0; ở cây sau, native leaf_value đã nhân learning rate. Không nhân hai lần.\n"
        "Gradient/Hessian được tính TRƯỚC cây tương ứng. Bin ID dùng mapper native chung; G/H thay đổi theo vòng và tập dòng ở nút.\n"
        "Min/max là giá trị quan sát trong bin. Histogram xuất cho thuộc tính được chọn ở mỗi nút, không xuất tất cả ứng viên chưa được chọn.\n"
        "Ghép row_id trong cay_N_dong với dữ liệu chung. Cây 0 ở bảng chỉ số là mức nền, không phải cây thứ 81.\n\n"
        "## CSV nén\n\nCác tệp .csv.gz chứa đầy đủ dòng nhưng được nén để giảm dung lượng. "
        "Có thể giải nén thành CSV hoặc đọc trực tiếp bằng pandas.read_csv(path).\n\n"
        "## Kiểm chứng\n\n720 tệp đối chiếu cây được kiểm tra tồn tại; n của 15 lá cộng thành 16.297 ở mọi cây. "
        "G/H được đối chiếu với toàn bộ 1.200 giá trị lá. Điểm cộng dồn khớp native ở cây 1, 2, 40, 80. "
        "Kết quả validation cuối khớp ma trận [[2180,68],[362,805]] và AP 0.8967566497124569. "
        "Artifact nguồn không bị thay đổi. Chi tiết tại kiem_chung.json.\n\n"
        "## Chạy lại\n\n"
        f"Python: {source_root / 'apps/backend/.venv/Scripts/python.exe'}\n"
        f"Script: {Path(__file__).resolve()}\n"
        f"Tham số: --source-root \"{source_root}\" --output \"{output}\"\n"
    )
    (output / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "toan_bo_80_cay")
    arguments = parser.parse_args()
    export(arguments.source_root, arguments.output)
