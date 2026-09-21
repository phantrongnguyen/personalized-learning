# Hướng dẫn đọc các notebook nghiên cứu

Tài liệu này giải thích vai trò của từng notebook trong thư mục `notebooks/`. Người mới không cần đọc code ngay từ đầu. Hãy xem notebook như một chuỗi câu trả lời cho các câu hỏi nghiên cứu: dữ liệu là gì, tạo dữ liệu dự đoán ra sao, model học máy làm mốc thế nào, HCO/VNLS tìm đặc trưng ra sao, rồi kiểm tra kết quả ở nhiều điều kiện và nhiều thời điểm trong học kỳ.

## 1. Bức tranh toàn bộ

Đề tài có hai phần phối hợp với nhau:

- **Model học máy**: học cách dự đoán `risk`, trong đó `risk=1` là sinh viên có kết quả cuối khóa `Fail` hoặc `Withdrawn`, còn `risk=0` là `Pass` hoặc `Distinction`.
- **HCO, VNLS và HCO+VNLS**: không thay thế model học máy. Các thuật toán này tìm một **bộ đặc trưng** (một mask gồm các cột nên giữ lại) để model học máy dự đoán với chất lượng và độ gọn phù hợp.

Vì vậy, cách hiểu đúng là:

```text
7 bảng OULAD
    ↓
gộp thành dữ liệu theo từng enrollment
    ↓
chỉ giữ thông tin có trước cutoff dự đoán
    ↓
tạo nhãn risk và các đặc trưng
    ↓
chia train / validation / test theo id_student
    ↓
chạy model học máy trên toàn bộ đặc trưng để lấy baseline
    ↓
cho HCO, VNLS, HCO+VNLS chọn bộ đặc trưng
    ↓
đánh giá lại bằng cùng model, cùng dữ liệu và cùng ngân sách
    ↓
tinh chỉnh HGB, kiểm tra nhiều tỷ lệ chia và các mốc học kỳ
```

**Trọng tâm của đề tài là HCO+VNLS.** Các model như HistGradientBoosting, Logistic Regression, RandomForest, ExtraTrees và DecisionTree là những bộ chấm nghiệm hoặc mốc đối chứng để trả lời xem bộ đặc trưng do thuật toán chọn có hữu ích hay không.

## 2. Bảng tổng quan nhanh

| Notebook | Vai trò chính | Câu hỏi được trả lời | Kết quả quan trọng |
|---|---|---|---|
| `01_kham_pha_du_lieu.ipynb` | Hiểu dữ liệu ban đầu | Có những bảng nào, khóa nào, thiếu dữ liệu và nhãn ra sao? | Xác nhận quy mô, cột, missing và phân bố `final_result`. |
| `02_gop_bang_tao_dac_trung.ipynb` | Gộp 7 bảng và tạo đặc trưng | Làm sao biến nhiều bảng thành một dòng dự đoán cho mỗi enrollment? | Tạo bảng gộp và các đặc trưng hành vi, điểm số, hoạt động. |
| `03_chia_tap_va_baseline.ipynb` | Tạo mốc so sánh model | Nếu dùng toàn bộ đặc trưng thì model nào có nền tốt? | HGB mạnh về AP/chất lượng xếp hạng; Logistic Regression hữu ích khi ưu tiên Recall risk. |
| `04_hco_vnls_co_ban.ipynb` | Thử HCO, VNLS, HCO+VNLS lần đầu | Optimizer có thể tìm mask đặc trưng tốt hơn hoặc gọn hơn không? | Tạo kết quả pilot đầu tiên và biểu đồ đánh đổi số cột–AP. |
| `05_tong_hop_quyet_dinh.ipynb` | Đọc và tổng hợp kết quả | Từ các bảng đã chạy, nên giữ model/phương pháp nào để nghiên cứu tiếp? | Tính `mean_ap`, `std_ap`, Recall, F1, số cột và thời gian để hỗ trợ quyết định. |
| `06_hco_vnls_trong_tam.ipynb` | Thí nghiệm trọng tâm đúng đề tài | HCO+VNLS có hơn HCO và VNLS khi điều kiện được giữ công bằng không? | So sánh 3 phương pháp trên cùng model, nhiều seed, cùng alpha và ngân sách. |
| `07_tien_xu_ly_chia_tap_va_so_sanh.ipynb` | Kiểm tra độ chặt của quy trình | Tiền xử lý có hợp lý không, và kết quả có đổi theo tỷ lệ chia không? | Audit tiền xử lý; so sánh 6/2/2, 7/1.5/1.5, 8/1/1, 7.5/1.5/1 và 5/2.5/2.5. |
| `08_toi_uu_hgb_va_hco_vnls.ipynb` | Tối ưu model rồi chạy lại thuật toán trọng tâm | HGB tuning có giúp không, và HCO+VNLS còn có lợi trên HGB mới không? | HGB tuning tăng Recall risk; HCO dẫn đầu AP, HCO+VNLS gọn và dẫn đầu fitness trong pilot. |
| `09_so_sanh_cac_moc_hoc_ky.ipynb` | So sánh thời điểm cảnh báo | Nên dự đoán ở 25%, 50% hay 75% tiến trình học kỳ? | 75% dễ dự đoán nhất; 50% là điểm cân bằng tốt hơn cho can thiệp sớm. |

## 3. Giải thích từng notebook

### 3.1. `01_kham_pha_du_lieu.ipynb` — dữ liệu ban đầu là gì?

#### Notebook này làm gì?

Đây là bước mở đầu, chưa huấn luyện model và chưa chạy HCO/VNLS. Notebook đọc bảy bảng OULAD, đếm số dòng, số cột và tổng số ô thiếu. Sau đó notebook xem riêng `studentInfo.csv` để kiểm tra phân bố `final_result` và số enrollment bị trùng khóa.

#### Vì sao phải có bước này?

Nếu chưa hiểu khóa và ý nghĩa từng bảng, việc gộp dữ liệu rất dễ sai. Ví dụ, một sinh viên có thể học nhiều module hoặc nhiều kỳ. Chỉ dùng `id_student` làm khóa có thể trộn những enrollment khác nhau thành một dòng, tạo ra dữ liệu sai và thậm chí gây rò rỉ thông tin.

#### Cần chú ý khi đọc

- `id_student` là mã sinh viên.
- `code_module` và `code_presentation` giúp phân biệt sinh viên học module nào, ở kỳ nào.
- `final_result` là kết quả cuối khóa, được dùng sau này để tạo nhãn `risk`.
- Missing không tự động có nghĩa là lỗi; có thể là sinh viên không có hoạt động hoặc bảng đó không áp dụng cho enrollment. Phải hiểu ngữ cảnh trước khi điền hoặc loại.

#### Output chính

- Bảng tổng quan quy mô và missing của bảy file.
- Biểu đồ `phan_bo_nhan.png`, cho thấy số lượng từng loại kết quả cuối khóa.

#### Notebook sau sử dụng gì?

Notebook `02_gop_bang_tao_dac_trung.ipynb` dùng thông tin khóa và schema đã kiểm tra ở đây để gộp dữ liệu đúng cấp enrollment.

### 3.2. `02_gop_bang_tao_dac_trung.ipynb` — từ 7 bảng thành một dataset

#### Notebook này làm gì?

Notebook gọi các hàm tái sử dụng trong `clht_code/data.py`, đọc bảy bảng và gộp chúng theo một enrollment: tổ hợp `id_student + code_module + code_presentation`. Các bảng hành vi có nhiều dòng cho một enrollment được tổng hợp thành các đặc trưng như số click, số ngày hoạt động, điểm, bài nộp trễ hoặc bài còn thiếu.

#### Vì sao gộp ở đây?

Model cần một bảng dạng:

```text
mỗi dòng = một enrollment của một sinh viên trong một module và một kỳ
mỗi cột = một thông tin dùng để dự đoán
```

Nếu để nguyên bảy bảng, model không biết cách tự nối chúng theo đúng quan hệ. Gộp trước cũng giúp tất cả model và optimizer dùng cùng một dữ liệu đầu vào, tránh trường hợp mỗi thí nghiệm tự gộp theo một cách khác.

#### Những điểm cần kiểm soát

- Không gộp chỉ theo `id_student`.
- Các bảng một-nhiều như VLE hoặc assessment phải được tổng hợp trước khi nối về cấp enrollment.
- Thời gian và điểm số phải được giới hạn theo cutoff khi tạo dữ liệu dự đoán; không được đưa thông tin tương lai vào đặc trưng.
- Nhãn cuối khóa chỉ dùng để tạo mục tiêu, không được biến thành feature.

#### Output chính

- Khi chạy với đủ dữ liệu nguồn, notebook ghi bảng gộp vào `ket_qua/du_lieu_da_gop_tao_dac_trung.csv`. Bản GitHub có thể không kèm file trung gian này để tránh đưa dữ liệu sinh viên đã xử lý vào package.
- Biểu đồ đặc trưng theo `final_result`, gồm điểm trung bình và click trung bình.

#### Mối liên hệ với code Python

Phần logic gộp dài được đóng gói ở `clht_code/data.py` để không phải chép lại nhiều lần. Notebook vẫn là nơi ghi lại tham số, cách gọi hàm và output nghiên cứu; file `.py` chỉ giữ phần dùng lại.

### 3.3. `03_chia_tap_va_baseline.ipynb` — có dataset rồi thì model nào làm mốc?

#### Notebook này làm gì?

Notebook tạo dữ liệu tại cutoff 50%, lấy danh sách feature, tạo nhãn `risk`, rồi chia dữ liệu thành train, validation và test. Việc chia theo nhóm `id_student` bảo đảm các enrollment của cùng một sinh viên không rơi vào nhiều tập.

Sau đó notebook chạy các model học máy baseline trên cùng feature và cùng split. Các model này gồm những mô hình tuyến tính và phi tuyến, trong đó HGB, Logistic Regression, RandomForest, ExtraTrees và DecisionTree giúp tạo các góc nhìn khác nhau.

#### Vì sao phải chạy baseline trước HCO/VNLS?

HCO/VNLS không trực tiếp dự đoán. Chúng cần một model bên trong objective để chấm một mask feature. Nếu chưa biết model nền nào phù hợp, ta không biết mask đang tốt vì thuật toán chọn feature hay vì model vốn đã mạnh.

Baseline trả lời câu hỏi:

> Với toàn bộ feature và cùng dữ liệu, model nào tạo nền tảng tốt nhất cho bước chọn feature?

#### Cách đọc các kết quả

- **AP risk**: model xếp hạng sinh viên nguy cơ cao tốt đến đâu, không phụ thuộc hoàn toàn vào một threshold.
- **Recall risk**: trong tất cả sinh viên thật sự risk, bắt được bao nhiêu người.
- **F1/Weighted F1**: cân bằng giữa Precision và Recall; Weighted F1 tính trọng số theo số lượng mỗi lớp.
- **Accuracy**: tỷ lệ dự đoán đúng chung, nhưng không nên dùng một mình nếu nhãn lệch.

#### Kết luận baseline hiện có

- HGB là baseline mạnh về AP và chất lượng tổng thể khi mục tiêu là xếp hạng risk.
- Logistic Regression đáng giữ lại vì có Recall risk tốt trong một số cấu hình.
- RandomForest và ExtraTrees là đối chứng phi tuyến; DecisionTree dễ giải thích nhưng thường kém ổn định/chất lượng hơn.

#### Output chính

- `ket_qua/ket_qua_mo_hinh_co_so.csv`: metric của các model baseline.
- `hinh/ap_mo_hinh_co_so.png`: so sánh AP risk trung bình.
- Một bảng test sau khi ứng viên đã được khóa. Test chỉ dùng để báo cáo cuối, không dùng để chọn model trong quá trình tìm kiếm.

### 3.4. `04_hco_vnls_co_ban.ipynb` — thử cơ chế tối ưu lần đầu

#### Notebook này làm gì?

Notebook dùng model học máy trong objective để chấm các mask feature. Ba phương pháp được thử là:

- **HCO**: đối chứng tìm kiếm theo hướng toàn cục.
- **VNLS**: đối chứng tìm kiếm lân cận/cục bộ.
- **HCO+VNLS**: kết hợp tìm kiếm rộng với cải thiện lân cận; đây là phương pháp đề tài quan tâm.

Mỗi mask bật/tắt một feature. Với mỗi mask, model được đánh giá bằng objective có kết hợp chất lượng dự đoán và mức phạt số feature. Notebook ghi lại AP CV, số feature được chọn, số lần gọi objective và thời gian.

#### Vì sao chưa thể kết luận ngay hybrid thắng?

Một lần chạy có thể phụ thuộc seed, alpha, số lần đánh giá và model bên trong. Hybrid có thể ít feature hơn nhưng AP thấp hơn; hoặc AP cao hơn nhưng do ngân sách lớn hơn. Vì vậy notebook này là pilot để phát hiện tín hiệu, chưa phải kết luận cuối.

#### Output chính

- `ket_qua/ket_qua_hco_vnls.csv`: kết quả từng method và seed.
- `hinh/danh_doi_bo_toi_uu.png`: nhìn quan hệ giữa số feature và AP CV.

### 3.5. `05_tong_hop_quyet_dinh.ipynb` — biến nhiều bảng số liệu thành quyết định

#### Notebook này làm gì?

Notebook này chủ yếu đọc các CSV đã có, không tự chạy lại toàn bộ thí nghiệm. Nó gom kết quả theo model hoặc method và tính các thống kê:

- `mean_ap`: AP trung bình qua các run/seed.
- `std_ap`: độ lệch chuẩn của AP; càng nhỏ thì kết quả càng ổn định hơn.
- `mean_recall`: Recall risk trung bình.
- `mean_f1`: Weighted F1 trung bình.
- `mean_features`: số feature trung bình.
- `mean_calls`: số lần gọi objective.
- `mean_seconds`: thời gian trung bình.

#### Vì sao cần notebook tổng hợp?

Nhìn một dòng có AP cao nhất dễ dẫn đến chọn nhầm một run may mắn. Nhìn `mean` cùng `std`, số feature và thời gian sẽ công bằng hơn. Đây cũng là nơi ghi lại lý do chọn hướng tiếp theo, thay vì chỉ ghi “model A tốt hơn”.

#### Cách đọc quyết định

- AP cao nhưng Recall thấp: cân nhắc threshold hoặc model khác trước khi kết luận model kém.
- Ít feature nhưng AP giảm: đó là cải thiện độ gọn, chưa phải cải thiện dự đoán.
- Fitness cao nhưng chỉ đạt được với nhiều objective calls hơn: phải so lại cùng ngân sách.
- Feature được chọn nhiều không có nghĩa là feature đó gây ra rủi ro; đây chỉ là quan sát của quy trình chọn feature.

### 3.6. `06_hco_vnls_trong_tam.ipynb` — thí nghiệm đúng trọng tâm HCO+VNLS

#### Câu hỏi trung tâm

Notebook này kiểm tra trực tiếp:

> Khi dùng cùng dữ liệu, cùng model, cùng alpha, cùng số lần đánh giá và nhiều seed, HCO+VNLS có tìm được bộ feature tốt hơn HCO và VNLS độc lập hay không?

Đây là notebook quan trọng nhất để trình bày vai trò của thuật toán đề tài.

#### Thiết lập công bằng

- Dùng cutoff 50%.
- Chia nhóm theo `id_student`.
- Tìm mask trên train bằng GroupKFold 3 fold.
- Dùng cùng alpha và cùng ngân sách objective calls.
- Chạy nhiều seed để xem kết quả có lặp lại không.
- Validation chỉ chấm nghiệm cuối; không dùng validation để tìm mask.

#### Hai phần thí nghiệm

1. So sánh HCO, VNLS và HCO+VNLS trên cùng các model đánh giá, trong đó HGB đại diện cho AP tốt và Logistic Regression đại diện cho mục tiêu Recall.
2. Kiểm tra alpha cho riêng HCO+VNLS. Alpha cao ưu tiên AP hơn; alpha thấp thưởng cho việc dùng ít feature nhiều hơn. Không được so chéo bảng alpha với bảng phương pháp nếu ngân sách hoặc điều kiện khác nhau.

#### Cách hiểu kết quả

- Hybrid thắng AP trên nhiều seed và nhiều model: có bằng chứng ủng hộ cải thiện chất lượng.
- Hybrid chỉ thắng số feature/fitness: kết luận đúng là hybrid giúp cân bằng chất lượng–độ gọn, chưa nói là dự đoán tốt nhất.
- Kết quả đổi mạnh theo model hoặc alpha: đó là phát hiện nghiên cứu, cho thấy phương pháp phụ thuộc mục tiêu.

#### Output chính

- `ket_qua/so_sanh_hco_vnls_theo_mo_hinh.csv`: kết quả từng model, method và seed.
- `ket_qua/tong_hop_hco_vnls_theo_mo_hinh.csv`: thống kê trung bình để so sánh ổn định hơn.
- `ket_qua/ket_qua_hco_vnls_theo_alpha.csv`: ảnh hưởng của alpha.
- `hinh/so_sanh_hco_vnls_theo_mo_hinh.png`: hình so sánh trực quan.

#### Kết luận pilot cần nhớ

HCO+VNLS là trọng tâm, nhưng không được gọi là “tốt nhất tuyệt đối” nếu chưa thắng lặp lại trên metric được chọn. Trong kết quả hiện tại, hybrid có tín hiệu tốt về fitness và độ gọn ở một số thiết lập; HCO có thể dẫn đầu AP. Hai phát hiện này không mâu thuẫn vì chúng tối ưu các mục tiêu khác nhau.

### 3.7. `07_tien_xu_ly_chia_tap_va_so_sanh.ipynb` — kiểm tra quy trình có đáng tin không?

#### Notebook này làm gì?

Notebook hệ thống hóa ba yêu cầu bắt buộc của nghiên cứu:

1. Có đầy đủ Accuracy, Precision, Recall, F1-score, AP/chất lượng xếp hạng, số cảnh báo và runtime.
2. Có nhiều tỷ lệ chia train/validation/test.
3. Giải thích tiền xử lý và kiểm soát rò rỉ dữ liệu.

#### Các bước tiền xử lý cần hiểu

| Bước | Tác dụng |
|---|---|
| Đọc 7 bảng | Lấy đủ thông tin nhân khẩu, enrollment, assessment, submission, VLE, site và khóa học. |
| Gộp theo enrollment | Đảm bảo một dòng đại diện đúng một sinh viên–module–kỳ. |
| Tạo cutoff | Chỉ dùng dữ liệu đã quan sát đến thời điểm dự đoán, không nhìn tương lai. |
| Tạo nhãn `risk` | Chuyển kết quả cuối khóa thành bài toán phân loại nhị phân. |
| Chia theo `id_student` | Không để cùng sinh viên xuất hiện ở nhiều tập. |
| Fit preprocessing trong train/fold | Không để validation/test ảnh hưởng ngược vào quá trình học. |

#### Các tỷ lệ chia

Các tỷ lệ ghi theo thứ tự **train/validation/test**:

- `6/2/2`: 60% / 20% / 20%.
- `7/1.5/1.5`: 70% / 15% / 15%.
- `8/1/1`: 80% / 10% / 10%.
- `7.5/1.5/1`: 75% / 15% / 10%.
- `5/2.5/2.5`: 50% / 25% / 25%.

Do chia theo group nên số dòng thực tế có thể lệch nhẹ so với phần trăm, nhưng nguyên tắc không tách một sinh viên sang nhiều tập vẫn được giữ.

#### Output chính

- `ket_qua/kiem_tra_tien_xu_ly.csv`: bảng audit các bước tiền xử lý và rủi ro leakage.
- `ket_qua/so_sanh_mo_hinh_theo_ty_le_chia.csv`: metric của model theo từng tỷ lệ chia.
- `hinh/so_sanh_ty_le_chia_tap.png`: biểu đồ so sánh tỷ lệ chia.

#### Notebook này đứng ở đâu trong quy trình?

Nó không thay thế notebook `06`. Nó kiểm tra độ bền của nền dữ liệu và baseline trước khi dùng kết quả đó để đánh giá HCO/VNLS. Khi viết luận văn, nên đặt phần tiền xử lý trước phần thuật toán tối ưu để người đọc hiểu nghiệm được chấm trên dữ liệu nào.

### 3.8. `08_toi_uu_hgb_va_hco_vnls.ipynb` — tối ưu model rồi kiểm tra lại trọng tâm

#### Notebook này làm gì?

Notebook thực hiện hai việc theo thứ tự:

1. Tuning HistGradientBoosting bằng random search trong inner GroupKFold.
2. Dùng HGB đã tuning để chạy lại HCO, VNLS và HCO+VNLS với cùng alpha, ngân sách và nhiều seed.

#### Vì sao phải tuning HGB trước?

Nếu đổi model và đổi luôn optimizer cùng lúc, ta không biết cải thiện đến từ đâu. Notebook này cố định giao thức: chọn cấu hình HGB bằng inner-CV, dùng validation để kiểm tra ngoài quá trình search, rồi mới chạy lại ba phương pháp chọn feature trên HGB mới.

#### Cấu hình HGB tốt hiện tại

- `learning_rate=0.08`
- `max_iter=450`
- `max_leaf_nodes=7`
- `max_depth=3`
- `min_samples_leaf=10`
- `l2_regularization=5.0`
- `class_weight=balanced`
- `early_stopping=False`

So với HGB baseline, cấu hình này tăng Recall risk từ khoảng `0.6336` lên `0.7119`, nhưng Accuracy và Precision risk giảm. Đây là đánh đổi dễ hiểu: model bắt được nhiều ca risk hơn nhưng tạo thêm cảnh báo nhầm.

#### Kết quả HCO/VNLS trên HGB đã tuning

| Phương pháp | AP validation | Recall risk | Weighted F1 | Fitness | Số feature |
|---|---:|---:|---:|---:|---:|
| HCO | **0.8460** | **0.6976** | **0.8001** | 0.7805 | 13.67 |
| HCO+VNLS | 0.8352 | 0.6868 | 0.7944 | **0.7873** | **11.33** |
| VNLS | 0.8307 | 0.6750 | 0.7904 | 0.7766 | 13.00 |

Cách kết luận đúng:

- HCO dẫn đầu AP trong bảng này.
- HCO+VNLS dẫn đầu fitness và dùng ít feature nhất.
- Vì đề tài tập trung HCO+VNLS, hybrid vẫn là phương pháp cần phát triển; nhưng báo cáo phải trung thực rằng nó chưa thắng mọi metric.
- Đây là validation screening. Khi chốt cuối, cần khóa model, feature, alpha và threshold rồi mới mở test một lần.

#### Output chính

- `ket_qua/tim_tham_so_hgb_ngau_nhien.csv`: các cấu hình HGB đã thử.
- `ket_qua/so_sanh_hgb_co_so_va_toi_uu.csv`: HGB baseline và HGB tuning trên validation.
- `ket_qua/ket_qua_hco_vnls_tren_hgb_toi_uu.csv`: từng run HCO/VNLS/hybrid trên HGB mới.
- `ket_qua/tong_hop_hco_vnls_tren_hgb_toi_uu.csv`: tổng hợp theo method.
- `ket_qua/so_sanh_hgb_toi_uu_va_co_so.csv`: bảng đối chiếu trước–sau.
- `hinh/toi_uu_hgb_va_hco_vnls.png`: hình tổng hợp.

### 3.9. `09_so_sanh_cac_moc_hoc_ky.ipynb` — khi nào nên cảnh báo?

#### Notebook này làm gì?

Notebook trình bày thí nghiệm ở ba mốc quan sát: 25%, 50% và 75% tiến trình học kỳ. Ý tưởng là dữ liệu càng về cuối kỳ càng nhiều, nên model thường dự đoán dễ hơn; nhưng cảnh báo quá muộn thì nhà trường còn ít thời gian hỗ trợ.

#### Kết quả pilot

| Mốc | AP risk | Recall risk | Accuracy | Cách hiểu |
|---|---:|---:|---:|---|
| 25% | 0.7908 | 0.5766 | 0.7538 | Cảnh báo sớm nhất nhưng còn ít dữ liệu. |
| 50% | 0.8595 | 0.6443 | 0.8225 | Cân bằng giữa chất lượng và thời gian can thiệp. |
| 75% | 0.8880 | 0.6749 | 0.8635 | Dự đoán tốt nhất trong pilot nhưng có thể quá muộn. |

#### Cảnh báo về cách dùng kết quả

Thí nghiệm lịch sử đã dùng test để so sánh trực tiếp các mốc, nên đây chỉ là **pilot mô tả**. Không nên dùng bảng này để tuyên bố mốc 75% là lựa chọn triển khai tốt nhất. Kết luận hiện tại giữ 50% làm mốc chính vì mục tiêu là hỗ trợ kịp thời, không chỉ tối đa hóa điểm số.

#### Output chính

- `ket_qua/so_sanh_cac_moc_hoc_ky.csv`.
- Biểu đồ xu hướng metric theo tiến trình học kỳ.

## 4. Quan hệ giữa notebook và file kết quả

| Notebook tạo/đọc | File hoặc kết quả liên quan | Ý nghĩa |
|---|---|---|
| `01` | Bảng kiểm tra 7 file, `phan_bo_nhan.png` | Biết dữ liệu đầu vào có gì. |
| `02` | `du_lieu_da_gop_tao_dac_trung.csv` và hình đặc trưng | Tạo dataset cấp enrollment. |
| `03` | `ket_qua_mo_hinh_co_so.csv`, `ap_mo_hinh_co_so.png` | Có baseline model. |
| `04` | `ket_qua_hco_vnls.csv`, `danh_doi_bo_toi_uu.png` | Có pilot optimizer đầu tiên. |
| `05` | Đọc các CSV từ `03` và `04` | Tóm tắt để ra quyết định, không phải thí nghiệm độc lập. |
| `06` | Ba CSV so sánh HCO/VNLS/hybrid | Kiểm tra câu hỏi trọng tâm với thiết lập công bằng. |
| `07` | Audit tiền xử lý và bảng theo tỷ lệ chia | Kiểm tra độ tin cậy của dữ liệu và giao thức. |
| `08` | Các CSV tuning HGB và chạy lại optimizer | Kiểm tra cải thiện sau khi tối ưu model. |
| `09` | Bảng và hình mốc học kỳ | Đánh giá đánh đổi giữa sớm và chính xác. |

Các hình chi tiết được giải thích thêm trong `hinh/GIAI_THICH_CAC_HINH.md`. Các bảng CSV được giải thích thêm trong `ket_qua/GIAI_THICH_CAC_BANG_KET_QUA.md`.

## 5. Thứ tự đọc đề xuất

### Nếu có thời gian đọc đầy đủ

Đọc theo thứ tự:

```text
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09
```

Lý do: không thể hiểu mask của HCO/VNLS nếu chưa biết feature được tạo thế nào; không thể biết mask tốt hay không nếu chưa có baseline; không thể kết luận hybrid nếu chưa kiểm tra nhiều seed, alpha, tỷ lệ chia và mốc thời gian.

### Nếu chỉ có 15 phút

1. Đọc phần “Bức tranh toàn bộ” trong file này.
2. Xem `03_chia_tap_va_baseline.ipynb` để hiểu model học máy làm gì.
3. Xem `06_hco_vnls_trong_tam.ipynb` để hiểu câu hỏi chính của đề tài.
4. Xem phần kết quả của `08_toi_uu_hgb_va_hco_vnls.ipynb` để biết kết luận mới nhất.
5. Xem `09_so_sanh_cac_moc_hoc_ky.ipynb` nếu cần giải thích vì sao dùng cutoff 50%.

### Nếu muốn hiểu “dữ liệu bỏ vào đâu?”

Đọc `01` rồi `02`. Dữ liệu nguồn đặt trong `data/raw/` theo hướng dẫn của `data/README.md`. Bảy bảng được đọc và gộp ở `02`; các notebook sau dùng bảng cutoff hoặc dữ liệu đã xử lý, không tự ý gộp lại theo cách khác.

## 6. Những điều không nên hiểu nhầm

- HCO/VNLS không phải là model phân loại thay cho HGB hoặc Logistic Regression; chúng là thuật toán tìm feature subset.
- HCO+VNLS là trọng tâm phương pháp, nhưng “trọng tâm” không đồng nghĩa với “luôn đứng đầu mọi chỉ số”. Kết luận phải dựa trên bảng và điều kiện chạy.
- `mean_ap` cao hơn là trung bình tốt hơn; `std_ap` thấp hơn là ổn định hơn. Cần nhìn cả hai, cùng Recall, F1, số feature và runtime.
- Test không được dùng để tune. Nếu một notebook cũ dùng test để mô tả pilot, phải ghi rõ giới hạn như notebook `09`.
- Mốc 75% có thể có AP cao hơn nhưng chưa chắc tốt hơn về mặt hỗ trợ sinh viên. Bài toán thực tế tối ưu cả chất lượng dự đoán và thời gian can thiệp.
- Một feature được chọn thường xuyên không chứng minh feature đó là nguyên nhân gây ra rủi ro.

## 7. File nào nên xem khi viết báo cáo?

- Phần dữ liệu và tiền xử lý: `01`, `02`, `07`.
- Phần model học máy: `03`, sau đó `08`.
- Phần thuật toán đề tài: `04`, `06`, sau đó `08`.
- Phần quyết định và hạn chế: `05`, `06`, `08`, `09`.
- Bảng số liệu: thư mục `ket_qua/`.
- Hình minh họa: thư mục `hinh/`.
- Tóm tắt dành cho người đọc ngoài nhóm: `docs/TOM_TAT_DE_TAI.md`.

## 8. Tóm tắt một câu cho từng notebook

1. `01`: Dữ liệu nguồn có gì và có vấn đề gì cần kiểm tra?
2. `02`: Làm sao gộp 7 bảng thành một dataset đúng cấp enrollment?
3. `03`: Model học máy nào làm mốc đáng tin?
4. `04`: HCO, VNLS và hybrid có thể chọn feature như thế nào?
5. `05`: Nhiều kết quả khác nhau nên được tổng hợp thành quyết định ra sao?
6. `06`: Hybrid có thực sự đáng được xem là phương pháp chính trong điều kiện công bằng không?
7. `07`: Tiền xử lý, chống leakage và tỷ lệ chia có làm kết quả thay đổi không?
8. `08`: Tối ưu HGB có giúp, và hybrid còn đứng ở đâu sau khi model được nâng cấp?
9. `09`: Có nên cảnh báo ở đầu, giữa hay cuối học kỳ?

Đọc đủ chuỗi này sẽ giúp phân biệt rõ ba việc: **chuẩn bị dữ liệu**, **dự đoán bằng học máy**, và **tìm bộ feature bằng HCO/VNLS/HCO+VNLS**.
