# Cách đọc các bảng kết quả

Các bảng được sao chép từ đầu ra đã lưu, không phải thí nghiệm mới. Không có CSV cấp sinh viên đầy đủ trong thư mục này.

| File | Nguồn | Vì sao cần trong buổi báo cáo? |
|---|---|---|
| kiem_ke_7_bang.csv | Notebook nghiên cứu 01, cell 3 | Chứng minh có bảy nguồn dữ liệu, tên bảng, số cột, kích thước và hash. Bảng này không chứa số hàng của từng nguồn. |
| hco_vnls_lightgbm_validation.csv | Notebook 05b, cell 3 | So sánh đủ 38 cột, HCO, VNLS và hybrid tại 50%/75%, cùng LightGBM 80 cây và ngưỡng 0,5. Có Accuracy, Precision, Recall, F1, Weighted F1, AP và số cột. |
| doi_chung_va_on_dinh_mask.csv | Notebook 09, cell 5 | Đối chiếu mask với tám mask ngẫu nhiên cùng số cột cho mỗi cấu hình; có AP train-CV, AP validation và Jaccard giữa năm seed. Không phải kiểm định ý nghĩa thống kê. |
| ablation_hybrid_75_train_cv.csv | Notebook 09, cell 9 | Bỏ từng đặc trưng của mask hybrid seed 41 tại 75%, đo thay đổi AP train-CV. Không đo tác động can thiệp lên điểm sinh viên. |
| doi_chieu_bai_nop.csv | Notebook app 11, cell 4 | Cách đếm tổng báo thiếu thấp hơn đối chiếu theo mã bài ở 406 dòng train tại 50% và 693 dòng tại 75%. Đây là sai khác cách đếm, không phải số sinh viên được giúp cải thiện điểm. |
| ket_qua_demo.csv | Notebook app 12, cell 4 | Bảy tình huống, xác suất nguy cơ, quy tắc khớp, trạng thái và thời gian gọi. Xác suất trống của trường hợp thiếu bằng chứng không phải 0%. |
| phieu_danh_gia_chua_cham.csv | Notebook app 13, cell 8 | Công cụ xin ý kiến về gợi ý; chưa có người chấm nên không tính điểm trung bình. |
| THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json | Metadata artifact đang dùng trong app; tạo từ notebook 10 | Xác nhận 17 cột, cutoff 75%, cấu hình phiên bản, 19.712 dòng fit train + validation và 3.447 dòng test không dùng để fit. Các chỉ số tham chiếu là validation của model fit train, không phải đánh giá mới của artifact. |

## Những cột thường gặp

- cutoff: phần thời gian môn học đã quan sát; 0.5 và 0.75 là 50% và 75%, không phải tỷ lệ lấy dòng.
- method: cách tìm hoặc giữ đặc trưng. Full features là dùng đủ cột.
- features: số đặc trưng được giữ, không phải số cây.
- fitness_cv: hàm mục tiêu trên train-CV có cân bằng chất lượng và độ gọn; không đọc như Accuracy/AP validation.
- objective_calls: số mask mới đã được chấm; ngân sách thử nghiệm nhỏ nên không kết luận tối ưu toàn cục.
- precision_risk: trong số hồ sơ được cảnh báo, tỷ lệ thật sự thuộc lớp nguy cơ.
- recall_risk: trong số hồ sơ thật sự nguy cơ, tỷ lệ được cảnh báo.
- f1_risk: trung bình điều hòa Precision và Recall của lớp nguy cơ.
- weighted_f1: F1 của các lớp được tổng hợp theo số lượng từng lớp.
- average_precision_risk hoặc ap_validation: AP lớp nguy cơ, phản ánh chất lượng xếp hạng.
- ap_cv: AP trung bình trên các fold train, không phải kết quả validation ngoài train.
- mean_jaccard_five_seeds: độ giống nhau của các tập đặc trưng giữa năm seed; không phải độ chính xác dự báo.
- tn/fp/fn/tp: số dự báo âm đúng/dương sai/âm sai/dương đúng, lớp dương là nguy cơ.

So sánh trong cùng cutoff và cùng cấu hình trước. Không lấy AP train-CV, AP validation và xác suất của một hồ sơ để thay thế cho nhau. Bảng LightGBM đã đủ số liệu để chỉ ra hybrid gọn hơn nhưng không vượt đủ cột trên mọi chỉ số.
