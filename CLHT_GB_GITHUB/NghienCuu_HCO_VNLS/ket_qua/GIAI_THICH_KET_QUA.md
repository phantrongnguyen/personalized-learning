# Cách đọc các bảng còn giữ

## Dữ liệu và model chính

- `kiem_ke_7_bang.csv`: nguồn, số cột/dung lượng và SHA-256 của bảy bảng; notebook 01 tạo.
- `tong_quan_cac_moc.csv`: thống kê tạo dữ liệu ở notebook 02, có cả mốc trung gian lịch sử; so sánh cuối dùng 50%/75%.
- `hco_vnls_lightgbm_validation.csv`: đủ 38 biến/HCO/VNLS/hybrid với LightGBM 80 cây ở hai cutoff; mask chuẩn của notebook 05b. Hàng Full features có thể không ghi chuỗi tên biến vì giữ toàn bộ đầu vào.
- `xuat_30_dac_trung_lightgbm/`: metadata và bảng giải thích tên 30 cột số sau pipeline. CSV cấp từng lượt học không chia sẻ; các con số 17 → 30 là mã hóa, không phải tạo thêm thông tin độc lập.

## Kiểm chứng bộ biến từ notebook 09

| Bảng | Cho biết gì? |
|---|---|
| `kiem_chung_mask_validation.csv` | Chỉ số và tên biến của các mask kiểm chứng; notebook 10 cần bảng này để đối chiếu mask chốt. |
| `nhat_ky_mask_hco_vnls.csv` | Từng mask mới đã chấm, AP train-CV, fitness và best fitness; nguồn hình diễn biến tìm kiếm. |
| `tan_suat_chon_feature.csv` | Số lần chọn từng biến trong năm seed; nguồn hình ổn định. |
| `mask_ngau_nhien_cung_kich_thuoc.csv` | Mask ngẫu nhiên cùng số biến để không nhầm giảm biến bất kỳ với hiệu quả của thuật toán. |
| `doi_chung_va_on_dinh_mask.csv` | Bảng tổng hợp đối chứng/ổn định, gồm Jaccard; không phải kiểm định ý nghĩa thống kê. |
| `ablation_hybrid_75_train_cv.csv` | AP thay đổi khi bỏ từng biến trong mask hybrid 75%; không đo tác động can thiệp. |

Bốn bảng nhật ký/kiểm chứng còn thiếu trong bản chia sẻ được sao chép nguyên nội dung từ gói quy trình cục bộ, kiểm tra hash, không tạo kết quả mới hoặc sửa số liệu.

## Hai đối chứng CatBoost và XGBoost

- `so_sanh_catboost_lightgbm_50_75.csv` và `so_sanh_xgboost_lightgbm_50_75.csv`: mỗi bảng 16 hàng = hai cutoff × hai bộ học × bốn phương án. Bộ học mới tự tìm mask trong train; LightGBM fit lại train-only với mask cũ.
- `so_sanh_ba_bo_hoc_50_75.csv`: 24 hàng của ba bộ học, không nhân đôi LightGBM; gộp ở cell 21 notebook 07 sau khi kiểm tra giao thức và hash dữ liệu.
- `tim_mask_catboost_50_75.csv` và `tim_mask_xgboost_50_75.csv`: mỗi bảng 48 mask mới, có AP ba fold và best fitness. Không phải dự đoán của từng sinh viên.
- `giao_thuc_catboost_50_75.json` và `giao_thuc_xgboost_50_75.json`: cấu hình, phiên bản, SHA dữ liệu, thống kê nhóm và xác nhận không đánh giá test/không đổi model app.

## Tên cột nên hiểu đúng

`features` là số biến gốc; `reduction_pct = 100 × (1 − features/38)`. `encoded_features` là số cột sau tiền xử lý bên ngoài bộ học; CatBoost giữ category gốc, không dùng con số này để suy ra số mã hóa nội bộ.

`mean_ap_cv`/`std_ap_cv` tính trong train, không phải AP validation. Std dùng ddof=0 giữa ba fold của một mask, không là độ ổn định qua nhiều seed hoặc khoảng tin cậy. `average_precision_risk` là AP trên validation; `weighted_f1` khác F1 của riêng lớp nguy cơ.

`fit_seconds` gồm tiền xử lý + fit; `predict_seconds` gồm transform + dự đoán validation; `search_seconds` là tìm mask. Search LightGBM mới để trống vì không chạy lại tìm kiếm; `objective_calls = 0` là không chấm mask mới trong lần đo này, không có nghĩa tìm kiếm miễn phí. `ap_delta_vs_historical` kiểm tra tái lập; hai đối chứng tái lập AP LightGBM với chênh lệch bằng 0.

Các số liệu dùng validation ở ngưỡng 0,5. Runtime đo một lần, phụ thuộc máy; không dùng số liệu này để khẳng định tiết kiệm tài nguyên chắc chắn. Test lịch sử không phải holdout mới. Không có điểm đánh giá con người hoặc bằng chứng gợi ý làm tăng điểm trong các bảng này.
