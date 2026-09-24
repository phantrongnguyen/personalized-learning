# Báo cáo thực nghiệm dự báo nguy cơ và chọn đặc trưng HCO–VNLS

**Cập nhật:** 24/09/2026. Thí nghiệm bắt đầu ngày 23/09 và một số notebook được chạy lại ngày 24/09. Báo cáo này phản ánh **trạng thái hiện tại**, thay vì giữ nguyên lời nhận xét đã lỗi thời của lần chạy đầu.

## 1. Bài toán và điều đã chốt

Chúng ta muốn cảnh báo sinh viên có nguy cơ `Fail` hoặc `Withdrawn` khi môn học đang diễn ra, không chờ hết kỳ mới dự báo. `risk = 1` là lớp nguy cơ, `risk = 0` là `Pass` hoặc `Distinction`. Sau khi thử các họ mô hình, nhóm **giữ đúng năm cấu hình để theo đuổi**: CatBoost, XGBoost, LightGBM, HistGradientBoosting (HGB) và LogisticRegression cân bằng lớp. Ba cách chọn đặc trưng **HCO, VNLS, HCO–VNLS** vẫn là trọng tâm của đề tài; việc chọn mô hình dự báo chỉ tạo các evaluator/đối chứng phù hợp cho chúng.

Mong muốn Accuracy 90–93% là **mục tiêu, chưa phải kết quả**. Không hy sinh Recall của sinh viên nguy cơ hoặc dùng test cũ để ép đạt mục tiêu này. ExtraTrees và MLP nhỏ không còn trong notebook/bảng ứng viên hiện tại. Một số notebook MLP/ensemble/test từ lần thăm dò đầu vẫn nằm **cục bộ** để lưu lịch sử; chúng không thuộc danh sách năm mô hình và không nằm trong kế hoạch cập nhật GitHub lần này.

## 2. Dữ liệu đi từ đâu đến một dòng dự báo?

| Nguồn OULAD | Vai trò ở mức cần hiểu |
|---|---|
| `studentInfo` | Thông tin người học, môn/kỳ học và kết quả cuối kỳ dùng tạo nhãn. |
| `studentRegistration` | Ngày đăng ký/rút khỏi môn; xác định người còn trong phạm vi dự báo tại cutoff. |
| `courses` | Độ dài của mỗi môn/kỳ để tính ngày cắt theo tiến trình học. |
| `studentVle` và `vle` | Sự kiện click VLE và loại hoạt động; tổng hợp trước khi gộp. |
| `studentAssessment` và `assessments` | Lần nộp và lịch bài đánh giá; tổng hợp số lần nộp, trễ, thiếu trước cutoff. |

**Đơn vị phân tích** là một lượt học, khóa `id_student + code_module + code_presentation`. Hai bảng sự kiện nhiều dòng được lọc theo thời gian, nhóm và tính tổng trước khi ghép; không nối thẳng mọi click với mọi bài nộp vì sẽ nhân bản hàng. Bảng cuối có **một hàng cho một lượt học** và 38 đặc trưng đầu vào. Bảng kiểm kê nguồn và hash ở `ket_qua/kiem_ke_7_bang.csv`; quy trình tạo dữ liệu ở `notebooks/01_kiem_tra_du_lieu_va_ro_ri.ipynb` và `02_tao_dac_trung_theo_thoi_gian.ipynb`.

**Cutoff 50% không có nghĩa lấy 50% số sinh viên hoặc số hàng.** Với từng môn/kỳ, `cutoff_day = floor(0,50 × module_presentation_length)`; 75% thay `0,50` bằng `0,75`. Chỉ sự kiện xảy ra không muộn hơn ngày này mới được dùng. Ví dụ môn dài 200 ngày thì hai mốc là ngày 100 và 150; đó là minh họa cách tính, **không phải một hàng dữ liệu thật**. Sinh viên đã rút môn trước cutoff không thuộc nhóm đang cần cảnh báo tại mốc ấy, khiến số lượt học thay đổi giữa các mốc. Không dùng `final_result`, `risk`, ID, `split`, hoạt động sau cutoff hoặc điểm bài chưa xác minh được thời điểm công bố làm feature.

Các biến bổ sung gồm mức click mỗi ngày, tỷ lệ ngày hoạt động, tỷ lệ nộp/trễ/thiếu, số ngày từ hoạt động cuối, click trong 7/30 ngày cuối và tỷ số click nửa sau/nửa đầu của **khoảng đã quan sát**. Những biến này mô tả cường độ và xu hướng, nhưng hiện chưa có ablation chứng minh riêng từng nhóm thực sự làm chỉ số tốt hơn. Kiểm tra khóa, ngày sự kiện và rò rỉ rõ ràng đã qua; không được diễn giải là chứng minh tuyệt đối không còn leakage.

## 3. Chia dữ liệu và đọc chỉ số

Cùng một `id_student` luôn được gán vào **một** tập train, validation hoặc test qua mọi cutoff, xấp xỉ 70/15/15 theo sinh viên. Tại mỗi cutoff, hàng thuộc các tập có thể thay đổi vì điều kiện còn theo học. Imputation, one-hot và scale (khi cần) được fit **chỉ trên train**; CatBoost nhận category gốc theo xử lý riêng. HCO/VNLS tính fitness bằng GroupKFold **bên trong train**; validation dùng so ứng viên, test không được dùng để chọn lại.

| Cutoff | Lượt học đủ điều kiện | Train | Validation | Test | Feature |
|---:|---:|---:|---:|---:|---:|
| 50% | 24.599 | 17.310 | 3.638 | 3.651 | 38 |
| 60% | 23.935 | 16.845 | 3.537 | 3.553 | 38 |
| 65% | 23.584 | 16.607 | 3.479 | 3.498 | 38 |
| 70% | 23.375 | 16.458 | 3.445 | 3.472 | 38 |
| 75% | 23.159 | 16.297 | 3.415 | 3.447 | 38 |

- **Accuracy:** tỷ lệ dự báo đúng cả hai lớp ở ngưỡng xác suất 0,5; cao không có nghĩa đã tìm đủ người nguy cơ.
- **Precision risk:** trong những người bị cảnh báo, bao nhiêu người thực sự nguy cơ; thấp thường đồng nghĩa nhiều cảnh báo nhầm.
- **Recall risk:** trong những người thực sự nguy cơ, bao nhiêu người được phát hiện; thấp là bỏ sót người cần hỗ trợ.
- **F1 risk:** trung bình điều hòa của Precision và Recall nguy cơ. **AP risk:** chất lượng xếp hạng người nguy cơ qua nhiều ngưỡng; không phải Accuracy và không tự thay đổi khi chỉ dời ngưỡng 0,5.
- **Thời gian:** phụ thuộc máy, preprocessing và cấu hình; thời gian tìm mask khác thời gian fit một model đủ cột. Không so chéo để kết luận tốc độ phổ quát.

## 4. Năm mô hình giữ lại: kết quả validation

Đây là **năm cấu hình triển khai đã chạy**, không phải cuộc thi tìm siêu tham số tốt nhất cho cả họ. So trong **cùng một cutoff**: đổi từ 50% sang 75% còn đổi cả tập lượt học đủ điều kiện. Các số lấy từ `ket_qua/nam_mo_hinh_validation.csv` (10 hàng), tổng hợp từ các notebook `03`, `04` và `04c` đã chạy sẵn.

| Cutoff | Model | Accuracy | Precision risk | Recall risk | F1 risk | AP risk |
|---:|---|---:|---:|---:|---:|---:|
| 50% | CatBoost | 0,8153 | 0,8492 | 0,6281 | 0,7221 | **0,8548** |
| 50% | XGBoost | **0,8164** | 0,8478 | 0,6331 | 0,7249 | 0,8528 |
| 50% | LightGBM | 0,8153 | 0,8374 | 0,6410 | 0,7262 | 0,8526 |
| 50% | HGB | 0,8134 | 0,8295 | 0,6439 | 0,7250 | 0,8505 |
| 50% | LogisticRegression cân bằng | 0,7971 | 0,7339 | **0,7360** | 0,7349 | 0,8483 |
| 75% | CatBoost | 0,8750 | 0,9120 | 0,7018 | 0,7932 | **0,9019** |
| 75% | XGBoost | **0,8779** | 0,9157 | 0,7078 | **0,7985** | 0,9002 |
| 75% | LightGBM | 0,8750 | 0,9139 | 0,7001 | 0,7928 | 0,8992 |
| 75% | HGB | 0,8773 | **0,9174** | 0,7044 | 0,7969 | 0,8986 |
| 75% | LogisticRegression cân bằng | 0,8518 | 0,7794 | **0,7901** | 0,7847 | 0,8949 |

**Điều quan sát được:** CatBoost dẫn AP ở hai mốc nhưng không dẫn Accuracy/Recall. XGBoost dẫn Accuracy ở cả hai; tại 75% dẫn F1 risk. LogisticRegression cân bằng báo được nhiều người nguy cơ hơn, đổi lại Precision và Accuracy thấp hơn. HGB và LightGBM được giữ làm các đối chứng đã dùng trong thí nghiệm chọn feature. Khoảng cách AP CatBoost–XGBoost ở 75% chỉ khoảng `0,0017`, chưa đủ chứng minh ưu thế bền vững sau nhiều lần thử trên cùng validation. Accuracy cao nhất tại 75% là `0,8779`, **chưa đạt 0,90**.

Ở ba mốc giữa 60/65/70%, notebook `03` đã chạy HGB và notebook `04` đã chạy ba boosting; bảng chi tiết nằm ở `hgb_theo_cutoff_validation.csv` và `boosting_validation.csv`. Notebook `04c` chỉ thêm LogisticRegression tại 50%/75% nên **chưa có bảng đủ năm mô hình ở các mốc giữa**. Không được suy ra kết quả LogisticRegression giữa kỳ từ hai đầu mốc. Trong bảng boosting, AP CatBoost tại 60/65/70% lần lượt là `0,8776 / 0,8891 / 0,8952`; AP HGB tương ứng `0,8742 / 0,8870 / 0,8928`.

**Chi phí tính toán tại hai mốc chính:** CatBoost 240 cây mất khoảng 16,4–17,7 giây cho fit và dự báo ở môi trường này; LightGBM/XGBoost khoảng 0,4–0,6 giây, LogisticRegression khoảng dưới một giây. CatBoost, LightGBM, XGBoost và HGB không có cấu hình hoặc cách xử lý category hoàn toàn giống nhau; thời gian và AP chỉ là so sánh *cấu hình đang dùng*, không cô lập được tác động riêng của thuật toán.

## 5. Trọng tâm HCO, VNLS, HCO–VNLS

Mỗi feature gốc ứng với một bit 0/1 trong mask. HCO, VNLS và cách lai tìm mask nhằm cân bằng **khả năng xếp hạng nguy cơ** với **số cột cần dùng**. Trong pilot, `fitness = 0,85 × AP_CV + 0,15 × (1 − số_cột_chọn / 38)`. `AP_CV` tính bằng ba fold GroupKFold trên train. **Fitness không phải AP validation**: một mask ít cột có thể đạt fitness cao mà AP trên validation giảm.

HGB dùng cấu hình **60 vòng** và trung bình hai seed `41`, `77`; LightGBM dùng **80 cây**, một seed; CatBoost dùng **80 cây**, một seed, giữ category gốc. Mỗi phương pháp có cùng ngân sách tối đa 8 lần đánh giá mask mới trong thí nghiệm tương ứng. Mỗi evaluator đều có hàng **đủ 38 cột cùng cấu hình**; không đem CatBoost 240 cây hay HGB 160 vòng ở bảng trên so với mask của cấu hình 80/60 để quy mọi chênh lệch cho việc chọn feature.

| Evaluator | Cutoff | AP đủ 38 cột | AP HCO | AP VNLS | AP HCO–VNLS | Cột hybrid | ΔAP hybrid so đủ cột |
|---|---:|---:|---:|---:|---:|---:|---:|
| HGB 60 (TB 2 seed) | 50% | 0,8500 | 0,8481 | 0,8432 | 0,8460 | 16,5 | −0,0040 |
| HGB 60 (TB 2 seed) | 75% | 0,8975 | 0,8935 | 0,8902 | 0,8954 | 17,0 | −0,0021 |
| LightGBM 80 | 50% | 0,8511 | 0,8452 | 0,8470 | 0,8452 | 16 | −0,0059 |
| LightGBM 80 | 75% | 0,8970 | 0,8915 | 0,8926 | 0,8968 | 17 | −0,0002 |
| CatBoost 80 | 50% | 0,8489 | 0,8414 | 0,8404 | 0,8426 | 17 | −0,0063 |
| CatBoost 80 | 75% | 0,8979 | 0,8885 | 0,8854 | 0,8839 | 16 | −0,0140 |

`ΔAP` là AP hybrid trừ AP đủ cột, làm tròn bốn chữ số. Các AP HGB chọn cột và số cột là **trung bình hai seed**, còn đối chứng đủ cột được chạy một lần; đừng diễn giải chênh vài phần nghìn như bằng chứng thống kê. Chi tiết Accuracy, Precision, Recall, F1, fitness và thời gian nằm ở `hco_vnls_validation.csv`, `hco_vnls_du_feature_validation.csv`, `hco_vnls_lightgbm_validation.csv` và `hco_vnls_catboost_validation.csv`.

**Kết luận thực nghiệm trung thực:** Trong sáu trường hợp evaluator × cutoff, hybrid giảm số cột nhưng **không vượt AP của chính evaluator đủ cột**. LightGBM 75% là đánh đổi đáng nghiên cứu: giữ 17/38 cột (giảm 21), AP `0,8968` so với `0,8970`, Recall đều khoảng `0,6898`, Accuracy `0,8741` so `0,8735`; đây là *gần bằng* chứ không phải tăng AP. CatBoost 75% là ví dụ ngược: 16 cột nhưng AP từ `0,8979` xuống `0,8839`, Recall từ `0,6847` xuống `0,6470`. HGB 75% hybrid có AP cao hơn HCO và VNLS riêng trong pilot nhưng vẫn dưới hàng đủ cột. Lợi ích của chọn cột phụ thuộc cutoff và evaluator; chưa có bằng chứng hybrid luôn thắng.

**Thời gian không thể bỏ qua:** với CatBoost 80 cây, riêng tìm mask pilot có thể mất khoảng 100–155 giây mỗi phương pháp/mốc, còn fit cuối khoảng 4–6 giây. Ngân sách 8 mask là nhỏ; số liệu này không chứng minh cực tiểu/toàn cục hoặc lợi ích runtime lúc huấn luyện. Tập feature gọn có thể hữu ích cho giải thích và triển khai, nhưng cần kiểm tra lại bằng nhiều seed, ablation và tập thời gian mới. Một cột được chọn một lần **chưa phải bằng chứng nó quan trọng một cách ổn định**.

## 6. Phần lịch sử được tách khỏi kết luận hiện tại

Một số thăm dò học sâu, ensemble, ngưỡng và test đã từng được thực hiện trong lịch sử cục bộ. Chúng không thuộc năm mô hình và chuỗi notebook công bố lần này. Test cũ đã từng được xem nên không thể coi là một holdout nguyên sơ để lựa chọn lại mô hình. Các kết luận chính trong báo cáo dựa trên validation; phần kết quả âm của HCO–VNLS vẫn được giữ nguyên.

## 7. Đã làm được gì, chưa làm gì và bước tiếp

**Đã làm:** kiểm kê đủ bảy nguồn, kiểm tra khóa và cutoff; tạo năm bảng dữ liệu theo thời gian với 38 feature; cố định split theo sinh viên; chạy HGB và ba boosting ở năm mốc; chạy LogisticRegression ở 50%/75%; lập bảng đúng năm model; chạy pilot HCO/VNLS/hybrid trên HGB, LightGBM, CatBoost với đối chứng đủ cột; ghi cả trường hợp giảm AP. Chín notebook trong luồng `00`–`05c` đã có output.

**Chưa làm:** chưa có validation/test ngoài thời gian thật sự mới; chưa lặp nhiều seed/budget lớn cho LightGBM/CatBoost; chưa có ablation tách đóng góp riêng của feature cửa sổ; chưa đưa HCO/VNLS vào XGBoost và LogisticRegression theo cùng protocol; chưa đánh giá chất lượng gợi ý hỗ trợ học tập thực tế. Không được đồng nhất AP/Accuracy phân loại với **chất lượng gợi ý**. Chưa có cơ sở nói đã đạt Accuracy 90–93% hoặc HCO–VNLS tăng mọi chỉ số.

**Ưu tiên tiếp:** (1) xác định tập kỳ học mới chưa nhìn thấy và khóa protocol; (2) ablation nhóm đặc trưng thời gian trên cùng split; (3) lặp seed, tăng ngân sách mask có kiểm soát và so cùng evaluator/đủ cột/ngẫu nhiên cùng số cột; (4) đánh giá Pareto AP–Recall–số cột–thời gian; (5) nếu xây dựng gợi ý hỗ trợ, định nghĩa tiêu chí đánh giá độc lập với phân loại. Không tune theo test cũ.

## 8. Đường dẫn kiểm chứng và trạng thái GitHub

| Câu hỏi | Notebook / dữ liệu tổng hợp |
|---|---|
| Nguồn và khóa gộp? | `01_kiem_tra_du_lieu_va_ro_ri.ipynb`; `ket_qua/kiem_ke_7_bang.csv`. |
| Cutoff, feature và số hàng? | `02_tao_dac_trung_theo_thoi_gian.ipynb`; `ket_qua/tong_quan_cac_moc.csv`. |
| Năm mô hình ra chỉ số nào? | `03_so_sanh_cac_moc_cutoff.ipynb`, `04_catboost_lightgbm_xgboost.ipynb`, `04c_thu_them_mo_hinh.ipynb`; `ket_qua/nam_mo_hinh_validation.csv`; `hinh/thu_them_mo_hinh_validation.png`. |
| HCO/VNLS/hybrid tạo mask ra sao? | `05_hco_vnls_tren_boosting.ipynb`, `05b_hco_vnls_lightgbm.ipynb`, `05c_hco_vnls_catboost.ipynb`; các CSV `hco_vnls_*validation.csv`; hình hội tụ trong `hinh/`. |
| Phạm vi công bố? | Chín notebook `00`–`05c`, các bảng tổng hợp, bốn hình và hai bản báo cáo; không kèm dữ liệu cấp sinh viên hoặc thí nghiệm MLP/ensemble/test lịch sử. |

**Phạm vi công bố:** repo riêng tư `phantrongnguyen/personalized-learning`, nhánh `aBaoN9/clht-gb-github`. Chỉ phát hành kết quả tổng hợp, hình, notebook đã chạy và báo cáo; không đưa CSV cấp sinh viên, môi trường ảo hoặc bảy nguồn dữ liệu chưa được xác minh quyền phân phối.
