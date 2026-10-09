# Nguồn và cách đọc bảy hình

Đây là các hình còn dùng cho model chính và hai đối chứng. Không trộn kết quả HGB cũ vào những hình này.

| Hình | Nguồn | Ý nghĩa và giới hạn |
|---|---|---|
| `kiem_chung_duong_di_mask.png` | Notebook 09, cell 7; `nhat_ky_mask_hco_vnls.csv` | Fitness tốt nhất theo số mask đã chấm trong train-CV, không phải Accuracy validation hoặc chứng minh tối ưu toàn cục. |
| `on_dinh_feature_hybrid.png` | Notebook 09, cell 7; `tan_suat_chon_feature.csv` | Tần suất chọn biến qua năm seed; đọc cùng Jaccard. Ổn định không đồng nghĩa tác động nhân quả. |
| `ablation_feature_hybrid_75.png` | Notebook 09, cell 9; `ablation_hybrid_75_train_cv.csv` | AP bộ gốc trừ AP khi bỏ một biến. Dương là bỏ biến làm giảm AP trong tổ hợp hiện tại; không đo mức tăng điểm. |
| `so_sanh_catboost_lightgbm_50_75.png` | Notebook 06 so sánh, cell 16 đếm cả Markdown từ 1; `so_sanh_catboost_lightgbm_50_75.csv` | Hai cột là 50%/75%; ba hàng là AP–Recall, Accuracy–F1 và thời gian fit/dự đoán. Category gốc của CatBoost khác One-Hot của LightGBM, nên so hai pipeline. |
| `tim_mask_catboost_50_75.png` | Notebook 06, cell 16; `tim_mask_catboost_50_75.csv` | Số mask mới từ 1–8 và fitness tốt nhất trong train-CV; không phải epoch hoặc AP validation. |
| `so_sanh_xgboost_lightgbm_50_75.png` | Notebook 07 so sánh, cell 16; `so_sanh_xgboost_lightgbm_50_75.csv` | Bố cục như hình CatBoost. XGBoost/LightGBM cùng median/mode/One-Hot nhưng cây và mask khác nhau. |
| `tim_mask_xgboost_50_75.png` | Notebook 07, cell 16; `tim_mask_xgboost_50_75.csv` | HCO/VNLS/hybrid cùng budget 8 và seed 41; chỉ là pilot nhỏ. |

Các địa chỉ cell đều đếm từ 1, gồm cả Markdown. Đã kiểm tra cell 7 của notebook 09 vẽ hình hội tụ/ổn định và cell 9 thực hiện ablation. Không nhầm với số In [ ] chỉ đếm lần thực thi code.

Các đường nối bốn phương án chỉ giúp đọc, không biểu diễn quá trình huấn luyện. Thời gian đo một lần khi chạy nối tiếp; không kết luận giảm biến luôn làm nhanh hơn. Full features trong hình là đủ 38 biến **tại cutoff**, không phải toàn kỳ 100%.
