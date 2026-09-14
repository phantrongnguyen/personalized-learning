# Giải thích các hình

Tài liệu này giải thích mỗi hình được tạo từ notebook nào, vì sao phải vẽ và nên đọc hình đó như thế nào. Các hình là kết quả trực quan đã được lưu lại khi chạy notebook, không phải hình minh họa tự vẽ thêm.

## 1. `phan_bo_nhan.png`

- **Nguồn:** `notebooks/01_kham_pha_du_lieu.ipynb`.
- **Cách tạo:** Đọc `studentInfo.csv`, đếm số lượng từng giá trị trong cột `final_result`, sau đó vẽ biểu đồ cột.
- **Vì sao cần:** Trước khi huấn luyện phải biết dữ liệu có bao nhiêu sinh viên Pass, Distinction, Fail và Withdrawn. Đây là bước kiểm tra phân bố nhãn.
- **Cho biết:** Quy mô từng kết quả cuối khóa và mức độ mất cân bằng lớp. Kết quả này giúp giải thích vì sao không thể chỉ nhìn Accuracy; cần thêm Precision, Recall, F1 và AP cho lớp risk.

## 2. `dac_trung_theo_nhan.png`

- **Nguồn:** `notebooks/02_gop_bang_tao_dac_trung.ipynb`.
- **Cách tạo:** Sau khi gộp 7 bảng, nhóm theo `final_result` rồi so sánh điểm trung bình và tổng số lượt click trung bình.
- **Vì sao cần:** Cần kiểm tra xem các đặc trưng sau khi gộp có khác nhau giữa các nhóm kết quả hay không.
- **Cho biết:** Mối liên hệ ban đầu giữa hành vi học tập và kết quả cuối. Đây là mô tả dữ liệu, chưa phải bằng chứng nhân quả và chưa thay thế đánh giá model.

## 3. `ap_mo_hinh_co_so.png`

- **Nguồn:** `notebooks/03_chia_tap_va_baseline.ipynb`.
- **Cách tạo:** Huấn luyện các model học máy baseline trên cùng cách chia dữ liệu, tính AP risk trung bình rồi vẽ biểu đồ thanh ngang.
- **Vì sao cần:** Cần có mốc tham chiếu trước khi cho HCO, VNLS hoặc HCO–VNLS chọn feature.
- **Cho biết:** Model nào xếp hạng nguy cơ tốt hơn theo AP. HGB là baseline mạnh về AP; Logistic Regression vẫn cần giữ làm đối chứng khi ưu tiên Recall.

## 4. `danh_doi_bo_toi_uu.png`

- **Nguồn:** `notebooks/04_hco_vnls_co_ban.ipynb`.
- **Cách tạo:** Mỗi thuật toán tạo một mask feature; notebook vẽ số feature được chọn so với AP CV risk.
- **Vì sao cần:** HCO, VNLS và HCO–VNLS không chỉ cần dự đoán tốt mà còn phải xem bộ feature có gọn hay không.
- **Cho biết:** Đánh đổi giữa chất lượng xếp hạng và số lượng feature. Điểm nằm cao hơn là AP tốt hơn; điểm nằm trái hơn là dùng ít feature hơn. Không nên kết luận chỉ từ một điểm đơn lẻ.

## 5. `so_sanh_hco_vnls_theo_mo_hinh.png`

- **Nguồn:** `notebooks/06_hco_vnls_trong_tam.ipynb`.
- **Cách tạo:** Chạy HCO, VNLS và HCO–VNLS trên nhiều model học máy, sau đó so sánh AP validation.
- **Vì sao cần:** Model evaluator có thể làm thay đổi mask được chọn. Phải kiểm tra hybrid có lợi cho model nào và mục tiêu nào.
- **Cho biết:** Hiệu quả của từng phương pháp phụ thuộc model. HCO–VNLS không được mặc định xem là thắng trong mọi trường hợp; kết luận phải gắn với evaluator và metric cụ thể.

## 6. `so_sanh_ty_le_chia_tap.png`

- **Nguồn:** `notebooks/07_tien_xu_ly_chia_tap_va_so_sanh.ipynb`.
- **Cách tạo:** Chạy các model với các tỷ lệ train/validation/test gồm `6/2/2`, `7/1.5/1.5`, `8/1/1`, `7.5/1.5/1` và `5/2.5/2.5`; chia theo `id_student`.
- **Vì sao cần:** Một model có thể tốt do một cách chia dữ liệu may mắn. Nhiều tỷ lệ giúp quan sát độ ổn định của kết quả.
- **Cho biết:** AP và Recall thay đổi như thế nào khi lượng dữ liệu train và validation thay đổi. Đây là kiểm tra độ bền của baseline, không phải phép chọn test cuối cùng.

## 7. `toi_uu_hgb_va_hco_vnls.png`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Cách tạo:** Tìm tham số HGB bằng inner GroupKFold, sau đó chạy HCO, VNLS và HCO–VNLS với HGB tối ưu; hình tổng hợp kết quả tuning và optimizer.
- **Vì sao cần:** Kiểm tra xem việc tinh chỉnh evaluator có làm thay đổi kết quả chọn feature hay không.
- **Cho biết:** HGB tối ưu tăng Recall/F1 risk nhưng giảm một số chỉ số khác. Trong lần chạy này HCO dẫn đầu AP, còn HCO–VNLS dẫn đầu fitness và dùng ít feature hơn. Đây là trade-off, chưa phải chiến thắng tuyệt đối.

## 8. `so_sanh_cac_moc_hoc_ky.png`

- **Nguồn:** `notebooks/09_so_sanh_cac_moc_hoc_ky.ipynb`, tổng hợp từ thí nghiệm lịch sử trong notebook giai đoạn 2.
- **Cách tạo:** Đọc bảng `ket_qua/so_sanh_cac_moc_hoc_ky.csv` rồi vẽ Accuracy, Recall risk, Weighted F1 và AP risk tại các mốc 25%, 50% và 75% tiến trình.
- **Vì sao cần:** Chất lượng dự đoán và thời gian còn lại để hỗ trợ sinh viên thay đổi theo thời điểm trong học kỳ.
- **Cho biết:** Chỉ số tăng khi dự đoán muộn hơn vì có nhiều dữ liệu hơn. Mốc 75% có AP cao nhất trong pilot, nhưng mốc 50% hợp lý hơn cho mục tiêu hỗ trợ vì vẫn còn thời gian can thiệp. Bảng lịch sử từng dùng test để so sánh mốc nên chỉ có giá trị mô tả, không dùng để chọn cấu hình cuối.
## Cách đọc chung

1. Xem hình để nhận biết xu hướng.
2. Mở bảng CSV tương ứng trong `ket_qua/` để xem số chính xác.
3. Đối chiếu notebook nguồn nếu cần biết công thức và cách tạo.
4. Không dùng hình riêng lẻ để kết luận cuối; luôn xem cùng metric, seed, cách chia và giới hạn của thí nghiệm.