# Kết quả tái thực nghiệm — rerun-20261025

Pipeline hoàn tất từ dữ liệu thô; giữ cấu hình lịch sử. Test là split OULAD lịch sử, không phải holdout độc lập mới.

## LightGBM trên validation

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

- accuracy: 0.8619089062953292
- precision_risk: 0.9123222748815166
- recall_risk: 0.6569965870307167
- f1_risk: 0.7638888888888888
- average_precision_risk: 0.8815750676130706
- roc_auc: 0.9049323031916888
- brier_score: 0.10136986801098771
- tn: 2201
- fp: 74
- fn: 402
- tp: 770

## Bằng chứng và giới hạn

- Bảng đối chiếu lịch sử: [validation_comparison.csv](validation_comparison.csv).
- Toàn bộ ba bộ học: [all_models_comparison.csv](all_models_comparison.csv); chênh AP lớn nhất: 0.
- Manifest, notebook đã chạy, dữ liệu cấp dòng và artifact nằm trong `packages/ml/runs/rerun-20261025/` (Git ignore).
- Mã nguồn và dữ liệu được checksum; môi trường đầy đủ được ghi trong manifest.
- Bản provenance không chứa dữ liệu cấp sinh viên: [provenance.json](provenance.json).
- Hình nghiên cứu tổng hợp được lưu tại [figures/](figures/).
- Không thay model backend; không đánh giá chất lượng gợi ý hay hiệu quả can thiệp.
- Giữ nguyên hạn chế phương pháp: ngân sách 8, cơ sở thuật toán cần đối chiếu và test đã được dùng trong lịch sử nghiên cứu.
