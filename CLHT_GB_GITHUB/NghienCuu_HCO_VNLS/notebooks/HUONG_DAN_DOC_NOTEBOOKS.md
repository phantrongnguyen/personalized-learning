# Cách đọc bảy notebook

## Năm notebook chính

Đọc **01 → 02 → 05b → 09 → 10** để đi từ bảy bảng dữ liệu đến model HCO–VNLS + LightGBM 75% đang dùng trong app.

| Notebook | Câu hỏi được giải quyết | Bằng chứng quan trọng |
|---|---|---|
| `01_kiem_tra_du_lieu_va_ro_ri.ipynb` | Gộp bảy bảng đúng khóa và đúng thời điểm không? | Kiểm kê nguồn; kiểm tra khóa và thông tin sau cutoff. |
| `02_tao_dac_trung_theo_thoi_gian.ipynb` | Tại thời điểm quan sát có thể biết những gì? | Đặc trưng/tỷ lệ/cửa sổ tương tác; split theo sinh viên; thống kê số dòng. |
| `05b_hco_vnls_lightgbm.ipynb` | HCO/VNLS giữ bao nhiêu biến, đổi lại chất lượng ra sao? | Cùng LightGBM 80 cây: đủ biến/HCO/VNLS/hybrid ở 50%/75%, bảng validation và mask. |
| `09_kiem_chung_dac_trung_hco_vnls.ipynb` | Bộ biến có bằng chứng ngoài việc được hàm chọn không? | Năm seed, mask ngẫu nhiên cùng số biến, Jaccard, tần suất chọn và bỏ từng biến. Đây không phải chứng minh nhân quả. |
| `10_dong_goi_model_hco_vnls_lightgbm_75.ipynb` | Model app được tạo và kiểm tra thế nào? | Đối chiếu mask 17 biến với 05b/09, fit 19.712 lượt học train + validation, lưu artifact và nạp thử. |

Notebook 02 giữ output lịch sử các mốc trung gian; chỉ hai mốc 50%/75% được đưa vào đối chứng cuối. Notebook 10 cần `kiem_chung_mask_validation.csv` do 09 tạo ra; không bỏ qua bước kiểm chứng khi tái tạo model.

## Hai notebook đối chứng

- `06_so_sanh_catboost_voi_lightgbm_50_75.ipynb`: CatBoost 80 cây, category gốc; đủ 38 biến/HCO/VNLS/hybrid ở hai cutoff, so pipeline LightGBM với mask đã chốt.
- `07_so_sanh_xgboost_voi_lightgbm_50_75.ipynb`: XGBoost 80 cây, median/mode/One-Hot; cùng các trường hợp, gộp bảng ba bộ học khi đã chạy 06.

Hai notebook đã chạy toàn bộ, có bảng và hình trong output. Không đánh giá test mới, không dò ngưỡng/hyperparameter và không thay model triển khai. Đủ 38 biến tại cutoff **không phải Full toàn kỳ 100%**.

## Địa chỉ cell của hai notebook đối chứng

Đếm từ 1, gồm cả Markdown; không nhầm với số `In [ ]`.

| Cell | Nội dung | Nên nhìn gì? |
|---|---|---|
| 4 | Giao thức | Seed, budget 8, alpha, ngưỡng 0,5 và tham số LightGBM. |
| 6 | Kiểm tra dữ liệu | Số dòng, nhóm sinh viên, SHA dữ liệu và chín cột loại khỏi đầu vào. |
| 8 | Bộ học và tiền xử lý | Xử lý số thiếu/category ở đâu; khác nhau giữa CatBoost và hai bộ học còn lại. |
| 10 | Chấm mask | GroupKFold chỉ trong train, AP trung bình/độ lệch chuẩn, fitness và cache. |
| 12 | Thực nghiệm | Accuracy, Precision/Recall/F1, weighted F1, AP, AUC, Brier và thời gian. |
| 14 | Đánh đổi khi giảm biến | Tên biến gốc, tỷ lệ giảm và delta so với đủ biến cùng bộ học. |
| 16 | Lưu bằng chứng | Hình, bảng CSV và JSON giao thức. |
| 18 | Nhận xét | Kết luận lấy trực tiếp từ số liệu, không viết sẵn rằng model mới thắng. |
| 21, chỉ notebook 07 | Bảng gộp | Kiểm tra hash/giao thức, gộp 24 trường hợp của ba bộ học. |

`std_ap_cv` là độ phân tán AP giữa ba fold của một mask, không phải qua nhiều seed hoặc khoảng tin cậy. `fit_seconds` gồm tiền xử lý + fit; `search_seconds` là tìm mask; `predict_seconds` gồm transform + dự đoán. Thời gian đo một lần, không đủ khẳng định benchmark.

Các CSV cấp sinh viên không chia sẻ. Để chạy lại, dùng Python 3.12, môi trường nghiên cứu riêng, requirements cấp trên và bảy CSV nguồn. Giải thích lý thuyết/bố cục trình bày nằm trong `../../../bao_cao/HUONG_DAN_TRINH_BAY.md`.
