# Thử CatBoost và thêm mô hình — 24/09/2026

## Vì sao có lần thử này?

Notebook so boosting đã dành sẵn một nhánh cho CatBoost nhưng trước đó thiếu thư viện. Vì vậy bảng cũ chỉ có LightGBM và XGBoost; không thể phát biểu về CatBoost. Lần này cài CatBoost `1.2.10` vào `.venv` của nhánh nghiên cứu, xác minh SHA-256 wheel trùng metadata PyPI chính thức, rồi **chạy lại** notebook 04. Notebook 04c hiện chỉ giữ LogisticRegression cân bằng; notebook 05c dùng CatBoost làm evaluator cho HCO, VNLS, HCO–VNLS. Các notebook có output sẵn; không đưa CSV dự đoán cấp sinh viên lên GitHub.

Cả ba thí nghiệm đều giữ split cố định theo `id_student` và chỉ đo model trên **validation**; không dùng test lịch sử để chọn cấu hình. Dữ liệu cutoff 50% và 75% đã gộp/tạo đặc trưng ở notebook 02. Các tập enrollment hợp lệ thay đổi theo cutoff, vì vậy so model **trong cùng cutoff**, không coi tăng điểm từ 50% lên 75% là hiệu ứng thuần của thuật toán.

## 1. CatBoost cạnh LightGBM, XGBoost

Notebook `04_catboost_lightgbm_xgboost.ipynb` dùng CatBoost **240 cây**, depth 5, learning rate 0,055, category gốc; LightGBM và XGBoost dùng các pipeline tiền xử lý riêng. Cùng split nhưng không phải một thí nghiệm tách biệt ảnh hưởng từng siêu tham số. Ngưỡng phân loại là 0,5.

| Cutoff | Model | Accuracy | Precision risk | Recall risk | F1 risk | AP risk |
|---|---|---:|---:|---:|---:|---:|
| 50% | CatBoost | 0,8153 | 0,8492 | 0,6281 | 0,7221 | **0,8548** |
| 50% | LightGBM | 0,8153 | 0,8374 | 0,6410 | **0,7262** | 0,8526 |
| 50% | XGBoost | **0,8164** | 0,8478 | 0,6331 | 0,7249 | 0,8528 |
| 75% | CatBoost | 0,8750 | 0,9120 | 0,7018 | 0,7932 | **0,9019** |
| 75% | LightGBM | 0,8750 | 0,9139 | 0,7001 | 0,7928 | 0,8992 |
| 75% | XGBoost | **0,8779** | **0,9157** | **0,7078** | **0,7985** | 0,9002 |

**Điều rút ra:** CatBoost dẫn **AP trong ba cấu hình boosting đã thử** ở 50% và 75%, nhưng không dẫn đồng thời Accuracy và Recall. Tại 75%, chênh AP so XGBoost chỉ khoảng `+0,0017`; phải lặp seed/đánh giá kỳ mới mới biết chênh lệch có bền không. Trên máy này, fit CatBoost khoảng 16–18 giây ở hai mốc, LightGBM/XGBoost dưới một giây; đó là thời gian theo máy và triển khai hiện tại, không phải kết luận tốc độ phổ quát.

## 2. LogisticRegression cân bằng được giữ lại

Notebook `04c_thu_them_mo_hinh.ipynb` chạy lại LogisticRegression cân bằng lớp, so với CatBoost, LightGBM, XGBoost và HGB từ các notebook khác. Tiền xử lý số/category chỉ fit trên train. Đây là **một cấu hình pilot**, không gọi kết quả một cấu hình là giới hạn của cả họ thuật toán. ExtraTrees và MLP nhỏ đã được xóa khỏi notebook/bảng ứng viên theo yêu cầu.

| Cutoff | Model | Accuracy | Recall risk | F1 risk | AP risk |
|---|---|---:|---:|---:|---:|
| 50% | LogisticRegression cân bằng | 0,7971 | **0,7360** | **0,7349** | 0,8483 |
| 75% | LogisticRegression cân bằng | 0,8518 | **0,7901** | 0,7847 | 0,8949 |

LogisticRegression đáng chú ý nếu ưu tiên phát hiện nguy cơ: Recall 75% cao hơn CatBoost 240 cây (`0,7901` so `0,7018`), đổi lại Accuracy thấp hơn (`0,8518` so `0,8750`). Không có một cấu hình thắng đồng thời AP, Accuracy và Recall; việc thử nhiều ứng viên trên cùng validation còn gây nguy cơ chọn trúng may mắn. Xem đồ thị `hinh/thu_them_mo_hinh_validation.png` và bảng đủ năm mô hình trong `ket_qua/nam_mo_hinh_validation.csv`.

## 3. HCO/VNLS với CatBoost: kết quả âm cũng có giá trị

Notebook `05c_hco_vnls_catboost.ipynb` dùng CatBoost **80 cây** làm evaluator riêng, nhận category gốc. Ba cách tìm kiếm dùng `alpha=0,85`, seed `41`, cùng ngân sách tối đa **8 mask chưa cache**, 3-fold GroupKFold **bên trong train**. Sau khi tìm mask, fit lại CatBoost cùng cấu hình trên train và so với hàng dùng **đủ 38 cột của chính CatBoost 80 cây** trên validation. Không so chéo hàng đầy đủ này với CatBoost 240 cây để quy công/đổ lỗi cho bước chọn cột.

| Cutoff | Cách dùng cột | Cột | Accuracy | Recall risk | AP validation |
|---|---|---:|---:|---:|---:|
| 50% | Đủ cột | 38 | **0,8101** | **0,6029** | **0,8489** |
| 50% | HCO | 17 | 0,8079 | 0,5914 | 0,8414 |
| 50% | VNLS | 16 | 0,8048 | 0,5957 | 0,8404 |
| 50% | HCO–VNLS | 17 | 0,8037 | 0,5892 | 0,8426 |
| 75% | Đủ cột | 38 | **0,8714** | **0,6847** | **0,8979** |
| 75% | HCO | 17 | 0,8679 | 0,6769 | 0,8885 |
| 75% | VNLS | 15 | 0,8691 | 0,6804 | 0,8854 |
| 75% | HCO–VNLS | 16 | 0,8589 | 0,6470 | 0,8839 |

**Điều rút ra:** ở cả hai cutoff, rút cột làm AP validation giảm trong pilot này. Hybrid không hơn hai cách riêng theo AP; ở 75%, hybrid giảm 22 cột nhưng AP giảm khoảng `0,0140` và Recall giảm khoảng `0,0377` so với đủ cột. VNLS có fitness CV cao hơn HCO/hybrid tại 75% do mục tiêu thưởng độ gọn, **không có nghĩa AP validation tốt hơn**. Biểu đồ `hinh/hco_vnls_catboost_hoi_tu.png` chỉ vẽ fitness CV tốt nhất, không phải AP validation. CatBoost **không thay thế** kết quả HCO–VNLS có lợi về độ gọn trên LightGBM 80 cây trước đó; nó cho thấy lợi ích của mask **phụ thuộc evaluator**.

## 4. Quyết định nghiên cứu tiếp

1. **Giữ HCO/VNLS ở trọng tâm:** thử nhiều seed và ngân sách mask lớn hơn (ví dụ 24–48) **theo ngân sách công bằng**, nhưng chốt trước mức tối đa; so đầy đủ cột và bộ ngẫu nhiên cùng kích thước trên validation. Không chạy chỉ để ép kết quả đẹp.
2. **Lựa chọn evaluator theo mục tiêu:** CatBoost 240 cây đáng theo dõi nếu ưu tiên AP; LogisticRegression cân bằng lớp nếu ưu tiên Recall. Với CatBoost 80 cây, chưa có bằng chứng rút cột có lợi cho AP; không tuyên bố hybrid luôn cải thiện.
3. **Kiểm tra tính quan trọng cột:** lặp seed để đo tần suất được chọn, ablation bỏ từng nhóm cột tương quan và bootstrap theo sinh viên để tính độ dao động ΔAP. Được chọn một lần không phải “chứng minh” một feature quan trọng.
4. **Tăng độ tin cậy:** thí nghiệm nhiều model/threshold trên cùng validation có nguy cơ overfit validation; đánh giá trên kỳ/khóa học mới chưa từng xem. Test lịch sử đã được nhìn thấy, không dùng nó để chọn lại tham số.

Nguồn để tái lập: `notebooks/04_catboost_lightgbm_xgboost.ipynb`, `notebooks/04c_thu_them_mo_hinh.ipynb`, `notebooks/05c_hco_vnls_catboost.ipynb`; CSV tổng hợp trong `ket_qua/`. Thư viện CatBoost chỉ cài ở `.venv/` cục bộ, không commit wheel hay môi trường ảo.
