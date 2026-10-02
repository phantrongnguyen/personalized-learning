# Những mô hình giữ lại để nghiên cứu tiếp

Đây là **danh sách đúng năm mô hình để làm việc tiếp**: CatBoost, XGBoost, LightGBM, HGB và LogisticRegression cân bằng; không phải kết luận rằng mọi thuật toán ngoài danh sách đều vô giá trị. Chỉ tiêu gồm Accuracy, Precision/Recall/F1 của lớp nguy cơ và AP. Các số dưới đây là **validation** với ngưỡng 0,5, cùng 38 đặc trưng và cùng cách chia nhóm sinh viên trong mỗi cutoff; không lấy kết quả test cũ để chọn. ExtraTrees và MLP nhỏ đã bị xóa khỏi notebook/bảng ứng viên hiện hành theo yêu cầu. Thí nghiệm HCO, VNLS, HCO–VNLS và đối chứng đầy đủ cột được giữ nguyên, kể cả kết quả kém hơn: không được xóa bằng chứng âm của đề tài.

## Bảng các ứng viên giữ lại

| Cutoff | Cấu hình | Vai trò | Accuracy | Precision risk | Recall risk | F1 risk | AP risk |
|---|---|---|---:|---:|---:|---:|---:|
| 50% | CatBoost 240 | Dẫn AP | 0,8153 | 0,8492 | 0,6281 | 0,7221 | **0,8548** |
| 50% | XGBoost | Accuracy cao nhất ở 50% | **0,8164** | 0,8478 | 0,6331 | 0,7249 | 0,8528 |
| 50% | LightGBM | Boosting và evaluator HCO/VNLS | 0,8153 | 0,8374 | 0,6410 | 0,7262 | 0,8526 |
| 50% | HGB 160 | Baseline của đề tài | 0,8134 | 0,8295 | 0,6439 | 0,7250 | 0,8505 |
| 50% | LogisticRegression balanced | Ưu tiên Recall | 0,7971 | 0,7339 | **0,7360** | 0,7349 | 0,8483 |
| 75% | CatBoost 240 | Dẫn AP | 0,8750 | 0,9120 | 0,7018 | 0,7932 | **0,9019** |
| 75% | XGBoost | Accuracy, F1 cao nhất | **0,8779** | 0,9157 | 0,7078 | **0,7985** | 0,9002 |
| 75% | LightGBM | Boosting và evaluator HCO/VNLS | 0,8750 | 0,9139 | 0,7001 | 0,7928 | 0,8992 |
| 75% | HGB 160 | Baseline của đề tài | 0,8773 | 0,9174 | 0,7044 | 0,7969 | 0,8986 |
| 75% | LogisticRegression balanced | Ưu tiên Recall | 0,8518 | 0,7794 | **0,7901** | 0,7847 | 0,8949 |

**Giữ vì mục tiêu khác nhau:** CatBoost dẫn AP; XGBoost nhỉnh về Accuracy/F1 tại 75%; LogisticRegression nhận diện thêm người học nguy cơ với đánh đổi Precision/Accuracy. LightGBM/HGB là các đối chứng quan trọng vì gắn với thí nghiệm chọn đặc trưng HCO/VNLS. Giữ cùng cấu hình tại hai cutoff, không chọn phiên bản khác nhau hậu nghiệm cho từng mốc.

## Điều chưa thể kết luận

Chênh vài phần nghìn AP không chứng minh mô hình tốt hơn một cách ổn định. Kết quả này được chọn sau khi đã khảo sát nhiều cấu hình trên cùng validation; test cũ từng được xem. Chưa có Accuracy 90–93% ở hai mốc. Nếu ghép với HCO/VNLS, phải so đủ cột, HCO, VNLS và hybrid trong **cùng một evaluator và ngân sách**, không lấy AP CatBoost 240 cây so thẳng với mask dùng CatBoost 80 cây.

## Tìm ở đâu?

- `notebooks/04_catboost_lightgbm_xgboost.ipynb`, `ket_qua/boosting_validation.csv`: ba boosting.
- `notebooks/03_so_sanh_cac_moc_cutoff.ipynb`, `ket_qua/hgb_theo_cutoff_validation.csv`: HGB baseline.
- `notebooks/04c_thu_them_mo_hinh.ipynb`, `ket_qua/mo_hinh_thu_them_validation.csv`, `ket_qua/nam_mo_hinh_validation.csv`, `hinh/thu_them_mo_hinh_validation.png`: LogisticRegression và bảng/hình đúng năm mô hình đã chạy lại.
- `notebooks/05_hco_vnls_tren_boosting.ipynb`, `05b_hco_vnls_lightgbm.ipynb`, `05c_hco_vnls_catboost.ipynb`: kết quả chọn đặc trưng, gồm cả các trường hợp không tăng AP.
