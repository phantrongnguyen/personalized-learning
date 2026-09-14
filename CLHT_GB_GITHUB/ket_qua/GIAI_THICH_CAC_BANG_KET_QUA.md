# Giải thích các bảng kết quả

Tài liệu này giải thích từng CSV trong folder `ket_qua/`: nguồn tạo, nội dung, mục đích và cách dùng. Các bảng được chọn để kể lại chuỗi nghiên cứu; không phải mọi file trung gian trong thư mục làm việc ban đầu đều được đưa vào.

## 1. `ket_qua_mo_hinh_co_so.csv`

- **Nguồn:** `notebooks/03_chia_tap_va_baseline.ipynb`.
- **Nội dung:** Kết quả từng model và seed, gồm Accuracy, Precision risk, Recall risk, F1 risk, Weighted F1, AP risk, ROC AUC, Brier, confusion matrix, số cảnh báo và thời gian.
- **Mục đích:** Làm baseline trước khi dùng optimizer.
- **Cách đọc:** So sánh các model trên cùng giao thức. Không chọn model chỉ bằng Accuracy; AP và Recall phải được xem cùng mục tiêu cảnh báo.

## 2. `ket_qua_hco_vnls.csv`

- **Nguồn:** `notebooks/04_hco_vnls_co_ban.ipynb`.
- **Nội dung:** Kết quả chạy HCO, VNLS và HCO–VNLS theo seed, số feature, fitness CV, AP CV, số lần gọi objective và thời gian.
- **Mục đích:** Cho thấy phiên bản thử nghiệm cơ bản của ba phương pháp.
- **Cách đọc:** `selected_count` càng thấp là mask càng gọn; `average_precision_cv` càng cao là xếp hạng risk càng tốt; `fitness_cv` cân bằng hai mục tiêu theo hàm fitness hiện tại.

## 3. `ket_qua_hco_vnls_theo_alpha.csv`

- **Nguồn:** `notebooks/06_hco_vnls_trong_tam.ipynb`.
- **Nội dung:** Kết quả HCO, VNLS và HCO–VNLS khi thay đổi `alpha`.
- **Mục đích:** Kiểm tra mức ưu tiên giữa AP và số feature.
- **Cách đọc:** Alpha cao ưu tiên AP hơn; alpha thấp thưởng cho việc giảm feature nhiều hơn. Đây là cơ sở để chọn mục tiêu theo nhu cầu hỗ trợ sinh viên.

## 4. `so_sanh_hco_vnls_theo_mo_hinh.csv`

- **Nguồn:** `notebooks/06_hco_vnls_trong_tam.ipynb`.
- **Nội dung:** AP, Recall, Weighted F1, fitness, số feature và thời gian của ba phương pháp trên các model evaluator.
- **Mục đích:** Kiểm tra ảnh hưởng của model học máy đến kết quả optimizer.
- **Cách đọc:** So sánh theo từng model, không gộp tất cả model thành một con số duy nhất nếu mục tiêu nghiên cứu là HCO–VNLS.

## 5. `tong_hop_hco_vnls_theo_mo_hinh.csv`

- **Nguồn:** `notebooks/06_hco_vnls_trong_tam.ipynb`.
- **Nội dung:** Trung bình các metric theo phương pháp và model.
- **Mục đích:** Tóm tắt bảng chi tiết để dễ so sánh.
- **Cách đọc:** Cột `mean_` là trung bình; các cột độ lệch chuẩn hoặc kết quả từng seed cho biết độ ổn định. Trung bình cao hơn chưa đủ nếu biến động rất lớn.

## 6. `kiem_tra_tien_xu_ly.csv`

- **Nguồn:** `notebooks/07_tien_xu_ly_chia_tap_va_so_sanh.ipynb`.
- **Nội dung:** Từng bước tiền xử lý, cách thực hiện, lý do và kiểm soát.
- **Mục đích:** Chứng minh dữ liệu được xử lý có chủ đích, đặc biệt là cutoff và chống rò rỉ.
- **Cách đọc:** Đây là bảng giải thích phương pháp, không phải bảng điểm model.

## 7. `so_sanh_mo_hinh_theo_ty_le_chia.csv`

- **Nguồn:** `notebooks/07_tien_xu_ly_chia_tap_va_so_sanh.ipynb`.
- **Nội dung:** Metric của nhiều model trên năm tỷ lệ chia dữ liệu.
- **Mục đích:** Kiểm tra baseline có phụ thuộc quá nhiều vào một tỷ lệ chia hay không.
- **Cách đọc:** Nên xem theo cả tỷ lệ chia và tên model; phần tổng hợp trung bình không thay thế việc xem từng trường hợp.

## 8. `tim_tham_so_hgb_ngau_nhien.csv`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Nội dung:** Baseline và 12 cấu hình HGB được thử, cùng AP CV, Recall, F1, Brier, độ lệch chuẩn AP và thời gian.
- **Mục đích:** Ghi lại quá trình chọn tham số HGB bằng inner GroupKFold.
- **Cách đọc:** Cấu hình được xếp hạng theo AP CV; vẫn phải xem Recall, F1 và Brier để nhận ra đánh đổi.

## 9. `so_sanh_hgb_co_so_va_toi_uu.csv`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Nội dung:** HGB baseline và HGB tối ưu trên validation, gồm Accuracy, Precision, Recall, F1, Weighted F1, AP, ROC AUC, Brier và thời gian fit.
- **Mục đích:** Kiểm tra việc tuning có cải thiện thật hay chỉ cải thiện một chỉ số.
- **Kết quả chính:** HGB tối ưu tăng Recall risk từ `0.6336` lên `0.7119`, nhưng Accuracy và Precision risk giảm.

## 10. `ket_qua_hco_vnls_tren_hgb_toi_uu.csv`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Nội dung:** Kết quả từng seed của HCO, VNLS và HCO–VNLS khi evaluator là HGB tối ưu.
- **Mục đích:** Là bằng chứng chi tiết cho lần chạy mới nhất.
- **Cách đọc:** Xem cùng `method`, `seed`, `validation_ap`, `validation_recall`, `validation_weighted_f1`, `fitness_cv`, `selected_count` và `search_seconds`.

## 11. `tong_hop_hco_vnls_tren_hgb_toi_uu.csv`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Nội dung:** Trung bình, độ lệch chuẩn AP, Recall, F1, Weighted F1, Brier, fitness, số feature và thời gian theo phương pháp.
- **Mục đích:** Bảng dễ dùng nhất khi viết phần kết quả.
- **Kết quả chính:** HCO có AP validation trung bình `0.8460`; HCO–VNLS có fitness cao nhất `0.7873` và ít feature nhất, trung bình `11.33`.

## 12. `so_sanh_hgb_toi_uu_va_co_so.csv`

- **Nguồn:** `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb`.
- **Nội dung:** Kết quả trước và sau tuning cho HCO, VNLS và HCO–VNLS cùng các delta AP, Recall và Weighted F1.
- **Mục đích:** Theo dõi mức thay đổi do evaluator được tinh chỉnh.
- **Cách đọc:** Delta dương là tăng so với baseline trong cùng bảng; không được hiểu là kết quả test độc lập.

## 13. `so_sanh_cac_moc_hoc_ky.csv`

- **Nguồn:** Thí nghiệm giai đoạn 2 được trình bày lại trong `notebooks/09_so_sanh_cac_moc_hoc_ky.ipynb`.
- **Nội dung:** Accuracy, Recall risk, Weighted F1, AP risk, số cảnh báo và số mẫu ở các mốc 25%, 50% và 75% học kỳ.
- **Mục đích:** Kiểm tra lượng thông tin tích lũy theo tiến trình ảnh hưởng đến dự đoán như thế nào.
- **Kết quả chính:** AP tăng từ `0.7908` ở 25% lên `0.8595` ở 50% và `0.8880` ở 75%. Recall tăng từ `0.5766` lên `0.6443` và `0.6749`.
- **Giới hạn:** Thí nghiệm lịch sử đã dùng test để so sánh trực tiếp các mốc. Vì vậy bảng chỉ dùng để mô tả xu hướng; nghiên cứu tiếp theo phải chọn mốc trên validation rồi mới mở test.
## Lưu ý quan trọng

- Các bảng này chủ yếu phục vụ inner-CV và validation; không dùng chúng để tuyên bố kết quả cuối trên test.
- Runtime phụ thuộc máy chạy.
- `fitness` không thay thế AP, Accuracy, Precision, Recall hoặc F1.
- Khi trích dẫn một kết quả, cần ghi rõ notebook, model evaluator, seed, tỷ lệ chia và metric.