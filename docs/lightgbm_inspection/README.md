# Kiểm tra cơ chế LightGBM — cutoff 75%

Gói đối chiếu dữ liệu OULAD: đủ **80 cây**, sơ đồ cơ chế, dự báo validation và kết quả test. Không thay số liệu bằng mô phỏng.

## Đọc từ đâu?

- `so_do_co_che_lightgbm.png`: sơ đồ đã trao đổi; chỉ số trong ảnh là validation của bản chỉ fit train.
- `toan_bo_80_cay/muc_luc.html`: mục lục dữ liệu 80 cây, không liên kết ảnh đã bỏ khỏi gói.
- `toan_bo_80_cay/du_lieu/cay_N_nut.csv`, `cay_N_la.csv`, `cay_N_bin.csv`: nút, lá và histogram của thuộc tính được chọn tại mỗi nút.
- `toan_bo_80_cay/du_lieu/cay_N_dong.csv.gz`: đủ 16.297 dòng train ở từng cây; gradient, Hessian, lá, F/p trước và sau cập nhật. CSV chỉ nén, không cắt bớt dòng.
- `toan_bo_80_cay/du_lieu_chung/`: đặc trưng gốc, 30 cột số, bin ID và tên cột.
- `du_bao_va_danh_gia/README.md`: giải thích dự báo, ngưỡng, TP/TN/FP/FN, AP và test bằng các dòng cụ thể.
- `train_only_lightgbm.txt`, `train_only_model_dump.json`: model train-only native và cấu trúc 80 cây.

Bộ ảnh cây/histogram khoảng 95 MiB giữ cục bộ, không đưa lên GitHub. Gói giữ đủ CSV/CSV.GZ/JSON, sơ đồ và ảnh chỉ số tổng hợp nhỏ. `kiem_chung.json` trong thư mục cây là biên bản lần xuất đầy đủ, có tính cả ảnh; `manifest_sha256.csv` phản ánh tệp thực tế trong gói GitHub.

## Phân biệt hai model

| Phạm vi | Model dùng chấm | Dòng đánh giá | Accuracy | Precision nguy cơ | Recall nguy cơ | F1 nguy cơ | AP |
|---|---|---:|---:|---:|---:|---:|---:|
| Sơ đồ / validation | Chỉ fit train: 16.297 dòng | 3.415 | 87,41% | 92,21% | 68,98% | 78,92% | 0,896757 |
| Test ứng dụng | Fit train + validation: 19.712 dòng, mask đã khóa | 3.447 | 86,19% | 91,23% | 65,70% | 76,39% | 0,881575 |

Hai bảng phân loại dùng ngưỡng 0,5. Bộ 80 cây xuất là **bản train-only**, không phải cây của artifact fit lại trên train + validation. Không ghép test với cây hoặc F0 của bản train-only.

Test xác nhận ngày **09/10/2026**, nạp artifact nguyên trạng: không fit lại, không chọn ngưỡng trên test. Tập test đã xuất hiện trong lịch sử nghiên cứu; không phải holdout mới hoàn toàn chưa từng được xem trong đề tài.

## Chạy và kiểm chứng

Cần Python có LightGBM 4.7.0, pandas, numpy, scikit-learn, joblib và matplotlib. Kiểm tra phụ thuộc đầy đủ từ môi trường đã dùng của dự án.

```powershell
python verify_package.py
python export_prediction_evaluation.py --source-root "<thu_muc_nguon>" --inspection-root "." --output "<thu_muc_doi_chieu_validation>"
python evaluate_main_model_test.py --source-root "<thu_muc_nguon>" --output "<thu_muc_doi_chieu_test>"
```

`--source-root` cần `apps/backend/model_store/model_hco_vnls_lightgbm_cutoff75.joblib`, metadata cùng thư mục và `CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/du_lieu_cutoff_75.csv`. Đây là cấu trúc nguồn lúc chạy, không phải vị trí artifact trong mọi phiên bản repo. Không đóng gói thêm dataset nguồn hoặc thay model ứng dụng.

`inspect_training.py` và `export_all_trees.py` tái tạo kiểm tra huấn luyện; chạy với `--output` riêng để tạo lại ảnh. `verify_package.py` kiểm tra số dòng, G/H, cập nhật F/p qua 80 cây, thống kê lá, chỉ số validation/test, AP và checksum; không huấn luyện lại hoặc sửa model.

`.gitattributes` giữ nguyên byte tệp trong gói để Git không đổi xuống dòng làm sai SHA-256. Dump bin native giữ nguyên định dạng LightGBM, không hiển thị diff văn bản. Chạy `build_index.py` để tạo lại mục lục và manifest nếu chủ động cập nhật gói.
