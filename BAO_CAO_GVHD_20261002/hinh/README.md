# Các hình dùng trong buổi báo cáo

Các hình giữ nguyên từ kết quả đã chạy; không tạo số liệu hay vẽ lại trong lần đóng gói này.

## 1. Diễn biến tìm mask

File: kiem_chung_duong_di_mask.png. Nguồn: notebook 09, cell 7, phần vẽ đường đi của HCO, VNLS và hybrid với seed 41 tại hai cutoff.

Trục ngang là số mask mới đã chấm; trục dọc là fitness tốt nhất trên train-CV. Đường tăng cho thấy tìm được phương án tốt hơn theo mục tiêu này; đường ngang là chưa cải thiện trong các lượt đó. Không phải đường AP validation, không chứng minh đã tìm tối ưu toàn cục. Nếu fitness được định nghĩa là điểm cần tối đa hóa thì nghiệm tốt hơn làm fitness tăng, không mặc định mọi đồ thị phải đi xuống.

## 2. Độ ổn định chọn đặc trưng

File: on_dinh_feature_hybrid.png. Nguồn: notebook 09, cell 7, thống kê các cột được hybrid chọn qua năm seed tại mỗi cutoff.

Hình chọn các cột có tần suất cao để dễ đọc. Một cột xuất hiện nhiều lần là tín hiệu về sự ổn định trong giao thức này, không phải bằng chứng cột đó gây ra nguy cơ. Dùng kèm Jaccard trong bảng doi_chung_va_on_dinh_mask.csv để đánh giá cả bộ mask, không chỉ nhìn các cột xuất hiện thường xuyên.

## 3. Thử bỏ từng đặc trưng

File: ablation_feature_hybrid_75.png. Nguồn: notebook 09, cell 9, mask hybrid seed 41 tại cutoff 75%.

Delta AP = AP train-CV của mask gốc trừ AP train-CV khi bỏ cột. Thanh dương nghĩa là AP giảm khi bỏ cột; thanh âm nghĩa là AP tăng sau khi bỏ cột. Kết quả phụ thuộc các cột còn lại, LightGBM và cách chia fold; không phải mức tăng điểm có thể nhận được khi thay đổi hành vi tương ứng.

## 4. Xác suất các hồ sơ minh họa

File: du_bao_ho_so_minh_hoa.png. Nguồn: notebook app 12, cell 9, từ các lần gọi API thật đã lưu ở cell 4.

Hình so sánh xác suất của sáu hồ sơ đủ điều kiện dự báo. Tình huống thiếu bằng chứng không có xác suất để đưa vào như một cột bằng 0. Không dùng hình này để tính Accuracy/AP hoặc kết luận model tốt trên toàn bộ sinh viên. Khi trình bày gợi ý, mở bảng ket_qua_demo.csv để đọc quy tắc khớp; chỉ nhìn xác suất chưa giải thích được căn cứ của lời khuyên.
