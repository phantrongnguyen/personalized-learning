"""Publish aggregate metrics only, leaving enrollment-level outputs inside ignored runs/."""
import argparse
import json
from pathlib import Path
import shutil

import pandas as pd
from storage import resolve_run_file, consolidate_report_copies

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in (".", ".."):
        parser.error("Invalid run ID")
    run = ROOT / "runs" / args.run_id
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed":
        raise RuntimeError("Only completed runs may be published")
    target = ROOT / "reports" / args.run_id
    target.mkdir(parents=True, exist_ok=True)
    provenance = {key: manifest[key] for key in (
        "status", "started_at", "finished_at", "python", "git_commit", "protocol",
        "stages", "source_sha256", "upstream_sha256", "raw_sha256", "environment",
        "output_sha256", "backend_model_sha256_before")}
    (target / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "figures").mkdir(exist_ok=True)
    for relative in manifest["output_sha256"]:
        relative = relative.replace("\\", "/")
        if relative.startswith("figures/") and relative.endswith(".png"):
            figure = resolve_run_file(run, relative)
            destination = target / "figures" / Path(relative).name
            if figure.resolve() != destination.resolve():
                shutil.copy2(figure, destination)
    validation = pd.read_csv(run / "results/hco_vnls_lightgbm_validation.csv")
    history = pd.read_csv(ROOT / "history/results/hco_vnls_lightgbm_validation.csv")
    columns = ["cutoff", "method", "features", "accuracy", "recall_risk", "f1_risk", "average_precision_risk", "roc_auc"]
    comparison = validation[columns].merge(history[columns], on=["cutoff", "method"], suffixes=("_new", "_historical"), validate="one_to_one")
    comparison.to_csv(target / "validation_comparison.csv", index=False)
    all_new = pd.read_csv(run / "results/so_sanh_ba_bo_hoc_50_75.csv")
    all_old = pd.read_csv(ROOT / "history/results/so_sanh_ba_bo_hoc_50_75.csv")
    all_comparison = all_new.merge(all_old, on=["cutoff", "model", "method"], suffixes=("_new", "_historical"), validate="one_to_one")
    all_comparison["delta_ap"] = all_comparison.average_precision_risk_new - all_comparison.average_precision_risk_historical
    all_comparison.to_csv(target / "all_models_comparison.csv", index=False)
    test = json.loads(resolve_run_file(run, "results/test_metrics.json").read_text(encoding="utf-8"))
    (target / "test_metrics.json").write_text(json.dumps(test, indent=2), encoding="utf-8")
    # Explicit allowlist: do not publish split IDs, feature tables, predictions, or notebook outputs.
    for name in ("so_sanh_ba_bo_hoc_50_75.csv", "doi_chung_va_on_dinh_mask.csv", "ablation_hybrid_75_train_cv.csv", "tong_quan_cac_moc.csv"):
        frame = pd.read_csv(run / "results" / name)
        frame.to_csv(target / name, index=False)
    text = [f"# Kết quả tái thực nghiệm — {args.run_id}", "",
            "Pipeline hoàn tất từ dữ liệu thô; giữ cấu hình lịch sử. Test là split OULAD lịch sử, không phải holdout độc lập mới.", "",
            "## LightGBM trên validation", "",
            "| Cutoff | Phương pháp | Đặc trưng | Accuracy | Recall | AP |", "| --- | --- | ---: | ---: | ---: | ---: |"]
    for row in validation.itertuples():
        text.append(f"| {row.cutoff:.0%} | {row.method} | {row.features} | {row.accuracy:.6f} | {row.recall_risk:.6f} | {row.average_precision_risk:.6f} |")
    text += ["", "## Test artifact sau fit train + validation", ""]
    for name in ("accuracy", "precision_risk", "recall_risk", "f1_risk", "average_precision_risk", "roc_auc", "brier_score", "tn", "fp", "fn", "tp"):
        text.append(f"- {name}: {test[name]}")
    text += ["", "## Bằng chứng và giới hạn", "",
             "- Bảng đối chiếu lịch sử: [validation_comparison.csv](validation_comparison.csv).",
             f"- Toàn bộ ba bộ học: [all_models_comparison.csv](all_models_comparison.csv); chênh AP lớn nhất: {all_comparison.delta_ap.abs().max():.12g}.",
             "- Manifest, notebook đã chạy, dữ liệu cấp dòng và artifact nằm trong `packages/ml/runs/" + args.run_id + "/` (Git ignore).",
             "- Mã nguồn và dữ liệu được checksum; môi trường đầy đủ được ghi trong manifest.",
             "- Bản provenance không chứa dữ liệu cấp sinh viên: [provenance.json](provenance.json).",
             "- Hình nghiên cứu tổng hợp được lưu tại [figures/](figures/).",
             "- Không thay model backend; không đánh giá chất lượng gợi ý hay hiệu quả can thiệp.",
             "- Giữ nguyên hạn chế phương pháp: ngân sách 8, cơ sở thuật toán cần đối chiếu và test đã được dùng trong lịch sử nghiên cứu."]
    (target / "README.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    provenance["output_locations"] = consolidate_report_copies(run, target)
    (target / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
