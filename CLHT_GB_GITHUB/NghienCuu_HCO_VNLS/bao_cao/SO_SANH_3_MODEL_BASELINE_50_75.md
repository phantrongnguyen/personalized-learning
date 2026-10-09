# So sánh LightGBM, XGBoost và CatBoost tại cutoff 50% / 75%

Ngày tổng hợp: **09/10/2026**. Nhánh: **`aBaoN9/clht-gb-github`**. Báo cáo đọc kết quả đã chạy; không chạy lại huấn luyện, không thêm số liệu mô phỏng và không đổi model ứng dụng.

Nguồn được kiểm tra tại commit `589bb3bca5bae82e1c9deffd84a5ed2b858b518a`. Hai baseline ở đây là **CatBoost và XGBoost**, đối chiếu với LightGBM. Mỗi bộ học có đủ biến / HCO / VNLS / HCO-VNLS ở hai cutoff: tổng cộng **24 trường hợp**, không chỉ ba dòng model.

## 1. Notebook baseline đã push chưa?

| Notebook | Cutoff | Cell code có execution count | Output | Lỗi output | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| [06_so_sanh_catboost_voi_lightgbm_50_75.ipynb](../notebooks/06_so_sanh_catboost_voi_lightgbm_50_75.ipynb) | 50% và 75% | 9/9 | 23 | 0 | Đã có trên GitHub |
| [07_so_sanh_xgboost_voi_lightgbm_50_75.ipynb](../notebooks/07_so_sanh_xgboost_voi_lightgbm_50_75.ipynb) | 50% và 75% | 10/10 | 24 | 0 | Đã có trên GitHub |

Cả hai notebook đã được push từ commit `87fae92`, có output thực nghiệm. Notebook 07 còn gộp bảng 24 trường hợp ở cell 21. LightGBM tham chiếu được khóa từ [notebook 05b](../notebooks/05b_hco_vnls_lightgbm.ipynb). Không cần push lại các notebook giống nội dung hiện có.

## 2. Giao thức và dữ liệu

| Cutoff | Train | Validation | Test chỉ kiểm kê | Biến gốc ứng viên | Tỷ lệ risk train | Tỷ lệ risk validation |
| --- | --- | --- | --- | --- | --- | --- |
| 50% | 17310 | 3638 | 3651 | 38 | 37.25% | 38.21% |
| 75% | 16297 | 3415 | 3447 | 38 | 33.35% | 34.17% |

- Cutoff 50%/75% là thời điểm dừng thu thập đặc trưng theo độ dài học phần; **không phải ngưỡng cảnh báo**. `Full features` là đủ 38 biến tại cutoff tương ứng, không phải quan sát hết học phần 100%.
- Nhãn nguy cơ: Fail/Withdrawn → 1; Pass/Distinction → 0. Fit cuối chỉ dùng train, chấm trên validation có sẵn, ngưỡng 0,5. Tìm mask bằng GroupKFold 3 fold theo `id_student` bên trong train.
- Seed 41, budget **8 mask mới / phương pháp / cutoff** cho baseline, population 3, alpha 0,85; cache tránh chấm lại mask. Mỗi mask mới được chấm 3 fold. Không dò thêm hyperparameter hoặc ngưỡng.
- LightGBM sử dụng mask đã chốt ở 05b, chỉ fit/chấm lại để đối chiếu. XGBoost/CatBoost tìm mask riêng, nên không được gọi đây là thí nghiệm ba bộ học trên một mask hoàn toàn giống nhau.
- Hai notebook này **không chấm test** và không thay artifact triển khai. Kết quả test LightGBM đã lưu ở gói kiểm tra khác không được ghép vào bảng validation của ba model.

| Bộ học | Cấu hình | Tiền xử lý | CPU threads |
| --- | --- | --- | --- |
| LightGBM | 80 cây; learning_rate=0,055; num_leaves=15; min_child_samples=35 | Median/mode trên train + One-Hot | 4 |
| XGBoost | 80 cây; max_depth=4; learning_rate=0,055; hist; reg_lambda=1; reg_alpha=0; min_child_weight=1; subsample=colsample_bytree=1 | Median/mode trên train + One-Hot | 4 |
| CatBoost | 80 cây; depth=5; learning_rate=0,055; l2_leaf_reg=5; Logloss | Category gốc; thiếu category → THIEU; numeric NaN | 4 |

CatBoost giữ category gốc, nên cột `encoded_features` trong CSV bằng số biến đầu vào, **không phải** đếm mọi đặc trưng nội bộ mà CatBoost có thể tạo. Cùng 80 cây không đồng nghĩa độ phức tạp bằng nhau.

## 3. Chất lượng validation của đủ 24 trường hợp

Accuracy / Precision / Recall / F1 risk / weighted F1 trình bày theo %. AP, ROC-AUC và Brier giữ thang 0–1. `Biến/cột` là số biến gốc / số cột sau tiền xử lý; Brier thấp hơn tốt hơn. `Full` trong các bảng là `Full features`.

### Cutoff 50%

| Model | Phương pháp | Biến/cột | Accuracy | Precision risk | Recall risk | F1 risk | Weighted F1 | AP | ROC-AUC | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LightGBM | Full | 38/76 | 81.28% | 84.65% | 62.30% | 71.78% | 80.56% | 0.851085 | 0.873013 | 0.131280 |
| LightGBM | HCO | 17/41 | 80.79% | 84.24% | 61.15% | 70.86% | 80.01% | 0.845177 | 0.864770 | 0.133670 |
| LightGBM | VNLS | 16/38 | 81.01% | 84.71% | 61.37% | 71.17% | 80.23% | 0.846981 | 0.866636 | 0.133365 |
| LightGBM | HCO-VNLS | 16/29 | 80.54% | 84.44% | 60.14% | 70.25% | 79.70% | 0.845151 | 0.867700 | 0.134244 |
| XGBoost | Full | 38/76 | 81.01% | 85.92% | 60.14% | 70.76% | 80.14% | 0.849215 | 0.869999 | 0.132547 |
| XGBoost | HCO | 17/41 | 80.95% | 86.19% | 59.71% | 70.55% | 80.05% | 0.846477 | 0.864564 | 0.133785 |
| XGBoost | VNLS | 16/38 | 80.92% | 86.02% | 59.78% | 70.54% | 80.03% | 0.844720 | 0.864212 | 0.134607 |
| XGBoost | HCO-VNLS | 17/30 | 80.87% | 86.07% | 59.57% | 70.41% | 79.96% | 0.848753 | 0.869656 | 0.132712 |
| CatBoost | Full | 38/38 | 81.01% | 85.77% | 60.29% | 70.81% | 80.15% | 0.848889 | 0.872285 | 0.132432 |
| CatBoost | HCO | 17/17 | 80.79% | 86.25% | 59.14% | 70.17% | 79.85% | 0.841382 | 0.861021 | 0.136515 |
| CatBoost | VNLS | 16/16 | 80.48% | 84.84% | 59.57% | 69.99% | 79.60% | 0.840444 | 0.861873 | 0.136732 |
| CatBoost | HCO-VNLS | 17/17 | 80.37% | 85.14% | 58.92% | 69.64% | 79.44% | 0.842623 | 0.865255 | 0.135767 |

### Cutoff 75%

| Model | Phương pháp | Biến/cột | Accuracy | Precision risk | Recall risk | F1 risk | Weighted F1 | AP | ROC-AUC | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LightGBM | Full | 38/76 | 87.35% | 92.00% | 68.98% | 78.84% | 86.83% | 0.896987 | 0.917889 | 0.094554 |
| LightGBM | HCO | 17/41 | 87.06% | 92.20% | 67.87% | 78.18% | 86.49% | 0.891541 | 0.912140 | 0.097061 |
| LightGBM | VNLS | 16/38 | 87.29% | 91.70% | 69.07% | 78.79% | 86.78% | 0.892561 | 0.912410 | 0.096208 |
| LightGBM | HCO-VNLS | 17/30 | 87.41% | 92.21% | 68.98% | 78.92% | 86.89% | 0.896757 | 0.917381 | 0.094905 |
| XGBoost | Full | 38/76 | 87.29% | 92.57% | 68.29% | 78.60% | 86.74% | 0.895345 | 0.916297 | 0.095650 |
| XGBoost | HCO | 17/41 | 87.20% | 93.04% | 67.61% | 78.31% | 86.61% | 0.890981 | 0.911325 | 0.097513 |
| XGBoost | VNLS | 15/37 | 87.14% | 92.23% | 68.12% | 78.36% | 86.59% | 0.887765 | 0.905385 | 0.097848 |
| XGBoost | HCO-VNLS | 17/30 | 87.32% | 93.08% | 67.95% | 78.55% | 86.75% | 0.894079 | 0.914169 | 0.096218 |
| CatBoost | Full | 38/38 | 87.14% | 91.84% | 68.47% | 78.45% | 86.61% | 0.897867 | 0.919869 | 0.094969 |
| CatBoost | HCO | 17/17 | 86.79% | 91.44% | 67.69% | 77.79% | 86.23% | 0.888544 | 0.910016 | 0.099419 |
| CatBoost | VNLS | 15/15 | 86.91% | 91.47% | 68.04% | 78.03% | 86.36% | 0.885410 | 0.904062 | 0.099762 |
| CatBoost | HCO-VNLS | 16/16 | 85.89% | 91.52% | 64.70% | 75.80% | 85.17% | 0.883905 | 0.908087 | 0.102242 |

## 4. Thời gian thực nghiệm

**Đơn vị: giây. Đo một lần, không phải trung bình benchmark.** `search_seconds` là tìm mask gồm CV; `fit_seconds` gồm tiền xử lý + fit cuối trên toàn train; `predict_seconds` gồm transform + dự đoán toàn validation, không phải một dòng và không gồm chấm metrics. Tổng pha bên dưới = search + fit cuối + predict, không gồm mọi overhead notebook.

LightGBM không tìm lại mask, nên search để **— (không đo / không chạy lại)**, không ghi 0 và không xem đây là tổng chi phí huấn luyện end-to-end. Full features của hai baseline không tìm mask nên search = 0. Thời gian LightGBM trong báo cáo lấy từ notebook 07 như bảng gộp, không cộng lặp lần fit LightGBM trong notebook 06.

### Thời gian cutoff 50%

| Model | Phương pháp | Mask mới trong lần đối chứng | Search (s) | Fit cuối (s) | Predict validation (s) | Tổng pha đo (s) |
| --- | --- | --- | --- | --- | --- | --- |
| LightGBM | Full | 0 | — | 0.2839 | 0.0229 | — |
| LightGBM | HCO | 0 | — | 0.1764 | 0.0162 | — |
| LightGBM | VNLS | 0 | — | 0.1574 | 0.0207 | — |
| LightGBM | HCO-VNLS | 0 | — | 0.2527 | 0.0189 | — |
| XGBoost | Full | 0 | 0.000 | 0.6488 | 0.0242 | 0.6730 |
| XGBoost | HCO | 8 | 6.344 | 0.1856 | 0.0128 | 6.5428 |
| XGBoost | VNLS | 8 | 4.979 | 0.2920 | 0.0208 | 5.2914 |
| XGBoost | HCO-VNLS | 8 | 6.231 | 0.1743 | 0.0137 | 6.4185 |
| CatBoost | Full | 0 | 0.000 | 5.6390 | 0.0335 | 5.6724 |
| CatBoost | HCO | 8 | 114.801 | 4.2839 | 0.0113 | 119.0959 |
| CatBoost | VNLS | 8 | 104.917 | 4.2939 | 0.0089 | 109.2197 |
| CatBoost | HCO-VNLS | 8 | 115.820 | 4.3463 | 0.0105 | 120.1767 |

### Thời gian cutoff 75%

| Model | Phương pháp | Mask mới trong lần đối chứng | Search (s) | Fit cuối (s) | Predict validation (s) | Tổng pha đo (s) |
| --- | --- | --- | --- | --- | --- | --- |
| LightGBM | Full | 0 | — | 0.4016 | 0.0287 | — |
| LightGBM | HCO | 0 | — | 0.2103 | 0.0210 | — |
| LightGBM | VNLS | 0 | — | 0.1726 | 0.0138 | — |
| LightGBM | HCO-VNLS | 0 | — | 0.1603 | 0.0143 | — |
| XGBoost | Full | 0 | 0.000 | 0.3681 | 0.0175 | 0.3856 |
| XGBoost | HCO | 8 | 6.131 | 0.1871 | 0.0160 | 6.3342 |
| XGBoost | VNLS | 8 | 4.926 | 0.1804 | 0.0124 | 5.1189 |
| XGBoost | HCO-VNLS | 8 | 4.474 | 0.1487 | 0.0106 | 4.6328 |
| CatBoost | Full | 0 | 0.000 | 4.9275 | 0.0184 | 4.9459 |
| CatBoost | HCO | 8 | 106.371 | 4.0081 | 0.0111 | 110.3905 |
| CatBoost | VNLS | 8 | 97.990 | 4.1465 | 0.0091 | 102.1453 |
| CatBoost | HCO-VNLS | 8 | 101.819 | 7.0622 | 0.0159 | 108.8974 |

### Tổng các pha của 8 trường hợp / model

| Model | Search tổng (s) | Fit cuối tổng (s) | Predict tổng (s) |
| --- | --- | --- | --- |
| LightGBM | — | 1.8152 | 0.1564 |
| XGBoost | 33.084 | 2.1850 | 0.1280 |
| CatBoost | 641.718 | 38.7074 | 0.1187 |

### Khoảng thực thi notebook từ metadata

| Notebook baseline | Bắt đầu UTC+7 | Kết thúc UTC+7 | Khoảng đầu–cuối (s) |
| --- | --- | --- | --- |
| LightGBM / 05b lịch sử | 23/09/2026 21:25:29 | 23/09/2026 21:26:07 | 38.294 |
| CatBoost | 07/10/2026 21:52:39 | 07/10/2026 22:04:13 | 693.871 |
| XGBoost | 07/10/2026 22:04:17 | 07/10/2026 22:05:04 | 47.083 |

Dòng LightGBM là metadata **lịch sử của notebook 05b ngày 23/09/2026**, không phải tìm kiếm được chạy lại ngày 07/10/2026. Chỉ có khoảng đầu–cuối notebook, không có search_seconds tách riêng cho từng mask. Không so trực tiếp 38,294 giây này với hai baseline để tuyên bố ưu thế tốc độ, không phân bổ hoặc suy đoán thời gian search từng phương pháp.

Khoảng đầu–cuối tính từ cell code đầu tiên bắt đầu đến cell code cuối cùng kết thúc, gồm cả import, fit lại LightGBM tham chiếu, search baseline, metrics, vẽ hình và ghi file, và có thể gồm khoảng chờ giữa các cell. Không phải thời gian riêng của CatBoost/XGBoost. Không cộng bảng này vào thời gian các pha vì sẽ tính trùng.

Không có số đo RAM đỉnh, CPU utilization hoặc cấu hình CPU/RAM phần cứng trong giao thức. Không suy ra tiết kiệm bộ nhớ, điện năng hoặc tốc độ ổn định. Python 3.12.6; numpy 2.2.6; pandas 2.2.2; scikit-learn 1.6.0; lightgbm 4.7.0; catboost 1.2.10; xgboost 3.1.2.

## 5. Đọc kết quả và đánh đổi

- **Cutoff 50%:** AP cao nhất trong nhóm đủ biến là LightGBM (0.851085); trong nhóm HCO-VNLS là XGBoost (0.848753). Đây là kết quả của cấu hình/seed/ngân sách đang dùng, không phải kết luận bộ học luôn tốt hơn.

  - HCO-VNLS + LightGBM: 16/38 biến, giảm 57.89%; so với đủ biến cùng bộ học, AP -0.005934, Accuracy -0.74 điểm %, Recall -2.16 điểm %.

  - HCO-VNLS + XGBoost: 17/38 biến, giảm 55.26%; so với đủ biến cùng bộ học, AP -0.000462, Accuracy -0.14 điểm %, Recall -0.58 điểm %.

  - HCO-VNLS + CatBoost: 17/38 biến, giảm 55.26%; so với đủ biến cùng bộ học, AP -0.006266, Accuracy -0.63 điểm %, Recall -1.37 điểm %.

- **Cutoff 75%:** AP cao nhất trong nhóm đủ biến là CatBoost (0.897867); trong nhóm HCO-VNLS là LightGBM (0.896757). Đây là kết quả của cấu hình/seed/ngân sách đang dùng, không phải kết luận bộ học luôn tốt hơn.

  - HCO-VNLS + LightGBM: 17/38 biến, giảm 55.26%; so với đủ biến cùng bộ học, AP -0.000231, Accuracy +0.06 điểm %, Recall +0.00 điểm %.

  - HCO-VNLS + XGBoost: 17/38 biến, giảm 55.26%; so với đủ biến cùng bộ học, AP -0.001266, Accuracy +0.03 điểm %, Recall -0.34 điểm %.

  - HCO-VNLS + CatBoost: 16/38 biến, giảm 57.89%; so với đủ biến cùng bộ học, AP -0.013962, Accuracy -1.26 điểm %, Recall -3.77 điểm %.

Ở cutoff 75%, HCO-VNLS + LightGBM giữ 17 biến thay vì 38 và Accuracy 87,41%; AP chỉ thấp hơn bản đủ biến khoảng 0,000231. CatBoost đủ biến có AP 0,897867 cao hơn LightGBM đủ biến 0,896987 một ít, nhưng HCO-VNLS + CatBoost không giữ được mức này trong lần chạy hiện tại. Không kết luận hybrid luôn thắng đủ biến, hoặc giảm số biến luôn giảm thời gian fit (CatBoost hybrid 75% fit lâu hơn bản đủ biến trong lần đo này).

LightGBM 75% vẫn là model ứng dụng hiện có. Báo cáo này không tự thay model, không chọn thêm ngưỡng và không khẳng định khác biệt nhỏ có ý nghĩa thống kê. Hai cutoff có số dòng/tỷ lệ nhãn khác nhau, nên tăng chỉ số từ 50% sang 75% không phải phép so sánh ghép cặp trên đúng một tập mẫu. Budget 8 nhỏ, một seed/một lần đo không chứng minh phương pháp chọn biến hay bộ học ưu việt tổng quát.

## 6. CV chọn đặc trưng và ma trận đối chiếu

Fitness CV là mục tiêu tìm mask, khác AP validation. Mean/std AP CV chỉ có ở baseline đã tìm lại; std là độ phân tán giữa 3 fold, không phải nhiều seed hay khoảng tin cậy. Mask LightGBM dùng fitness lịch sử từ 05b; cột mean/std để trống nếu nguồn không ghi, không suy ngược từ fitness.

| Cutoff | Model | Phương pháp | Fitness CV | Mean AP CV | Std AP CV |
| --- | --- | --- | --- | --- | --- |
| 50% | LightGBM | Full | — | — | — |
| 50% | LightGBM | HCO | 0.797282 | — | — |
| 50% | LightGBM | VNLS | 0.804073 | — | — |
| 50% | LightGBM | HCO-VNLS | 0.802476 | — | — |
| 50% | XGBoost | Full | — | — | — |
| 50% | XGBoost | HCO | 0.795610 | 0.838488 | 0.000544 |
| 50% | XGBoost | VNLS | 0.802871 | 0.842387 | 0.001591 |
| 50% | XGBoost | HCO-VNLS | 0.800115 | 0.843789 | 0.001358 |
| 50% | CatBoost | Full | — | — | — |
| 50% | CatBoost | HCO | 0.790603 | 0.832598 | 0.002133 |
| 50% | CatBoost | VNLS | 0.799837 | 0.838817 | 0.000962 |
| 50% | CatBoost | HCO-VNLS | 0.795699 | 0.838594 | 0.002897 |
| 75% | LightGBM | Full | — | — | — |
| 75% | LightGBM | HCO | 0.833627 | — | — |
| 75% | LightGBM | VNLS | 0.842307 | — | — |
| 75% | LightGBM | HCO-VNLS | 0.837786 | — | — |
| 75% | XGBoost | Full | — | — | — |
| 75% | XGBoost | HCO | 0.832096 | 0.881413 | 0.002657 |
| 75% | XGBoost | VNLS | 0.840578 | 0.882105 | 0.002954 |
| 75% | XGBoost | HCO-VNLS | 0.836695 | 0.886824 | 0.002179 |
| 75% | CatBoost | Full | — | — | — |
| 75% | CatBoost | HCO | 0.829617 | 0.878497 | 0.002255 |
| 75% | CatBoost | VNLS | 0.838231 | 0.879343 | 0.002887 |
| 75% | CatBoost | HCO-VNLS | 0.833718 | 0.878677 | 0.002439 |

| Cutoff | Model | Phương pháp | TN | FP | FN | TP | Cảnh báo | Validation n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50% | LightGBM | Full | 2091 | 157 | 524 | 866 | 1023 | 3638 |
| 50% | LightGBM | HCO | 2089 | 159 | 540 | 850 | 1009 | 3638 |
| 50% | LightGBM | VNLS | 2094 | 154 | 537 | 853 | 1007 | 3638 |
| 50% | LightGBM | HCO-VNLS | 2094 | 154 | 554 | 836 | 990 | 3638 |
| 50% | XGBoost | Full | 2111 | 137 | 554 | 836 | 973 | 3638 |
| 50% | XGBoost | HCO | 2115 | 133 | 560 | 830 | 963 | 3638 |
| 50% | XGBoost | VNLS | 2113 | 135 | 559 | 831 | 966 | 3638 |
| 50% | XGBoost | HCO-VNLS | 2114 | 134 | 562 | 828 | 962 | 3638 |
| 50% | CatBoost | Full | 2109 | 139 | 552 | 838 | 977 | 3638 |
| 50% | CatBoost | HCO | 2117 | 131 | 568 | 822 | 953 | 3638 |
| 50% | CatBoost | VNLS | 2100 | 148 | 562 | 828 | 976 | 3638 |
| 50% | CatBoost | HCO-VNLS | 2105 | 143 | 571 | 819 | 962 | 3638 |
| 75% | LightGBM | Full | 2178 | 70 | 362 | 805 | 875 | 3415 |
| 75% | LightGBM | HCO | 2181 | 67 | 375 | 792 | 859 | 3415 |
| 75% | LightGBM | VNLS | 2175 | 73 | 361 | 806 | 879 | 3415 |
| 75% | LightGBM | HCO-VNLS | 2180 | 68 | 362 | 805 | 873 | 3415 |
| 75% | XGBoost | Full | 2184 | 64 | 370 | 797 | 861 | 3415 |
| 75% | XGBoost | HCO | 2189 | 59 | 378 | 789 | 848 | 3415 |
| 75% | XGBoost | VNLS | 2181 | 67 | 372 | 795 | 862 | 3415 |
| 75% | XGBoost | HCO-VNLS | 2189 | 59 | 374 | 793 | 852 | 3415 |
| 75% | CatBoost | Full | 2177 | 71 | 368 | 799 | 870 | 3415 |
| 75% | CatBoost | HCO | 2174 | 74 | 377 | 790 | 864 | 3415 |
| 75% | CatBoost | VNLS | 2174 | 74 | 373 | 794 | 868 | 3415 |
| 75% | CatBoost | HCO-VNLS | 2178 | 70 | 412 | 755 | 825 | 3415 |

## 7. Nguồn và kiểm chứng

Tất cả bảng lấy từ CSV/JSON và output notebook đã lưu trên đúng nhánh. Đã kiểm tra đủ 24 khóa model/cutoff/method, số dòng validation, tổng TN+FP+FN+TP, số cảnh báo, Accuracy từ ma trận, metric/thời gian của bảng gộp khớp bảng nguồn và notebook không có output lỗi. Số làm tròn trong Markdown để đọc; dùng CSV cho giá trị đầy đủ và danh sách biến cụ thể.

| Nguồn | SHA-256 của blob Git tại commit nguồn |
| --- | --- |
| [ket_qua/so_sanh_ba_bo_hoc_50_75.csv](../ket_qua/so_sanh_ba_bo_hoc_50_75.csv) | `56d0e641ac03d36e831cf3d20b7e00e3b262214d7e06f9d70d2e09074e5703d7` |
| [ket_qua/so_sanh_catboost_lightgbm_50_75.csv](../ket_qua/so_sanh_catboost_lightgbm_50_75.csv) | `2fcfb4d25adbb93e8d6768f927b9de25d992d327d53d54693eea089d35152b94` |
| [ket_qua/so_sanh_xgboost_lightgbm_50_75.csv](../ket_qua/so_sanh_xgboost_lightgbm_50_75.csv) | `532ee47f3dfdc16a439ec244fe610e93cffaab6730ff80742449aeed451c6efb` |
| [ket_qua/hco_vnls_lightgbm_validation.csv](../ket_qua/hco_vnls_lightgbm_validation.csv) | `2e75f60665159a873e2394509f9bb0121cbc9b8d1fd29cd7e41343a63d1b3417` |
| [ket_qua/giao_thuc_catboost_50_75.json](../ket_qua/giao_thuc_catboost_50_75.json) | `149b060d2e1a58d0313a5651d3a26e2e6ba867e52cc18d9a0dbc37e169349a49` |
| [ket_qua/giao_thuc_xgboost_50_75.json](../ket_qua/giao_thuc_xgboost_50_75.json) | `d046d58ceb6187833a0231a1cc77c4b8fe58a9fa5135dcaa24119faada1bf3e2` |
| [ket_qua/tim_mask_catboost_50_75.csv](../ket_qua/tim_mask_catboost_50_75.csv) | `ff5499d9e2f2921365ea85eff9045e422a01c77f0d21715c9f1002a2ee7fddc8` |
| [ket_qua/tim_mask_xgboost_50_75.csv](../ket_qua/tim_mask_xgboost_50_75.csv) | `af97ff15bc70a2b287c04f3cb24b8e39988274415dde131c4916cf9ab712bed2` |

Hash trên tính byte của blob Git, không phải bản checkout đã đổi LF/CRLF trên Windows. Thời điểm ghi giao thức: CatBoost `2026-10-07T22:04:13`; XGBoost `2026-10-07T22:05:04` (giờ cục bộ).
