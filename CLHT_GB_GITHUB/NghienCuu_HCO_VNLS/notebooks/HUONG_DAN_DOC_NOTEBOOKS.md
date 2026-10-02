# Hướng dẫn đọc chuỗi thực nghiệm dự báo và chọn đặc trưng

Đọc `00`–`05c` để hiểu các mô hình đã thử và HCO/VNLS; đọc tiếp `09`–`10` để kiểm chứng đặc trưng và tìm hiểu cách đóng gói model đang dùng trong app. Không so sánh trực tiếp kết quả giữa các chuỗi nếu cách chia tập, đặc trưng hoặc cutoff khác. Bản công bố gồm 11 notebook trong bảng dưới; không bao gồm các thử nghiệm `06`–`08` chưa được chọn làm bằng chứng trực tiếp cho model app.

Bản tổng hợp đã cập nhật: `../bao_cao/BaoCao_DuBaoNguyCo_HCO_VNLS.md`. Đọc báo cáo này để xem bảng năm mô hình, bảng so HCO/VNLS theo từng evaluator và những kết luận chưa thể khẳng định.

| File | Câu hỏi | Đầu ra chính | Cần nhớ |
|---|---|---|---|
| `00_thiet_ke_thi_nghiem.ipynb` | Thành công được định nghĩa thế nào? | Protocol và kiểm kê nguồn | Accuracy phải đi cùng Recall/AP. |
| `01_kiem_tra_du_lieu_va_ro_ri.ipynb` | Bảy bảng và khóa gộp có hợp lệ? | Kiểm kê 7 bảng; audit cutoff | Không lấy dữ liệu sau cutoff. |
| `02_tao_dac_trung_theo_thoi_gian.ipynb` | Hành vi gần cutoff có thêm tín hiệu? | Năm bảng cutoff và thống kê | Dữ liệu từng sinh viên chỉ lưu cục bộ. |
| `03_so_sanh_cac_moc_cutoff.ipynb` | Đổi thời điểm có ích không? | Bảng/đồ thị HGB | Tập enrollment có thể đổi giữa các mốc. |
| `04_catboost_lightgbm_xgboost.ipynb` | Boosting mới có vượt HGB? | Bảng validation 5 mốc | Chỉ là cấu hình ban đầu. |
| `04c_thu_them_mo_hinh.ipynb` | LogisticRegression cân bằng đánh đổi AP/Recall thế nào so bốn model còn lại? | Bảng năm model tại 50%/75% và hình AP–Recall | Cùng validation; không có test mới. |
| `05_hco_vnls_tren_boosting.ipynb` | Hybrid có hơn HCO/VNLS ở cùng budget? | Bảng mask, hình hội tụ | Fitness khác AP; pilot budget nhỏ. |
| `05b_hco_vnls_lightgbm.ipynb` | Kết luận chọn feature có phụ thuộc model? | Bảng HCO/VNLS trên LightGBM nhỏ | So đúng với LightGBM đủ feature, không trộn cấu hình 210 cây. |
| `05c_hco_vnls_catboost.ipynb` | HCO, VNLS, hybrid có còn hữu ích với CatBoost xử lý category gốc? | Bảng CatBoost 80 cây đủ cột và chọn cột, hình hội tụ | Chỉ so đúng cùng evaluator CatBoost, không trộn 240 cây của notebook 04. |
| `09_kiem_chung_dac_trung_hco_vnls.ipynb` | Mask HCO/VNLS có ổn định qua seed và hơn mask ngẫu nhiên cùng số cột không? | Bảng, hình, thử bỏ từng cột với mask hybrid | Được chọn không đồng nghĩa ảnh hưởng nhân quả; AP validation của mask có thể thấp hơn đủ 38 cột. |
| `10_dong_goi_model_hco_vnls_lightgbm_75.ipynb` | Model 17 đặc trưng tại cutoff 75% được tạo cho app như thế nào? | Đối chiếu mask 05b/09, fit train + validation, lưu model và nạp thử | Không dùng test để fit; smoke test năm dòng không phải đánh giá độ chính xác mới. |

Các kết quả test từng được xem trong lịch sử dự án; không được gọi test cũ là một holdout chưa từng sử dụng. Bảng công bố hiện tại chỉ trình bày validation.

`code_dung_chung/` chỉ chứa thao tác lặp lại (đường dẫn, chia nhóm, tạo tỷ lệ, tiền xử lý). Code huấn luyện, so sánh và nhận xét đều ở notebook để theo dõi thí nghiệm.

## Tên cột thường gặp

- `risk = 1`: Fail/Withdrawn; `risk = 0`: Pass/Distinction.
- `cutoff_day`: `floor(tỷ lệ cutoff × module_presentation_length)`, không phải phần trăm số dòng.
- `*_to_t`: chỉ dùng hoạt động đến cutoff.
- `split`: train/validation/test cố định theo sinh viên, không phải feature.
- `average_precision_risk` (AP): chất lượng xếp hạng lớp nguy cơ.
- `recall_risk`: tỷ lệ sinh viên thật sự nguy cơ được cảnh báo.
- `brier_score`: sai số xác suất; thấp hơn thường tốt hơn.
- `fitness_cv`: mục tiêu tìm mask có thưởng ít feature, không bằng AP thuần.

## Kiểm tra trạng thái

Mười một notebook trong bảng trên đã chạy và có output. `09` cần dữ liệu cutoff và mã dùng chung; `10` còn cần bảng kết quả do `05b` và `09` tạo ra. Muốn chạy lại trên máy khác cần đủ bảy CSV trong `../data/`, tái tạo các đầu ra trung gian theo đúng thứ tự và cài các gói nêu ở `README.md`. Bộ app đã có model đóng gói nên không cần chạy lại các notebook này để dùng demo.
