# Tóm tắt đề tài và hành trình nghiên cứu

## 1. Tài liệu này dùng để làm gì

Đây là tài liệu giải thích toàn bộ dự án cho người chưa từng xem code hoặc notebook. Người đọc chỉ cần đọc file này trước để biết bài toán, dữ liệu, các bước xử lý, vai trò của HCO - VNLS, cách đọc chỉ số và kết quả hiện tại.

Các hình được giải thích tại `hinh/GIAI_THICH_CAC_HINH.md`. Các bảng CSV được giải thích tại `ket_qua/GIAI_THICH_CAC_BANG_KET_QUA.md`. Bản Word có cùng nội dung tổng quát nằm ở `docs/TOM_TAT_DE_TAI_VA_HANH_TRINH.docx`.

## 2. Bài toán đang giải quyết

Dự án dự đoán sớm sinh viên có nguy cơ không hoàn thành môn học. Nhãn `risk=1` gồm `Fail` và `Withdrawn`; nhãn `risk=0` gồm `Pass` và `Distinction`. Mốc dự đoán chính là 50% tiến trình khóa học, để mô phỏng thời điểm nhà trường vẫn còn thời gian hỗ trợ.

Ví dụ: đến giữa học kỳ, một sinh viên ít tương tác trên hệ thống và có nhiều bài chưa nộp. Hệ thống có thể đánh dấu sinh viên này để cố vấn liên hệ sớm. Đây là cảnh báo hỗ trợ, không phải kết luận sinh viên chắc chắn thất bại.

## 3. Bảy bảng dữ liệu

- `studentInfo.csv`: thông tin nền của sinh viên và kết quả cuối.
- `studentRegistration.csv`: thời điểm đăng ký và rút môn.
- `assessments.csv`: thông tin bài đánh giá, ngày đến hạn và trọng số.
- `studentAssessment.csv`: điểm và ngày nộp bài của từng sinh viên.
- `studentVle.csv`: số lần tương tác với tài nguyên học tập.
- `vle.csv`: loại tài nguyên hoặc hoạt động.
- `courses.csv`: thông tin module và kỳ học.

Khi gộp, một dòng đại diện cho một enrollment, tức là một sinh viên học một module trong một kỳ cụ thể. Khóa nghiệp vụ là `id_student + code_module + code_presentation`.

## 4. Tiền xử lý và lý do phải làm

Các bảng ban đầu có mức chi tiết khác nhau: có bảng ở mức sinh viên, có bảng ở mức bài nộp và có bảng ở mức sự kiện click. Model cần một dòng đặc trưng cho mỗi enrollment nên phải gộp và tổng hợp.

1. Đọc và kiểm tra đủ 7 bảng.
2. Gộp assessment để tạo điểm trung bình, điểm thấp nhất, số bài đã làm và số bài nộp trễ.
3. Gộp VLE để tạo tổng click, click theo loại hoạt động, số ngày hoạt động và ngày hoạt động cuối.
4. Cắt dữ liệu tại cutoff 50%, không sử dụng sự kiện xảy ra sau thời điểm dự đoán.
5. Tạo nhãn risk và loại cột tiết lộ kết quả cuối.
6. Điền giá trị thiếu, mã hóa biến phân loại và chuẩn hóa khi model cần.
7. Chia train, validation và test theo `id_student` để tránh một sinh viên xuất hiện ở nhiều tập.

Các tỷ lệ chia đã kiểm tra gồm `6/2/2`, `7/1.5/1.5`, `8/1/1`, `7.5/1.5/1` và `5/2.5/2.5`. Do chia theo sinh viên, số dòng thực tế có thể không đúng tuyệt đối tỷ lệ phần trăm; điều quan trọng là các tập không giao nhau về sinh viên.

## 5. Vai trò của model học máy

Logistic Regression, Decision Tree, RandomForest, ExtraTrees và HistGradientBoosting đều là các model học máy. Chúng học quan hệ giữa đặc trưng và nhãn risk.

- Logistic Regression nhanh, đơn giản, phù hợp làm đối chứng khi ưu tiên Recall.
- Decision Tree dễ giải thích nhưng có thể quá khớp.
- RandomForest kết hợp nhiều cây để ổn định hơn một cây đơn.
- ExtraTrees tạo nhiều cây với cách chia ngẫu nhiên hơn.
- HistGradientBoosting xây dựng nhiều cây nhỏ nối tiếp nhau để sửa lỗi của cây trước và là baseline mạnh về AP.

Các model này không thay thế HCO - VNLS. Chúng được dùng làm evaluator: nhận một bộ feature do optimizer chọn và chấm xem bộ đó dự đoán risk tốt đến đâu.

## 6. HCO, VNLS và HCO - VNLS

Có thể hình dung mỗi bộ feature là một chiếc balo. Mỗi thuật toán thử bật hoặc tắt các feature để tìm chiếc balo vừa đủ thông tin nhưng không quá nặng.

- HCO tìm kiếm rộng bằng một nhóm mask nhị phân rồi cập nhật vị trí để tiến về nghiệm tốt.
- VNLS bắt đầu từ một mask và thử các lân cận, ví dụ bật hoặc tắt một feature; nếu tốt hơn thì giữ lại.
- HCO - VNLS kết hợp tìm kiếm rộng của HCO với bước tinh chỉnh cục bộ của VNLS.

Fitness hiện tại được tính theo công thức:

`fitness = alpha × AP + (1 - alpha) × (1 - số feature được chọn / tổng số feature)`

`AP` đo chất lượng xếp hạng nguy cơ. Thành phần còn lại thưởng cho bộ feature gọn. Vì vậy fitness cao nhất không bắt buộc đồng nghĩa với AP, Recall hoặc Weighted F1 cao nhất.

## 7. Các chỉ số cần đọc

- `Accuracy`: tỷ lệ dự đoán đúng trên toàn bộ mẫu.
- `Precision risk`: trong các cảnh báo risk, bao nhiêu cảnh báo đúng.
- `Recall risk`: trong các sinh viên thật sự risk, bắt được bao nhiêu.
- `F1 risk`: cân bằng giữa Precision và Recall risk.
- `Weighted F1`: F1 có tính đến kích thước từng lớp.
- `AP risk`: chất lượng xếp hạng xác suất risk, hữu ích khi lớp risk không cân bằng.
- `Brier`: sai số xác suất; thường càng thấp càng tốt.
- `Runtime`: thời gian chạy model hoặc optimizer.

Nếu mục tiêu là không bỏ sót sinh viên cần hỗ trợ, Recall quan trọng. Nếu nguồn lực hỗ trợ ít và không muốn cảnh báo nhầm, Precision quan trọng hơn. Vì vậy không nên chọn model chỉ bằng Accuracy.

## 8. Hành trình nghiên cứu

### Giai đoạn 1 Dữ liệu

Đọc 7 bảng OULAD và xác định khóa enrollment. Mục tiêu là đưa thông tin sinh viên, đăng ký, đánh giá và hoạt động VLE về cùng một dòng cho một lượt học.

### Giai đoạn 2 Tiền xử lý và thời điểm dự đoán

Chọn cutoff 50%. Hoạt động sau cutoff không được đưa vào feature. Tạo nhãn risk và tổng hợp hành vi học tập thành các đặc trưng có thể đưa vào model.

### Giai đoạn 3 Chia tập và baseline

Dùng split theo `id_student` và thử nhiều tỷ lệ. HGB là baseline mạnh về AP trung bình; Logistic Regression có Recall risk tốt trong nhóm baseline và nên được giữ làm đối chứng.

### Giai đoạn 4 HCO, VNLS và hybrid

Optimizer chọn mask feature, còn model học máy chấm mask bằng inner GroupKFold. Pilot trước cho thấy HCO - VNLS có tín hiệu tích cực nhỏ trên HGB và đạt fitness tốt hơn nhờ giảm số feature, nhưng chưa thắng ổn định trên Logistic Regression. Vì vậy hybrid vẫn là trọng tâm, không được tuyên bố là luôn tốt nhất.

### Giai đoạn 5 và 6 Kiểm định

Đã kiểm tra threshold, độ ổn định feature, fairness, độ bền optimizer và ảnh hưởng của nhiều model. Các kiểm tra này giúp phân biệt cải thiện có cơ sở với kết quả chỉ tốt trên một seed hoặc một metric.

### Lần tối ưu HGB mới nhất

Notebook `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb` thử 12 cấu hình HGB bằng inner GroupKFold. Cấu hình được chọn có `max_iter=450`, `max_leaf_nodes=7`, `max_depth=3`, `min_samples_leaf=10`, `l2_regularization=5.0` và `class_weight=balanced`.

So với HGB baseline, Recall risk tăng từ `0.6336` lên `0.7119`, F1 risk tăng từ `0.7247` lên `0.7354`, nhưng Accuracy giảm từ `0.8181` xuống `0.8065` và Precision risk giảm từ `0.8464` xuống `0.7606`. Đây là đánh đổi giữa bắt được nhiều ca risk và giảm cảnh báo nhầm.

## 9. Kết quả hiện tại

Trên HGB tối ưu:

| Phương pháp | AP validation | Recall risk | Weighted F1 | Fitness | Số feature |
|---|---:|---:|---:|---:|---:|
| HCO | **0.8460** | **0.6976** | **0.8001** | 0.7805 | 13.67 |
| HCO - VNLS | 0.8352 | 0.6868 | 0.7944 | **0.7873** | **11.33** |
| VNLS | 0.8307 | 0.6750 | 0.7904 | 0.7766 | 13.00 |

Diễn giải:

- HCO đang mạnh nhất về AP validation trong lần chạy này.
- HCO - VNLS đang đạt fitness cao nhất và dùng ít feature nhất.
- HCO - VNLS chưa thắng AP, Recall và Weighted F1, nhưng vẫn có giá trị nghiên cứu vì đề tài tập trung vào hybrid và mục tiêu của fitness có cả độ gọn.
- HGB tối ưu giúp tăng Recall nhưng làm giảm Precision; cấu hình nào phù hợp còn phụ thuộc chi phí của cảnh báo nhầm và bỏ sót.

## 10. Model demo và ứng dụng nhanh

Model demo đã được xuất thành file `mo_hinh/model_hco_vnls_hgb_demo.joblib`. File này chứa pipeline tiền xử lý, HGB đã tinh chỉnh, 14 feature do HCO–VNLS chọn, threshold `0.5` và thông tin cấu hình.

Model được fit trên train + validation sau khi khóa feature; test không được dùng để huấn luyện. Đây là model phục vụ demo kỹ thuật, chưa phải model triển khai chính thức. Có thể chạy giao diện nhanh bằng:

```powershell
streamlit run app_demo.py
```

Danh sách feature và cách dùng nằm trong `mo_hinh/README.md`. Các tên cột đầu vào vẫn giữ theo tên dataset để app gửi dữ liệu đúng schema.

## 11. Thử nghiệm theo các mốc học kỳ

Dự án đã thử ba mốc tiến trình: 25%, 50% và 75% học kỳ. Đây là mốc quan sát dữ liệu, không phải ba nhãn học kỳ cố định.

| Mốc quan sát | AP risk | Recall risk | Accuracy | Cách hiểu |
|---|---:|---:|---:|---|
| 25% | 0.7908 | 0.5766 | 0.7538 | Cảnh báo sớm nhưng còn ít thông tin. |
| 50% | 0.8595 | 0.6443 | 0.8225 | Cân bằng giữa chất lượng và thời gian hỗ trợ. |
| 75% | 0.8880 | 0.6749 | 0.8635 | Dự đoán tốt hơn nhưng có thể đã muộn để can thiệp. |

Kết quả này được đưa vào `notebooks/09_so_sanh_cac_moc_hoc_ky.ipynb`, `ket_qua/so_sanh_cac_moc_hoc_ky.csv` và `hinh/so_sanh_cac_moc_hoc_ky.png`. Đây là pilot lịch sử dùng test khi so sánh mốc, nên chỉ dùng để mô tả xu hướng; không dùng để chọn model cuối.
## 12. Cách đọc các thư mục

- `notebooks/`: code và output theo trình tự nghiên cứu.
- `clht_code/`: các hàm dùng lại cho gộp dữ liệu, model, đánh giá và optimizer.
- `ket_qua/`: các bảng kết quả; đọc thêm `GIAI_THICH_CAC_BANG_KET_QUA.md` trong cùng thư mục.
- `hinh/`: các biểu đồ; đọc thêm `GIAI_THICH_CAC_HINH.md` trong cùng thư mục.
- `docs/`: tài liệu tổng hợp này và bản Word.
- `data/README.md`: hướng dẫn dữ liệu đầu vào.

## 13. Giới hạn và bước tiếp theo

Kết quả phụ thuộc bộ dữ liệu, seed, cách chia và máy chạy. Test chưa được dùng để chọn cấu hình trong lần tối ưu HGB mới nhất. HCO/VNLS hiện là triển khai theo phong cách thuật toán đã thiết kế; nếu cần khẳng định tái hiện đúng một bài báo cụ thể thì phải đối chiếu công thức gốc.

Các hướng tiếp theo:

1. Tiếp tục tối ưu HCO - VNLS, neighborhood, alpha và fitness có ràng buộc Recall.
2. Thử threshold trên validation và khóa threshold trước khi dùng test.
3. Chạy thêm seed chia group và khoảng tin cậy để kiểm tra độ ổn định.
4. Chỉ chạy test một lần sau khi đã khóa evaluator, mask, alpha và threshold.