# HCO–VNLS: phân tích và đánh giá kết quả huấn luyện

Ngày rà soát: **19/10/2026**. Phân tích từ CSV/JSON đã lưu và mã nguồn notebook; **không chạy lại huấn luyện**. Các điểm dưới đây là **validation lịch sử** hoặc train-CV, không phải điểm kiểm thử độc lập của artifact triển khai.

Kết quả chính: **HCO–VNLS + LightGBM tại cutoff 75%, seed 41** giữ 17/38 đặc trưng, Accuracy 87,4085%, Precision nguy cơ 92,2108%, Recall 68,9803%, AP 0,896757 và ROC-AUC 0,917381. Giá trị rõ nhất là giảm 55,26% số cột đầu vào và gần giữ nguyên chất lượng so với đủ cột. Kết quả chưa chứng minh hybrid luôn tốt hơn hoặc đã sẵn sàng triển khai rộng.

## 1. Mục tiêu và cấu trúc

Bài toán phân loại nguy cơ học tập từ OULAD tại từng thời điểm quan sát. HCO, VNLS và hybrid chọn tập con đặc trưng; LightGBM, CatBoost hoặc XGBoost đánh giá các tập con đó.

| Thành phần | Vai trò |
| --- | --- |
| `research_code/data.py` | Đọc nguồn, tạo dữ liệu as-of theo cutoff và nhãn. |
| `research_code/models.py` | Cấu hình bộ học và pipeline tiền xử lý. |
| `research_code/evaluation.py` | Metric và GroupKFold ba fold theo sinh viên. |
| `research_code/optimizers.py` | Mask nhị phân, fitness và thuật toán tìm kiếm. |
| `shared_code/thuc_nghiem.py` | Chia sinh viên, dựng tỷ lệ/cửa sổ thời gian, quản lý đường dẫn. |
| `notebooks/` | Kiểm tra dữ liệu, tạo đặc trưng, huấn luyện, so sánh và đóng gói. |
| `results/` | Kết quả CSV và giao thức JSON hiện có. |
| `requirements.txt` | Phiên bản thư viện thí nghiệm. |

Luồng notebook hiện có: **01 → 02 → 05b → 06/07 → 09 → 10**. Notebook 03/04/05/08 được nhắc trong lịch sử nhưng không có trong thư mục hiện tại.

## 2. Dữ liệu và cách chia tập

Bảy nguồn đặt tại `data/raw` ở gốc repository: `studentInfo.csv`, `studentRegistration.csv`, `courses.csv`, `assessments.csv`, `studentAssessment.csv`, `studentVle.csv`, `vle.csv`. [Kiểm kê nguồn](results/kiem_ke_7_bang.csv) lưu số cột, kích thước và SHA-256, không phải bảng huấn luyện đã gộp.

- Đơn vị dữ liệu là enrollment, khóa `(id_student, code_module, code_presentation)`.
- `risk=1` gồm `Fail` và `Withdrawn`; `risk=0` gồm `Pass` và `Distinction`. Model không phân biệt nguyên nhân bỏ học với trượt môn.
- Cutoff = `floor(tỷ_lệ × module_presentation_length)`, không phải tỷ lệ số dòng dữ liệu.
- Mã tạo đặc trưng chỉ tổng hợp hoạt động/bài nộp không vượt cutoff; loại đăng ký chưa bắt đầu hoặc đã rút trước/đúng cutoff. Vì vậy quần thể thay đổi theo mốc.
- Notebook 02 chia xấp xỉ 70%/15%/15% **theo sinh viên**, seed 41, rồi gắn split vào enrollment. Các enrollment của cùng người thuộc cùng tập; tỷ lệ số dòng có thể khác tỷ lệ người.
- Loại `id_student`, `final_result`, `risk`, `split` và các cột quản lý cutoff khỏi feature. Chọn mask dùng GroupKFold ba fold chỉ trong train; tiền xử lý được fit riêng trong từng fold.

Nguồn: [tong_quan_cac_moc.csv](results/tong_quan_cac_moc.csv).

| Cutoff | Enrollment | Train | Validation | Test | Feature | Tỷ lệ nguy cơ train |
| --- | --- | --- | --- | --- | --- | --- |
| 50% | 24599 | 17310 | 3638 | 3651 | 38 | 37.25% |
| 60% | 23935 | 16845 | 3537 | 3553 | 38 | 35.52% |
| 65% | 23584 | 16607 | 3479 | 3498 | 38 | 34.59% |
| 70% | 23375 | 16458 | 3445 | 3472 | 38 | 34.00% |
| 75% | 23159 | 16297 | 3415 | 3447 | 38 | 33.35% |

Validation 50% có 1.390/3.638 enrollment nguy cơ (38,21%); 75% có 1.167/3.415 (34,17%). Chênh lệch metric giữa mốc chịu tác động của cả dữ liệu quan sát lẫn thay đổi quần thể, không phải so sánh trên cùng toàn bộ enrollment. Mốc 60%, 65%, 70% mới có tổng quan dữ liệu, chưa có bảng so sánh model tương ứng.

## 3. Giao thức và chỉ số

| Thành phần | Cấu hình đã lưu |
| --- | --- |
| LightGBM | 80 cây; learning_rate=0,055; num_leaves=15; min_child_samples=35; random_state=41; n_jobs=4. |
| CatBoost | 80 iterations; depth=5; learning_rate=0,055; l2_leaf_reg=5; random_seed=41; CPU, 4 threads. |
| XGBoost | 80 cây; max_depth=4; learning_rate=0,055; min_child_weight=1; reg_lambda=1; tree_method=hist; random_state=41; CPU, 4 threads. |
| Tìm mask | 38 bit; alpha=0,85; budget 8 mask mới; population=3 cho tìm kiếm quần thể. |
| Kiểm chứng độ ổn định | Seed tìm kiếm 41, 77, 103, 211, 307; giữ nguyên split và random_state của LightGBM. |
| Ngưỡng phân loại | 0,5; chưa tối ưu theo mục tiêu vận hành. |

```text
fitness = 0.85 × AP_train_CV + 0.15 × (1 − số_cột_được_chọn / 38)
```

Fitness cao có thể do ít cột hơn dù AP giảm. Giảm 21 cột đóng góp khoảng 0,0829 vào phần thưởng độ gọn; không đọc fitness như độ chính xác. Số cột là feature gốc: ở 75%, LightGBM đủ cột có 76 chiều sau tiền xử lý, hybrid có 30 chiều.

AP là `average_precision_score` cho lớp nguy cơ, khác ROC-AUC và khác precision tại ngưỡng 0,5. Precision đo độ đúng của cảnh báo, Recall đo tỷ lệ nguy cơ được phát hiện. Accuracy/Precision/Recall/F1/AP/ROC-AUC cao hơn thường tốt hơn; Brier thấp hơn tốt hơn, nhưng riêng Brier chưa chứng minh xác suất đã được hiệu chỉnh tốt.

HCO trong mã nguồn cập nhật vị trí/vận tốc rồi lấy mẫu bit qua sigmoid; VNLS lật bit quanh mask hiện tại; hybrid thêm tìm kiếm lân cận. Tên gọi không tự xác nhận đây là bản tái hiện chính xác một công bố thuật toán cụ thể.

## 4. LightGBM: tác động của chọn đặc trưng

Nguồn: [hco_vnls_lightgbm_validation.csv](results/hco_vnls_lightgbm_validation.csv). Các hàng cùng cutoff dùng cùng LightGBM 80 cây, fit train và chấm validation; seed tìm kiếm 41.

| Cutoff | Phương pháp | Cột | Accuracy | Precision | Recall | F1 nguy cơ | AP | ROC-AUC | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50% | Full features | 38 | 81.2809% | 84.6530% | 62.3022% | 0.717779 | 0.851085 | 0.873013 | 0.131280 |
| 50% | HCO | 17 | 80.7861% | 84.2418% | 61.1511% | 0.708629 | 0.845177 | 0.864770 | 0.133670 |
| 50% | VNLS | 16 | 81.0060% | 84.7071% | 61.3669% | 0.711723 | 0.846981 | 0.866636 | 0.133365 |
| 50% | HCO-VNLS | 16 | 80.5388% | 84.4444% | 60.1439% | 0.702521 | 0.845151 | 0.867700 | 0.134244 |
| 75% | Full features | 38 | 87.3499% | 92.0000% | 68.9803% | 0.788443 | 0.896987 | 0.917889 | 0.094554 |
| 75% | HCO | 17 | 87.0571% | 92.2002% | 67.8663% | 0.781836 | 0.891541 | 0.912140 | 0.097061 |
| 75% | VNLS | 16 | 87.2914% | 91.6951% | 69.0660% | 0.787879 | 0.892561 | 0.912410 | 0.096208 |
| 75% | HCO-VNLS | 17 | 87.4085% | 92.2108% | 68.9803% | 0.789216 | 0.896757 | 0.917381 | 0.094905 |

### 4.1. Cutoff 75%: gọn hơn, chất lượng gần giữ nguyên

Hybrid giảm 38 → 17 cột (**55,26%**). AP giảm 0,000231, tương đương 0,0231 điểm phần trăm; Accuracy tăng 0,0586 điểm phần trăm; Recall giữ nguyên. ROC-AUC giảm 0,000508 và Brier tăng 0,000351. Chưa có khoảng tin cậy hay kiểm định để xác nhận khác biệt nhỏ là có ý nghĩa thống kê.

| Kết quả trên 3.415 enrollment validation | Đủ 38 cột | Hybrid 17 cột |
| --- | --- | --- |
| TN — Không nguy cơ nhận đúng | 2.178 | 2.180 |
| FP — Cảnh báo nhầm | 70 | 68 |
| FN — Bỏ sót nguy cơ | 362 | 362 |
| TP — Nguy cơ được phát hiện | 805 | 805 |
| Tổng cảnh báo | 875 | 873 |

Hybrid giảm hai cảnh báo nhầm, không phát hiện thêm nguy cơ trong lượt này. Model vẫn bỏ sót **362/1.167 = 31,02%** trường hợp nguy cơ tại ngưỡng 0,5. Accuracy 87,4% không có nghĩa phát hiện được 87,4% sinh viên nguy cơ. Các con số là enrollment, không phải số sinh viên duy nhất.

### 4.2. Cutoff 50%: giảm cột nhưng giảm chất lượng

Hybrid giữ 16/38 cột, giảm 57,89%, nhưng AP giảm 0,851085 → 0,845151; Recall giảm 62,3022% → 60,1439%; Accuracy giảm 81,2809% → 80,5388%. Bỏ sót tăng từ 524 lên 554 enrollment nguy cơ. Với cấu hình này, chưa có bằng chứng hybrid cải thiện phát hiện sớm.

Mốc 75% có metric tốt hơn nhưng chỉ còn khoảng một phần tư thời lượng học phần để hỗ trợ. Chưa có đánh giá thực địa cho biết can thiệp ở mốc đó có cải thiện kết quả học tập hay không.

## 5. So sánh ba bộ học

Nguồn: [so_sanh_ba_bo_hoc_50_75.csv](results/so_sanh_ba_bo_hoc_50_75.csv), gồm 24 cấu hình (3 bộ học × 2 cutoff × 4 chế độ). Bảng dưới trích đủ cột và hybrid; HCO/VNLS riêng nằm trong CSV.

| Cutoff | Bộ học | Chế độ | Cột | Accuracy | Recall | AP | ROC-AUC | Fit cuối (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50% | LightGBM | Full features | 38 | 81.2809% | 62.3022% | 0.851085 | 0.873013 | 0.284 |
| 50% | LightGBM | HCO-VNLS | 16 | 80.5388% | 60.1439% | 0.845151 | 0.867700 | 0.253 |
| 50% | XGBoost | Full features | 38 | 81.0060% | 60.1439% | 0.849215 | 0.869999 | 0.649 |
| 50% | XGBoost | HCO-VNLS | 17 | 80.8686% | 59.5683% | 0.848753 | 0.869656 | 0.174 |
| 75% | LightGBM | Full features | 38 | 87.3499% | 68.9803% | 0.896987 | 0.917889 | 0.402 |
| 75% | LightGBM | HCO-VNLS | 17 | 87.4085% | 68.9803% | 0.896757 | 0.917381 | 0.160 |
| 75% | XGBoost | Full features | 38 | 87.2914% | 68.2948% | 0.895345 | 0.916297 | 0.368 |
| 75% | XGBoost | HCO-VNLS | 17 | 87.3206% | 67.9520% | 0.894079 | 0.914169 | 0.149 |
| 50% | CatBoost | Full features | 38 | 81.0060% | 60.2878% | 0.848889 | 0.872285 | 5.639 |
| 50% | CatBoost | HCO-VNLS | 17 | 80.3738% | 58.9209% | 0.842623 | 0.865255 | 4.346 |
| 75% | CatBoost | Full features | 38 | 87.1449% | 68.4662% | 0.897867 | 0.919869 | 4.927 |
| 75% | CatBoost | HCO-VNLS | 16 | 85.8858% | 64.6958% | 0.883905 | 0.908087 | 7.062 |

- Đủ cột tại 50%: LightGBM dẫn AP 0,851085, sau đó XGBoost 0,849215 và CatBoost 0,848889.
- Đủ cột tại 75%: CatBoost dẫn AP 0,897867 và ROC-AUC 0,919869; LightGBM có Accuracy và Recall cao hơn ở ngưỡng 0,5. Không có model tốt nhất trên mọi tiêu chí.
- Hybrid tại 75%: LightGBM AP 0,896757, XGBoost 0,894079, CatBoost 0,883905. CatBoost hybrid Recall 64,6958%, giảm 3,7704 điểm phần trăm so với CatBoost đủ cột.
- Mask được chọn bằng evaluator tương ứng, không nhất thiết cùng tập cột. Đây là so sánh pipeline bộ học + chọn đặc trưng, không phải chỉ thay bộ học trên một mask cố định.
- LightGBM/XGBoost dùng imputation và One-Hot fit train; CatBoost giữ category gốc, điền category thiếu bằng `THIEU`, numeric thiếu giữ NaN. Khác biệt còn bao gồm tiền xử lý.

LightGBM dùng mask đóng băng từ 05b (`frozen_lightgbm_05b`), không tìm lại trong 06/07. `objective_calls=0` và `search_seconds` trống không có nghĩa chi phí tìm mask ban đầu bằng 0. CatBoost/XGBoost tìm mask train-CV với budget 8; giao thức ghi `lightgbm_max_ap_drift=0.0`.

Ở 75%, fit cuối hybrid LightGBM khoảng 0,160 s, XGBoost 0,149 s, CatBoost 7,062 s. Tìm mask riêng của hybrid XGBoost khoảng 4,474 s, CatBoost 101,819 s. Không gộp thời gian tìm mask với fit cuối. Các thời gian chỉ đo một lần (`timing_repeats=1`), chưa đủ kết luận tốc độ tổng quát hay độ trễ API. Bảng tổng hợp lấy các dòng LightGBM từ lần so XGBoost nên thời gian có thể khác bảng so CatBoost dù metric giống nhau.

[Giao thức CatBoost](results/giao_thuc_catboost_50_75.json) và [giao thức XGBoost](results/giao_thuc_xgboost_50_75.json) ghi cấu hình, phiên bản, checksum và thời điểm chạy 07/10/2026. Đây chưa phải tìm kiếm siêu tham số đầy đủ hay so sánh cùng tổng thời gian tính toán.

## 6. Độ ổn định và đối chứng ngẫu nhiên

Nguồn: [kiem_chung_mask_validation.csv](results/kiem_chung_mask_validation.csv) và [doi_chung_va_on_dinh_mask.csv](results/doi_chung_va_on_dinh_mask.csv). Có 30 mask thuật toán và hai hàng đủ cột. Notebook 09 đối chiếu mỗi mask với tám mask ngẫu nhiên cùng số cột.

| Cutoff | Phương pháp | Cột TB | AP validation TB ± SD | Recall TB | Jaccard TB | Random có AP CV thấp hơn |
| --- | --- | --- | --- | --- | --- | --- |
| 50% | HCO | 17.4 | 0.844793 ± 0.004270 | 61.1367% | 0.3183 | 65.0% |
| 50% | HCO-VNLS | 15.4 | 0.845104 ± 0.004091 | 60.7770% | 0.2962 | 90.0% |
| 50% | VNLS | 16.0 | 0.844388 ± 0.003340 | 61.1511% | 0.2667 | 82.5% |
| 75% | HCO | 16.6 | 0.889757 ± 0.007767 | 67.3693% | 0.2861 | 65.0% |
| 75% | HCO-VNLS | 15.6 | 0.893906 ± 0.003150 | 68.7746% | 0.2568 | 85.0% |
| 75% | VNLS | 16.2 | 0.891084 ± 0.003294 | 68.9460% | 0.2674 | 57.5% |

Ở 75%, hybrid có AP validation trung bình cao nhất trong ba phương pháp chọn cột (**0,893906 ± 0,003150**), nhưng vẫn thấp hơn đủ cột 0,896987. HCO dao động lớn hơn (SD 0,007767); VNLS có Recall trung bình nhỉnh hơn hybrid. Không mask nào trong 30 mask thuật toán vượt AP đủ cột tại cùng cutoff.

Jaccard hybrid 75% chỉ 0,2568, cho thấy tập cột thay đổi đáng kể theo seed. [Tần suất chọn](results/tan_suat_chon_feature.csv) ghi hybrid 75% chọn `code_module`, `highest_education`, `clicks_recent_30` ở 4/5 seed; `submission_rate` chỉ 1/5 dù ablation ở seed 41 cho mức giảm AP lớn nhất khi bỏ nó. Các cột có thể thay thế nhau và budget còn nhỏ; tần suất chọn không chứng minh ảnh hưởng nhân quả.

Tỷ lệ random thấp hơn là trung bình tỷ lệ trong tám đối chứng của từng mask; hybrid 75% đạt 85% trên train-CV. **Không phải p-value hoặc xác suất thắng tổng quát.** Thuật toán đã tối ưu trên CV, random là đối chứng; cần đối chứng best-of-budget và đánh giá độc lập để kết luận mạnh hơn. SD là dao động giữa seed tìm kiếm trên cùng split, không phải khoảng tin cậy qua năm tập dữ liệu độc lập.

Notebook 09 ghi hybrid thắng mask random tốt nhất trong tám lượt ở 3/5 seed tại 75%, 2/5 seed tại 50%. File random chi tiết chưa có trong `results`, nên nhận xét này chỉ dẫn từ notebook, chưa tái tính độc lập từ CSV hiện có.

## 7. Ablation và bộ 17 đặc trưng

Nguồn: [ablation_hybrid_75_train_cv.csv](results/ablation_hybrid_75_train_cv.csv). Bỏ từng cột khỏi hybrid 75%, seed 41, AP train-CV gốc 0,888107. Delta = AP gốc − AP khi bỏ: số dương nghĩa bỏ cột làm giảm AP.

| Cột bị bỏ | AP CV sau khi bỏ | Delta AP CV |
| --- | --- | --- |
| submission_rate | 0.883287 | +0.004821 |
| code_module | 0.884563 | +0.003544 |
| late_submissions_to_t | 0.884705 | +0.003402 |
| clicks_recent_30 | 0.885642 | +0.002466 |
| highest_education | 0.886444 | +0.001663 |
| days_since_last_activity | 0.886955 | +0.001152 |
| studied_credits | 0.887944 | +0.000163 |
| active_days_to_t | 0.888002 | +0.000105 |
| age_band | 0.888020 | +0.000087 |
| total_clicks_to_t | 0.888028 | +0.000079 |
| active_day_ratio | 0.888043 | +0.000064 |
| gender | 0.888073 | +0.000035 |
| assessments_submitted_to_t | 0.888186 | -0.000079 |
| clicks_recent_7 | 0.888321 | -0.000214 |
| clicks_url_to_t | 0.888348 | -0.000240 |
| date_registration | 0.888413 | -0.000306 |
| clicks_resource_to_t | 0.888591 | -0.000483 |

Bốn mức giảm lớn nhất thuộc `submission_rate`, `code_module`, `late_submissions_to_t`, `clicks_recent_30`. Bỏ năm cột lại làm AP CV tăng nhẹ: mask 17 cột chưa phải nghiệm tối ưu đã được chứng minh. Ablation đo đóng góp có điều kiện trong một mask/cấu hình, không xác nhận quan hệ nhân quả hoặc mức cải thiện trên dữ liệu mới.

Bộ 17 cột theo đúng thứ tự đầu vào:

```text
code_module
gender
highest_education
age_band
studied_credits
date_registration
total_clicks_to_t
clicks_resource_to_t
clicks_url_to_t
active_days_to_t
assessments_submitted_to_t
late_submissions_to_t
active_day_ratio
submission_rate
days_since_last_activity
clicks_recent_7
clicks_recent_30
```

## 8. Model đóng gói và giới hạn diễn giải

Notebook 10 khóa mask 17 cột, fit lại trên **19.712 enrollment train + validation** (16.297 + 3.415), loại 3.447 enrollment test khỏi fit. Output ghi đã nạp lại và thử năm dòng không đọc nhãn test. Đây là smoke test khả năng nạp/dự đoán, không phải đánh giá độ chính xác.

AP 0,896757, Accuracy 0,874085 và Recall 0,689803 là **điểm tham chiếu model fit train**, chép vào `validation_reference_train_only`; không phải điểm mới của artifact fit train + validation. Không ghi nhầm AP 0,8968 thành ROC-AUC.

Notebook xuất tới `mo_hinh/` dưới thư mục thí nghiệm; thư mục/artifact này chưa có trong bản được rà soát. Báo cáo không xác nhận model đã được xuất lại hoặc đồng bộ với artifact backend. Model 75% cần đúng cutoff và schema 17 cột, không tự áp dụng cho 50% hay dữ liệu HUIT.

| Khía cạnh | Giới hạn hiện tại |
| --- | --- |
| Rò rỉ dữ liệu | Mã có lọc thời gian và tách sinh viên; lượt rà soát này chưa tái sinh dữ liệu từ nguồn để kiểm chứng mọi đầu vào. |
| Đánh giá độc lập | Notebook cảnh báo validation/test lịch sử từng được xem; chưa có tập mới nguyên sơ. Giao thức 06/07 ghi `test_evaluated=false`. |
| Độ bền của chọn cột | Jaccard thấp, năm seed, budget 8 trong không gian 2^38 mask; chưa chứng minh hội tụ/tối ưu. |
| Xác suất/ngưỡng | Chưa có đánh giá hiệu chỉnh hoặc ngưỡng theo chi phí bỏ sót, cảnh báo nhầm và nguồn lực cố vấn. |
| Khái quát/công bằng | Chưa có kết quả độc lập theo kỳ học mới, môn và nhóm nhân khẩu học; không suy ra hiệu quả HUIT từ OULAD. |
| Hiệu quả can thiệp | Metric dự báo không chứng minh gợi ý làm giảm trượt môn/bỏ học. |
| Tái lập | Có tham số/phiên bản/checksum, nhưng thiếu dữ liệu đặc trưng, nhật ký random/mask và artifact trong thư mục hiện tại. |

Các bước kiểm chứng tiếp cần bám vào những giới hạn trên: khóa trước cấu hình và quy tắc chọn model; so đủ cột, HCO/VNLS/hybrid và random cùng ngân sách; tăng budget/seed; báo cáo bất định theo nhóm sinh viên; đánh giá ngưỡng, hiệu chỉnh và dữ liệu học kỳ mới. Không dùng tập mới để tiếp tục dò cấu hình rồi vẫn coi nó là test cuối.

## 9. Tái chạy và kiểm tra bằng chứng

Từ gốc repository, tạo môi trường riêng:

```powershell
python -m venv .venv-hco
.venv-hco/Scripts/python.exe -m pip install -r experiments/hco_vnls/requirements.txt
.venv-hco/Scripts/python.exe -m jupyter lab experiments/hco_vnls
```

Chọn kernel tương ứng; mở notebook từ `experiments/hco_vnls` hoặc `notebooks` bên trong để đoạn tìm ROOT thấy `research_code` và `shared_code`. Đặt bảy CSV nguồn trong `data/raw`, chạy 01/02 trước rồi 05b, 06/07, 09; chỉ chạy 10 khi muốn fit lại và xuất artifact.

Notebook 02 tạo `results/du_lieu_cutoff_*.csv` và `phan_tap_sinh_vien.csv`; nếu cutoff CSV đã tồn tại thì có nhánh tái sử dụng, cần đối chiếu nguồn/checksum trước khi coi là sinh mới. Notebook có thể ghi đè kết quả, nên lưu riêng bằng chứng cũ trước khi tái chạy. Notebook 10 không tự cập nhật model backend.

Các đầu ra được notebook/giao thức nhắc nhưng hiện chưa có: dữ liệu cutoff/split, `mask_ngau_nhien_cung_kich_thuoc.csv`, `nhat_ky_mask_hco_vnls.csv`, `tim_mask_catboost_50_75.csv`, `tim_mask_xgboost_50_75.csv`, hình trong `figures/` và model trong `mo_hinh/`. Có tên trong giao thức không chứng minh file đang tồn tại. Cần khôi phục bằng chứng gốc hoặc tái chạy có kiểm soát để tính lại đầy đủ.

## 10. Đánh giá tổng thể

**LightGBM hybrid 75% là cấu hình gọn đáng xem xét trong phạm vi kết quả hiện có:** giảm mạnh đầu vào, gần giữ nguyên AP/Recall đối chứng, fit cuối nhanh trong lượt đo đã lưu. Chưa có bằng chứng tăng AP, tăng Recall, ổn định tập cột hoặc cải thiện hiệu quả can thiệp thực tế.

Đối chứng đủ cột vẫn mạnh: LightGBM dẫn AP ở 50%, CatBoost dẫn AP ở 75% trong các bộ học/cấu hình đã thử. Lựa chọn cuối cần gắn mục tiêu AP, Recall, độ gọn và chi phí, rồi xác nhận trên dữ liệu mới.
