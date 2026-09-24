# Hướng dẫn đọc chuỗi thực nghiệm dự báo và chọn đặc trưng

Đọc `00`–`05c` để hiểu năm mô hình theo đuổi và HCO/VNLS. Không so sánh trực tiếp kết quả từ chuỗi này với bảng cũ nếu cách chia tập, đặc trưng hoặc cutoff khác. Bản công bố này chỉ gồm chín notebook trong bảng dưới.

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

Chín notebook trong bảng trên đã chạy và có output. Muốn chạy lại trên máy khác cần đủ bảy CSV trong `../data/` và cài các gói nêu ở `README.md`.
