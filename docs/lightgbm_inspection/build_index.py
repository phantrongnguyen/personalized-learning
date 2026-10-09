from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path


def build(root: Path) -> None:
    model = json.loads((root / "train_only_model_dump.json").read_text(encoding="utf-8"))
    rows = []
    for tree_number, tree in enumerate(model["tree_info"], start=1):
        node = tree["tree_structure"]
        feature = html.escape(model["feature_names"][node["split_feature"]])
        threshold = html.escape(str(node["threshold"]))
        links = " · ".join(
            f'<a href="du_lieu/cay_{tree_number}_{suffix}">{label}</a>'
            for suffix, label in (
                ("nut.csv", "Nút"), ("la.csv", "Lá"), ("bin.csv", "Bin"),
                ("dong.csv.gz", "Từng dòng / G-H"), ("cau_truc.json", "Cấu trúc"),
            )
        )
        rows.append(f"<tr><td>Cây {tree_number}</td><td>{tree['num_leaves']}</td><td>{feature} ≤ {threshold}</td><td>{links}</td></tr>")
    document = """<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dữ liệu 80 cây LightGBM</title>
<style>html{color-scheme:light dark}body{font-family:system-ui,sans-serif;margin:2rem;line-height:1.5}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.6rem;border-bottom:1px solid GrayText}img{max-width:100%;height:auto}.scroll{overflow-x:auto}</style>
<h1>Dữ liệu 80 cây LightGBM — bản train-only</h1>
<p>Gói GitHub giữ đầy đủ CSV/CSV.GZ/JSON, không kèm bộ ảnh cây/histogram lớn.</p>
<p><a href="../README.md">Hướng dẫn gói</a> · <a href="README.md">Ý nghĩa cột</a> · <a href="../du_bao_va_danh_gia/README.md">Dự báo và đánh giá</a> · <a href="../so_do_co_che_lightgbm.png">Sơ đồ cơ chế</a> · <a href="chi_so_theo_so_cay.csv">Chỉ số theo số cây</a> · <a href="vi_du_10_dong_qua_80_cay.csv">10 dòng qua 80 cây</a></p>
<img src="chi_so_theo_so_cay.png" alt="Chỉ số train và validation qua số cây">
<div class="scroll"><table><thead><tr><th>Cây</th><th>Số lá</th><th>Điều kiện nút gốc</th><th>Dữ liệu đối chiếu</th></tr></thead><tbody>
""" + "\n".join(rows) + "\n</tbody></table></div></html>\n"
    (root / "toan_bo_80_cay" / "muc_luc.html").write_text(document, encoding="utf-8")
    manifest = root / "manifest_sha256.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["path", "bytes", "sha256"])
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path == manifest or "__pycache__" in path.parts:
                continue
            writer.writerow([path.relative_to(root).as_posix(), path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()])
    print("Built 80-tree data index and SHA-256 manifest.")


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
