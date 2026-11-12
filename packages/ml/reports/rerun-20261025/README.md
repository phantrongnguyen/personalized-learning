# Kết quả tái thực nghiệm — rerun-20261025

Pipeline hoàn tất từ dữ liệu thô; giữ cấu hình lịch sử. Test là split OULAD lịch sử, không phải holdout độc lập mới.

## Danh tính và phạm vi run

Ngày hoàn tất **25/10/2026** theo [provenance](provenance.json). Dữ liệu **OULAD**, chia theo ID sinh viên seed 41, train/validation/test theo giao thức lịch sử. Artifact refit train+validation tại cutoff 75%, threshold 0,5 có SHA-256 `50811be18f112283f25de864a9d5b99b63501f8f1579c455ac10860a55828df0` theo [test_metrics.json](test_metrics.json). Artifact app giữ SHA `90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db`; metric trùng không làm hai artifact đồng nhất. [Thực nghiệm hiện hành](../../../../reports/evaluation/THESIS_EXPERIMENTS.md) là nguồn chuẩn về phạm vi kết luận.

## LightGBM trên validation

Ngữ cảnh **mọi hàng của bảng dưới**: run 25/10/2026, OULAD validation, model **train-only**, threshold 0,5; cutoff ghi riêng từng hàng. SHA estimator train-only từng hàng **không được công bố**, không dùng SHA artifact refit làm checksum thay thế. Validation 50% có 3.638 lượt; 75% có 3.415 lượt theo [all_models_comparison.csv](all_models_comparison.csv); cohort thay đổi theo cutoff. Nguồn số liệu: [bảng so sánh](all_models_comparison.csv), môi trường/dữ liệu/checksum: [provenance](provenance.json).

| Cutoff | Phương pháp | Đặc trưng | Accuracy | Recall | AP |
| --- | --- | ---: | ---: | ---: | ---: |
| 50% | Full features | 38 | 0.812809 | 0.623022 | 0.851085 |
| 50% | HCO | 17 | 0.807861 | 0.611511 | 0.845177 |
| 50% | VNLS | 16 | 0.810060 | 0.613669 | 0.846981 |
| 50% | HCO-VNLS | 16 | 0.805388 | 0.601439 | 0.845151 |
| 75% | Full features | 38 | 0.873499 | 0.689803 | 0.896987 |
| 75% | HCO | 17 | 0.870571 | 0.678663 | 0.891541 |
| 75% | VNLS | 16 | 0.872914 | 0.690660 | 0.892561 |
| 75% | HCO-VNLS | 17 | 0.874085 | 0.689803 | 0.896757 |

## Test artifact sau fit train + validation

Ngữ cảnh: SHA `50811be18f112283f25de864a9d5b99b63501f8f1579c455ac10860a55828df0`, OULAD **test lịch sử 3.447 lượt**, cutoff **75%**, threshold **0,5**, hoàn tất **25/10/2026**. [Bảng metric chuẩn app/rerun](../../../../reports/evaluation/THESIS_EXPERIMENTS.md#3-kết-quả-dự-báo-lịch-sử) được sinh trực tiếp từ JSON nguồn; số đầy đủ và confusion counts nằm trong [test_metrics.json](test_metrics.json).

## Bằng chứng và giới hạn

- Bảng đối chiếu lịch sử: [validation_comparison.csv](validation_comparison.csv).
- Toàn bộ ba bộ học: [all_models_comparison.csv](all_models_comparison.csv); chênh AP lớn nhất: 0.
- Manifest, notebook đã chạy, dữ liệu cấp dòng và artifact nằm trong `packages/ml/runs/rerun-20261025/` (Git ignore).
- Mã nguồn và dữ liệu được checksum; môi trường đầy đủ được ghi trong manifest.
- Bản provenance không chứa dữ liệu cấp sinh viên: [provenance.json](provenance.json).
- Hình nghiên cứu tổng hợp được lưu tại [figures/](figures/).
- Không thay model backend; không đánh giá chất lượng gợi ý hay hiệu quả can thiệp.
- Giữ nguyên hạn chế phương pháp: ngân sách 8, cơ sở thuật toán cần đối chiếu và test đã được dùng trong lịch sử nghiên cứu.
