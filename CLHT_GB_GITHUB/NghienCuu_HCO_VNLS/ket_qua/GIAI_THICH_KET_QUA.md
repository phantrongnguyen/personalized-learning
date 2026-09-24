# Cách đọc các bảng kết quả

- `kiem_ke_7_bang.csv`: tên bảng, cột, dung lượng và SHA-256 của bảy nguồn.
- `tong_quan_cac_moc.csv`: số enrollment và số feature ở năm cutoff; `risk_rate_train` chỉ tính trên train.
- `hgb_theo_cutoff_validation.csv`: HGB đối chứng trên validation, cùng nhóm sinh viên chia theo seed 41.
- `boosting_validation.csv`: CatBoost/LightGBM/XGBoost trên năm cutoff; CatBoost đã được cài và notebook 04 chạy lại. Cùng split nhưng cấu hình/tiền xử lý của từng model khác nhau, đây là bảng so model hoàn chỉnh chứ không quy chênh lệch cho một tham số.
- `hco_vnls_validation.csv`: ba phương pháp tìm mask, hai seed, 50/75%; `fitness_cv` là AP CV có thưởng độ gọn, không bằng `average_precision_risk` trên validation.
- `hco_vnls_hoi_tu.csv`: lịch sử fitness, dùng vẽ biểu đồ hội tụ.
- `hco_vnls_du_feature_validation.csv`: HGB 60 vòng dùng đủ feature, đối chứng đúng cùng evaluator của notebook 05.
- `hco_vnls_lightgbm_validation.csv`: cùng ba optimizer trên LightGBM nhỏ và hàng đủ feature cùng cấu hình; thí nghiệm bổ sung ở notebook 05b.
- `hco_vnls_catboost_validation.csv`: CatBoost 80 cây nhận category gốc, hai cutoff, đủ cột và ba optimizer cùng evaluator; AP CV dùng chọn mask, AP validation dùng đối chiếu.
- `hco_vnls_catboost_hoi_tu.csv`: fitness CV tốt nhất theo bước của từng phương pháp trên CatBoost; không phải AP validation.
- `mo_hinh_thu_them_validation.csv`: **chỉ LogisticRegression cân bằng** ở 50%/75%, cùng train/validation. Có Accuracy, Precision, Recall, F1, AP và thời gian. Các ứng viên khác không nằm trong bảng năm mô hình.
- `nam_mo_hinh_validation.csv`: bảng gộp 5 mô hình CatBoost, XGBoost, LightGBM, HGB, LogisticRegression cân bằng ở hai cutoff; do notebook 04c sinh ra từ ba CSV tổng hợp, không chứa dự đoán cấp sinh viên. Chỉ so trong từng cutoff; cấu hình và preprocessing khác nhau.

Các file `du_lieu_cutoff_*.csv`, `phan_tap_sinh_vien.csv`, `du_doan_validation_*.csv` chứa thông tin cấp sinh viên/enrollment và được `.gitignore` loại khỏi bản đưa lên GitHub. Giữ chúng cục bộ để tái lập, không chia sẻ khi chưa kiểm tra quyền dữ liệu.
