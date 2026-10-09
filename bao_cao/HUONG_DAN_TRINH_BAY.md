# Nội dung trình bày về LightGBM và hai mô hình đối chứng

## 1. Phần có thể báo cáo

Đã có cơ sở để trình bày **lý thuyết LightGBM, hai đối chứng CatBoost/XGBoost và kết quả thực nghiệm**. Đây là báo cáo nghiên cứu hiện tại, không phải tuyên bố đã nghiệm thu toàn bộ khóa luận. Các thí nghiệm đối chứng chạy ngày 07/10/2026; nội dung có thể dùng chuẩn bị buổi trình bày ngày 08/10/2026.

| Nội dung cần trình bày | Nguồn | Trạng thái |
|---|---|---|
| Lý thuyết LightGBM, ví dụ xuyên suốt và công thức | [Word LightGBM](../apps/docs/Co_so_ly_thuyet_LightGBM_va_ung_dung_trong_du_bao_nguy_co_hoc_tap.docx) | Đã có; dùng phân biệt lý thuyết chung với cấu hình đã chạy. |
| Bảy bảng, tiền xử lý, cutoff và chia nhóm | [Notebook 01](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/01_kiem_tra_du_lieu_va_ro_ri.ipynb), [02](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/02_tao_dac_trung_theo_thoi_gian.ipynb) | Có output; CSV cấp lượt học không chia sẻ. |
| HCO/VNLS chấm mask bằng LightGBM | [Notebook 05b](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/05b_hco_vnls_lightgbm.ipynb) | Có đủ biến/HCO/VNLS/hybrid tại 50%/75%. |
| Vì sao bộ biến có bằng chứng | [Notebook 09](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/09_kiem_chung_dac_trung_hco_vnls.ipynb) | Nhiều seed, mask ngẫu nhiên cùng kích thước và ablation. |
| Model triển khai được tạo thế nào | [Notebook 10](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/10_dong_goi_model_hco_vnls_lightgbm_75.ipynb) | Khóa mask, fit train + validation, lưu/nạp thử model. |
| CatBoost để so sánh | [Notebook 06](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/06_so_sanh_catboost_voi_lightgbm_50_75.ipynb) và mục 4 bên dưới | Chạy xong; có lý thuyết, tham số, bảng và hình. |
| XGBoost để so sánh | [Notebook 07](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/07_so_sanh_xgboost_voi_lightgbm_50_75.ipynb) và mục 5 bên dưới | Chạy xong; gộp 24 trường hợp của ba bộ học. |

**Chưa có:** test độc lập mới/kỳ học mới, tối ưu tham số hoàn chỉnh cho hai đối chứng, kết quả chấm độ phù hợp gợi ý từ người dùng, hoặc bằng chứng can thiệp làm tăng điểm. Không báo cáo các phần này như đã hoàn thành.

## 2. Dữ liệu và giao thức cần nói trước

Đơn vị phân tích là một lượt đăng ký sinh viên–học phần–kỳ học. Bảy nguồn gồm studentInfo, studentRegistration, courses, studentVle, vle, studentAssessment và assessments. Tổng hợp các bảng sự kiện theo khóa và thời gian trước khi ghép, tránh nhân bản hàng từ phép nối nhiều–nhiều.

Cutoff 50%/75% là ngày quan sát `floor(tỷ lệ × module_presentation_length)`. Không lấy 50%/75% số dòng. Dữ liệu sau ngày quan sát không được dùng. Hai cutoff có thể có số lượt học khác nhau do điều kiện đăng ký/rút học phần.

Bảng 75% có **23.159 dòng, 47 cột**, trong đó **38 cột ứng viên**. Chín cột định danh/nhãn/cấu hình không đưa vào dự báo. Chia theo sinh viên, giữ nguyên split seed 41: **16.297 train, 3.415 validation, 3.447 test**. Tỷ lệ 70%/15%/15% là tỷ lệ sinh viên, không nhất thiết đúng tỷ lệ lượt học.

Điền thiếu số bằng median và chữ bằng mode chỉ học từ train trong pipeline LightGBM/XGBoost; chữ tiếp tục One-Hot. CatBoost giữ category gốc, chữ thiếu dùng THIEU, số thiếu dùng NaN. Các bước được fit riêng trong train của mỗi fold, không học quy tắc điền thiếu từ cả bảng trước khi chia.

## 3. LightGBM trong bài này

### 3.1 Vì sao cần học nhiều cây?

Một cây chia dữ liệu thành các nhóm theo điều kiện trên đặc trưng. Boosting tạo nhiều cây nối tiếp để điều chỉnh sai số mà mô hình hiện tại còn mắc. Với bài toán nhị phân, điểm thô F chuyển thành xác suất nguy cơ qua sigmoid:

$$p(x)=\frac{1}{1+\exp(-F(x))}$$
$$F_t(x)=F_{t-1}(x)+\eta f_t(x)$$

p là xác suất thuộc Fail/Withdrawn; eta là learning rate; f_t là cây bổ sung ở vòng t. Không hiểu f_t là một cây độc lập dự đoán lại từ đầu hoặc mỗi cây chỉ học một biến.

### 3.2 Những điểm cần minh họa

- Histogram nhóm giá trị đặc trưng vào bin để tích lũy thống kê và tìm split hiệu quả hơn. Đây không phải cắt bớt sinh viên bằng cutoff.
- Leaf-wise ưu tiên mở lá có mức cải thiện phù hợp nhất thay vì bắt buộc phát triển đồng đều theo tầng. Cần giới hạn độ phức tạp để tránh các nhánh quá chuyên biệt.
- GOSS là một cơ chế lấy mẫu theo độ lớn gradient; EFB là tổ chức các biến thưa ít xung đột để giảm chi phí. Hai cơ chế này không phải HCO–VNLS chọn biến đầu vào.

Word đi sâu gradient, Hessian, split, leaf-wise, GOSS/EFB và ví dụ nhỏ. Cấu hình đang dùng là **80 cây, learning rate 0,055, num_leaves 15, min_child_samples 35**, seed 41, bốn luồng. Model hiện tại không cấu hình GOSS; không nói tốc độ thu được là nhờ GOSS. Chưa có bằng chứng về số bundle EFB thực sự tạo ra, không suy ra điều đó từ 17 → 30 cột.

### 3.3 HCO–VNLS làm gì trước và trong việc học?

Tạo 38 biến quan sát được trước, rồi HCO/VNLS thử các mask giữ/bỏ biến. Với mỗi mask, bộ học được huấn luyện trong GroupKFold của train để chấm AP; bộ chọn không tự sinh thêm biến mới.

$$Fitness(m)=0,85\,\overline{AP}_{train-CV}(m)+0,15\left(1-\frac{|m|}{38}\right)$$

m là mask; |m| là số biến giữ. Thành phần thứ hai thưởng độ gọn, nên fitness tốt hơn không luôn nghĩa AP validation cao hơn. Ngân sách 8 mask rất nhỏ so với tất cả tổ hợp 38 biến; không chứng minh tối ưu toàn cục. VNLS hiện tại chủ yếu lật một bit, cần đối chiếu bài báo gốc trước khi khẳng định đã triển khai đầy đủ lý thuyết.

Sau khi khóa 17 biến hybrid tại 75%, model app fit trên **19.712 lượt học train + validation**, test không dùng fit. Pipeline mã hóa thành 30 cột số. Kết quả validation dùng trình bày ở mục 6 là các bản fit train-only, không lấy artifact cuối dự đoán chính validation rồi gọi là đánh giá độc lập.

## 4. CatBoost: đối chứng xử lý biến phân loại

### 4.1 Câu hỏi nghiên cứu

Dataset có các biến như học phần, kỳ học, nhóm tuổi hoặc học vấn. CatBoost phù hợp làm đối chứng cho pipeline dùng One-Hot vì có cơ chế xử lý category. Câu hỏi là: giữ category gốc có giúp cải thiện xếp hạng/nguy cơ trong cùng dữ liệu và giao thức không? Không mặc định nhiều category là CatBoost chắc chắn thắng.

### 4.2 Cơ chế cần hiểu

Mã hóa category bằng trung bình nhãn của toàn bộ dữ liệu có thể đưa nhãn của chính hàng đang học vào đặc trưng của nó. Ý tưởng ordered target statistics dùng một thứ tự của mẫu và chỉ dựa vào các mẫu trước đó, kèm prior làm trơn:

$$TS_i(c)=\frac{\sum_{j\prec i,\,c_j=c}y_j+a\mu}{\sum_{j\prec i,\,c_j=c}1+a}$$

c là một category; j trước i theo thứ tự xét; mu là prior; a là mức làm trơn. Đây là công thức minh họa nguyên lý, không khẳng định mọi cột được thư viện mã hóa đúng duy nhất theo công thức này với một a cụ thể trong thí nghiệm.

Ordered boosting là một ý tưởng liên quan nhằm giảm prediction shift; cần phân biệt với xử lý category. Cây đối xứng dùng cùng điều kiện chia ở một mức cho các nút cùng tầng, tạo cấu trúc đều và có thể giới hạn độ linh hoạt.

### 4.3 Cấu hình và điều đã kiểm chứng

Thử nghiệm dùng **80 cây, depth 5, learning rate 0,055, L2 bằng 5**, CPU, seed 41, bốn luồng. Category thiếu dùng THIEU, số thiếu để NaN. Không học bất kỳ thống kê tiền xử lý nào từ validation.

Đã kiểm tra `get_all_params()` của cấu hình hybrid 75% fit lại trên train: **boosting_type = Plain, grow_policy = SymmetricTree, nan_mode = Min**. Vì vậy, có thể giải thích ordered boosting trong lý thuyết CatBoost, nhưng **không nói thí nghiệm này đã bật Ordered boosting**. Nói “giữ category gốc” chính xác hơn nói “đã chứng minh ưu điểm ordered boosting”.

## 5. XGBoost: đối chứng boosting có regularization

### 5.1 Câu hỏi nghiên cứu

XGBoost là một bộ học boosting cây có mục tiêu gồm độ khớp dữ liệu và chi phí độ phức tạp. Dùng nó để kiểm tra chất lượng khi vẫn giữ median/mode/One-Hot như LightGBM, tránh thay cả biểu diễn category như CatBoost. Mask vẫn có thể khác, nên chưa tách riêng tác động bộ học khỏi chọn biến.

### 5.2 Từ gradient đến giá trị lá

Với logloss nhị phân, các đại lượng tại xác suất hiện tại là:

$$g_i=p_i-y_i,\qquad h_i=p_i(1-p_i)$$

G là tổng gradient, H là tổng Hessian trong một lá. Trong trường hợp không dùng L1, giá trị lá điển hình theo xấp xỉ bậc hai là:

$$w^*=-\frac{G}{H+\lambda}$$

lambda điều chỉnh regularization: giá trị lớn làm mức cập nhật thận trọng hơn, không đảm bảo Accuracy tăng. Gain của split hai nhánh có dạng:

$$Gain=\frac{1}{2}\left[\frac{G_L^2}{H_L+\lambda}+\frac{G_R^2}{H_R+\lambda}-\frac{(G_L+G_R)^2}{H_L+H_R+\lambda}\right]-\gamma$$

L/R là hai nhánh; gamma là chi phí thêm split. Gain này chấm một điều kiện chia cây, **khác fitness chấm cả mask đặc trưng** ở HCO/VNLS.

### 5.3 Cấu hình đã chạy

**80 cây, max_depth 4, learning rate 0,055, L2 bằng 1, L1 bằng 0**, hist trên CPU, seed 41, bốn luồng; subsample/colsample đều bằng 1. Không early stopping dựa trên validation, không dò threshold. Đây là cấu hình đối chứng ban đầu, không phải XGBoost đã tối ưu tốt nhất. Cùng 80 cây không có nghĩa cùng chi phí/độ phức tạp với hai bộ học còn lại.

## 6. Kết quả phải đặt cạnh lý thuyết

Nguồn đầy đủ: [bảng 24 trường hợp](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/so_sanh_ba_bo_hoc_50_75.csv). Có đủ biến/HCO/VNLS/hybrid cho từng bộ học và cutoff. Bảng dưới chỉ lấy hybrid để trình bày gọn:

| Cutoff | Bộ học + HCO–VNLS | Biến | Giảm so 38 biến | Accuracy | Precision risk | Recall risk | F1 risk | AP |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 50% | LightGBM | 16 | 57,89% | 80,54% | 84,44% | 60,14% | 70,25% | 0,8452 |
| 50% | CatBoost | 17 | 55,26% | 80,37% | 85,14% | 58,92% | 69,64% | 0,8426 |
| 50% | XGBoost | 17 | 55,26% | 80,87% | 86,07% | 59,57% | 70,41% | 0,8488 |
| 75% | LightGBM | 17 | 55,26% | 87,41% | 92,21% | 68,98% | 78,92% | 0,8968 |
| 75% | CatBoost | 16 | 57,89% | 85,89% | 91,52% | 64,70% | 75,80% | 0,8839 |
| 75% | XGBoost | 17 | 55,26% | 87,32% | 93,08% | 67,95% | 78,55% | 0,8941 |

- Tại 50%, XGBoost hybrid nhỉnh Accuracy/AP/F1 nhưng Recall thấp hơn LightGBM. Không kết luận thắng mọi chỉ số.
- Tại 75%, hybrid LightGBM nhỉnh Accuracy/Recall/F1/AP; XGBoost nhỉnh Precision. Chênh nhỏ chưa được chứng minh có ý nghĩa thống kê.
- CatBoost đủ 38 biến tại 75% đạt AP **0,8979**, hybrid chỉ **0,8839**. Việc giảm biến là đánh đổi trong pilot, không tự động tăng chất lượng. LightGBM đủ biến tại 75% cũng có AP **0,8970**, hơi cao hơn hybrid **0,8968**.
- Giữ model app LightGBM 75% hiện tại. Không thay artifact chỉ từ một cấu hình/một seed đối chứng.

Accuracy là tỷ lệ đúng toàn bộ; Precision risk là tỷ lệ cảnh báo đúng; Recall risk là tỷ lệ ca nguy cơ thật được phát hiện; F1 risk cân bằng Precision/Recall lớp nguy cơ. Weighted F1 khác F1 risk. AP đánh giá xếp hạng qua nhiều ngưỡng; AUC và Brier cũng có trong CSV. Std AP CV là độ phân tán ba fold của mask, không phải khoảng tin cậy.

Thời gian được tách thành tìm mask, fit và dự đoán. Thời gian tìm mask LightGBM mới để trống vì dùng mask đã chốt, không phải tìm kiếm miễn phí. Các số đo một lần, không đủ khẳng định benchmark tốc độ hoặc tiết kiệm tài nguyên chắc chắn.

So sánh giữa hai cutoff còn chịu ảnh hưởng của tập lượt học đủ điều kiện tại mỗi thời điểm. Giữ cùng phép chia sinh viên không có nghĩa hai validation chứa đúng cùng các lượt học; không quy toàn bộ mức tăng chỉ số ở 75% riêng cho việc quan sát lâu hơn. So các bộ học trong cùng cutoff là đối chứng trực tiếp hơn.

## 7. Hình và bằng chứng kiểm chứng

- [Giải thích bảy hình](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/hinh/GIAI_THICH_HINH.md): nguồn bảng/cell, trục và ý nghĩa của từng hình.
- [Giải thích các bảng](../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua/GIAI_THICH_KET_QUA.md): chỉ số, tên biến và các bảng đối chứng/ablation.
- Tần suất chọn biến, mask ngẫu nhiên cùng kích thước và bỏ từng biến là các bằng chứng bổ sung cho bộ chọn. Được chọn không đồng nghĩa quan trọng tuyệt đối hoặc tạo hiệu quả tăng điểm.
- Hai notebook mới: cell **6** kiểm tra dữ liệu; **8** cấu hình/tiền xử lý; **10** chấm mask; **12** chạy và đo; **14** tên biến/delta; **16** hình/bảng; **18** nhận xét. Cell **21** notebook 07 gộp bảng. Đếm cả Markdown từ 1.

## 8. Bố cục slide có thể dùng

| Slide | Mục tiêu riêng | Nội dung/bằng chứng |
|---|---|---|
| 1 | Đặt câu hỏi dự báo sớm | Nguy cơ Fail/Withdrawn tại 50%/75%, không chờ toàn kỳ. |
| 2 | Cho biết dữ liệu đi vào đâu | Bảy bảng → bảng cutoff → 38 biến; tách nhãn/ID, chia theo sinh viên. |
| 3 | Hiểu boosting | Nhiều cây cập nhật điểm thô, sigmoid và learning rate; ví dụ sư phạm trong Word. |
| 4 | Hiểu LightGBM xây cây | Gradient/Hessian, histogram, split gain, leaf-wise và giới hạn số lá. |
| 5 | Phân biệt lý thuyết với cấu hình thực | GOSS/EFB là cơ chế thư viện; model hiện tại không bật GOSS, không suy ra số bundle EFB. |
| 6 | Giữ HCO–VNLS làm trọng tâm | Mask, AP train-CV, fitness có thưởng độ gọn, kiểm chứng biến. |
| 7 | Hiểu lý do chọn CatBoost | Category, ordered target statistics, cây đối xứng; thực nghiệm dùng Plain, không gọi là đã bật Ordered. |
| 8 | Hiểu lý do chọn XGBoost | Mục tiêu regularized, giá trị lá/gain và hist; cùng pipeline tiền xử lý với LightGBM. |
| 9 | Cho thấy so sánh có kiểm soát | Split/cutoff/seed/threshold/budget giữ cố định; các pipeline vẫn khác độ phức tạp. |
| 10 | Kết quả mô hình tại 50% | Bảng/ảnh cùng cutoff; Accuracy phải đọc cạnh Recall/AP và đủ biến. |
| 11 | Kết quả mô hình tại 75% | Hybrid LightGBM, CatBoost, XGBoost; Precision XGBoost cao hơn nhưng Recall thấp hơn. |
| 12 | Nêu điều đã và chưa chứng minh | Model triển khai không đổi; còn thiếu kiểm chứng độc lập và đánh giá chất lượng gợi ý. |

Không bắt buộc đủ 12 slide; có thể gộp 3–5 tùy thời lượng. Mỗi slide chỉ làm một nhiệm vụ, đưa công thức/hình ở nơi cần giải thích cơ chế, không liệt kê tên hàm Python thay lý thuyết. Các số minh họa sư phạm phải ghi rõ là ví dụ, không gọi là hàng dữ liệu thực hoặc kết quả đo.

## 9. Model, ứng dụng và tài liệu Word

[Streamlit](../streamlit-web/app.py) nạp [model đã lưu](../streamlit-web/model_hco_vnls_lightgbm_cutoff75.joblib); [metadata](../apps/backend/model_store/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json) ghi schema và hash. Không tìm lại mask cho từng người. Gợi ý kết hợp kết quả dự báo và bằng chứng tương tác/bài nộp, không phải một mô hình thứ hai đã chứng minh hiệu quả can thiệp.

[Chương ứng dụng Word](../apps/docs/Bao_5.docx) mô tả ứng dụng React/FastAPI đã có trong `apps/`; không tự coi các chi tiết kỹ thuật/ảnh nghiệm thu đó là của Streamlit. Bản Word LightGBM ở đầu tài liệu là nguồn chính cho phần lý thuyết ngày mai; không sửa hoặc thay công thức Word trong lần dọn nhánh này.

## 10. Tài liệu lý thuyết để đối chiếu

1. [LightGBM — Features, tài liệu chính thức](https://lightgbm.readthedocs.io/en/stable/Features.html).
2. [LightGBM — Parameters, tài liệu chính thức](https://lightgbm.readthedocs.io/en/stable/Parameters.html).
3. [Prokhorenkova và cộng sự, 2018 — CatBoost: unbiased boosting with categorical features](https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html).
4. [Chen và Guestrin, 2016 — XGBoost: A Scalable Tree Boosting System](https://arxiv.org/abs/1603.02754).
5. [XGBoost — Introduction to Boosted Trees, tài liệu chính thức](https://xgboost.readthedocs.io/en/stable/tutorials/model.html).

Phiên bản thực nghiệm là LightGBM 4.7.0, CatBoost 1.2.10 và XGBoost 3.1.2, được ghi trong JSON giao thức. Tài liệu stable có thể mới hơn; dùng để đối chiếu lý thuyết, không đổi tham số hoặc nâng thư viện rồi coi là cùng lần chạy.
