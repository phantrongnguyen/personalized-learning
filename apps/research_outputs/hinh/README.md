# Giải thích hình

## du_bao_ho_so_minh_hoa.png

- **Nguồn:** notebook 12_goi_y_chien_luoc_co_giai_thich.ipynb, cell 9; bảng đầu vào từ các lần gọi model thật ở cell 4.
- **Vì sao có hình:** minh họa xác suất model trên các tình huống đang dùng để trình diễn app, giúp phân biệt dự báo với lời khuyên.
- **Trục ngang:** xác suất ước lượng thuộc nhóm Fail/Withdrawn, từ 0–100%; không phải điểm bài làm.
- **Trục dọc:** sáu tình huống được chọn bằng điều kiện hành vi trong train.
- **Đường dọc 50%:** ngưỡng demo phân loại nguy cơ, không phải cutoff theo thời lượng học phần.
- **Cách đọc:** một hồ sơ dưới ngưỡng vẫn có thể nhận lời nhắc kiểm tra bài nộp vì có căn cứ riêng. Cột thấp hơn không có nghĩa người đó chắc chắn không cần hỗ trợ.
- **Không xuất hiện trong hình:** tình huống thiếu bằng chứng, vì model chưa chạy; không vẽ nó thành xác suất 0%.
- **Không được kết luận:** mô hình tổng quát tốt hơn, gợi ý hiệu quả hơn hoặc giúp tăng điểm. Đây không phải một tập test đánh giá model.
