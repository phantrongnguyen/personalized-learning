# Kết quả model đã chốt — 19/10/2026

## Phạm vi và kết luận

Nhóm đã chốt model dùng trong app: **HCO-VNLS chọn 17/38 đặc trưng gốc** tại mốc 75% thời lượng học phần (30 cột sau mã hóa); **LightGBM 80 cây**, ngưỡng phân loại **0,50**. SHA-256 của artifact `apps/backend/artifacts/model_hco_vnls_lightgbm_cutoff75.joblib` là `90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db`. Việc tạo bộ hình này **không huấn luyện lại, hiệu chỉnh xác suất, đổi ngưỡng hoặc ghi đè model**.

Nhãn dương là nguy cơ **Fail/Withdrawn** trong OULAD, không phải kết luận chắc chắn một sinh viên sẽ trượt. HCO-VNLS chọn đặc trưng; LightGBM dự báo; giảng viên đánh giá căn cứ rồi quyết định nhiệm vụ trong một bước riêng. Không dùng các số 4/30, 86,7% hay 93,04% từ baseline khác để mô tả artifact hiện tại.

Nguồn kiểm tra lịch sử ở ngoài repo: `../output/lightgbm_training_inspection/du_bao_va_danh_gia/du_doan_test_model_chinh.csv` và `kiem_chung_test_model_chinh.json` (đường dẫn tính từ gốc repo). CSV chứa kết quả cấp lượt học nên **không đưa lên Git**. Script `generate_charts.py` đối chiếu SHA-256 artifact và metadata với biên bản lịch sử, tính lại các chỉ số từ nhãn và xác suất đã lưu, đối chiếu từng số đếm/chỉ số và dừng khi không khớp. `verified_metrics.json` chỉ lưu kết quả tổng hợp và checksum nguồn. Script không nạp joblib hay huấn luyện lại; việc nhóm sinh viên độc lập giữa các tập chỉ được ghi nhận theo giao thức lịch sử, không được chứng minh lại từ CSV kết quả.

| Tập / giao thức | Lượt học | Kết quả và giới hạn |
| --- | ---: | --- |
| Train | 16.297 | Chọn mask bằng train CV; không dùng test để fit. |
| Validation, model train-only | 3.415 | AP 0,8968; accuracy 0,8741; recall nguy cơ 0,6898. **Không phải** artifact sau refit. |
| Test lịch sử, artifact sau fit train + validation | 3.447 | Accuracy **0,8619**; precision nguy cơ **0,9123**; recall nguy cơ **0,6570**; F1 nguy cơ **0,7639**; AP **0,8816**; ROC-AUC **0,9049**; Brier **0,1014**. |

Tại ngưỡng 0,50: **TN=2.201, FP=74, FN=402, TP=770**. Trong 1.172 lượt học thuộc nhóm nguy cơ thật, model phát hiện 770 và bỏ sót **402 (34,3%)**; phát 844 cảnh báo. AP là average precision của thứ hạng xác suất, **khác ROC-AUC**. Test lịch sử này đã xuất hiện trong quá trình nghiên cứu: **không gọi là external holdout mới hay kiểm chứng triển khai thực địa**. Không chọn ngưỡng mới từ test.

## Bộ hình cho phần phương pháp và kết quả

| Hình | Nội dung | Nguồn và cách trình bày |
| --- | --- | --- |
| `figures/00_split_and_classes.png` | Số lượt học theo split và phân bố lớp test | Split từ bảng nghiên cứu; lớp test từ nhãn lưu trữ. |
| `figures/01_confusion_matrix.png` | Bỏ sót và báo nhầm ở ngưỡng 0,50 | Test lịch sử; phần trăm theo từng hàng nhãn thật. |
| `figures/02_roc_precision_recall.png` | ROC-AUC và AP | Test lịch sử; đường nền PR bằng tỷ lệ nguy cơ 34,0%. |
| `figures/03_calibration.png` | Xác suất so với tần suất quan sát | Chẩn đoán 10 nhóm quantile, **không hiệu chỉnh** xác suất. |
| `figures/04_threshold_sensitivity.png` | Precision/recall/số cảnh báo khi giả định đổi ngưỡng | Chỉ minh họa, **không tối ưu ngưỡng trên test**. |
| `figures/05_validation_comparison.png` | LightGBM, XGBoost, CatBoost | Train-only validation cùng 3.415 lượt học, mask khác nhau; không trộn với test model app. |
| `figures/06_feature_ablation.png` | Chênh AP khi bỏ từng biến | Train CV; không kết luận quan hệ nhân quả từ chênh lệch nhỏ. |
| `figures/07_feature_reduction.png` | Giảm 38 xuống 17 đặc trưng (55,3%) và đánh đổi AP/recall | LightGBM train-only validation; AP của bộ chọn **0,8968**, bộ đầy đủ **0,8970**, recall cùng **0,6898**. Không tuyên bố cải thiện vượt trội. |

Nhãn trên hình dùng tiếng Anh để thống nhất font; cột cuối là chú thích tiếng Việt có thể đưa vào báo cáo. Đây là **hình nghiên cứu**, không phải biểu đồ nguy cơ cá nhân trên giao diện học sinh. Không suy ra mức khẩn cấp nhẹ/vừa/nặng từ xác suất; nhãn nhị phân hiện tại theo ngưỡng 0,50. Luồng giảng viên phải giữ `insufficient_data` khi thiếu bằng chứng, không điền số liệu nghiên cứu hoặc demo thay cho nguồn LMS.

## Tái tạo và đối chiếu

Chạy tại gốc repo với Python có `pandas`, `numpy`, `scikit-learn`, `matplotlib` (tham khảo `experiments/hco_vnls/requirements.txt`):

```powershell
.\.venv\Scripts\python.exe reports/model_final/generate_charts.py `
  --predictions ../output/lightgbm_training_inspection/du_bao_va_danh_gia/du_doan_test_model_chinh.csv `
  --verification ../output/lightgbm_training_inspection/du_bao_va_danh_gia/kiem_chung_test_model_chinh.json
.\.venv\Scripts\python.exe -m pytest -q reports/model_final/test_generate_charts.py
```

Hai file `../output/...` không có trong clone Git mới; cần bản gốc được phép sử dụng, không tự tạo số liệu thay thế. Script kiểm tra checksum model/metadata, số dòng, nhãn, ngưỡng và từng chỉ số; checksum của CSV xuất hiện trong `verified_metrics.json` để so sánh chính xác tệp đầu vào. Nguồn bảng so sánh validation và ablation nằm trong `experiments/hco_vnls/ket_qua`.

## Điều chưa thể khẳng định

- Chưa có external holdout mới/kỳ học mới chưa từng được xem trong lịch sử nghiên cứu; chưa đánh giá công bằng giữa các nhóm hoặc độ trễ dữ liệu LMS ở môi trường triển khai.
- Chưa đo tác động của gợi ý/nhiệm vụ đến kết quả học tập; chất lượng dự báo không chứng minh hiệu quả can thiệp sư phạm.
- Seed cũ từng dùng AP validation khoảng 0,8968 dưới tên ROC-AUC. Migration `0002_normalize` ngày 19/10 đã tách AP và đặt ROC-AUC seed về NULL theo nguồn đã xác minh; **không lấy seed DB làm nguồn đánh giá test model**.

## Đối chiếu và tích hợp ngày 21/10/2026

Xem [chương thực nghiệm tích hợp](../evaluation/THESIS_EXPERIMENTS.md), [giao thức can thiệp](../evaluation/INTERVENTION_PROTOCOL.md) và `scripts/audit_model_evidence.py`. Đã đối chiếu source notebook tìm mask/CV/đóng gói, kiểm tra artifact/mask và tính lại metric suy ra từ confusion counts. Tệp đặc trưng và dự đoán test lịch sử chưa có tại đường dẫn tham chiếu nên chưa tái chứng minh split của đúng bộ dữ liệu hoặc tính lại AP/ROC-AUC cấp dòng. Checksum metadata lịch sử là biểu diễn CRLF; verifier chấp nhận riêng biến thể LF/CRLF, vẫn từ chối thay đổi nội dung. Không fit lại hoặc đổi threshold.
