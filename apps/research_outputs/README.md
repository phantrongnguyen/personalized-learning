# Kết quả phục vụ bản demo

Các file do ba notebook trong apps/notebooks tạo ra. Không có kết quả cuối kỳ, mã sinh viên hoặc bảng dữ liệu đầy đủ trong thư mục này.

| File | Được tạo từ đâu? | Cho biết điều gì? |
|---|---|---|
| doi_chieu_bai_nop.csv | Notebook 11, đối chiếu mã bài trên train ở 50/75% | Số dòng mà cách đếm cũ báo thiếu thấp hơn đối chiếu; không phải chỉ số chất lượng lời khuyên |
| ket_qua_demo.csv | Notebook 12, gọi API cùng code app | Xác suất dự báo, quy tắc khớp, trạng thái và thời gian của 7 tình huống; hồ sơ thiếu bằng chứng có xác suất trống |
| ket_qua_demo.json | Cùng lần chạy notebook 12 | Toàn bộ lời giải thích/bằng chứng của từng tình huống; dùng cho kiểm thử render frontend |
| kiem_thu_api.txt | Notebook 13 chạy pytest | Nhật ký kiểm thử kỹ thuật backend, không phải đánh giá tác động học tập |
| kiem_thu_giao_dien.txt | Lệnh npm run test, render bằng Node/SSR | Kết quả kiểm tra thành phần, không phải kiểm thử thao tác trình duyệt |
| build_frontend.txt | Lệnh npm run build | Frontend biên dịch thành công |
| phieu_danh_gia_chua_cham.csv | Notebook 13 | Phiếu chấm 1–5 chưa có người chấm; ô điểm cố ý để trống, chưa có trung bình để báo cáo |
| hinh/du_bao_ho_so_minh_hoa.png | Notebook 12 | So sánh xác suất trên 6 bản trích rút có đủ dữ liệu; không phải đánh giá tổng quát model |

Sáu hồ sơ được chọn theo tình huống quan sát trên train, không chọn theo kết quả cuối kỳ hoặc xác suất. Tình huống thứ bảy là phép thử thiếu xác nhận nguồn, có nhãn tổng hợp rõ ràng. Không dùng sáu đầu vào này để báo cáo Accuracy, AP hay lợi ích can thiệp.

Thời gian lần gọi đầu có thể gồm nạp model và thư viện, nên không so với các lần cache nóng để kết luận hiệu năng. API đã được cấu hình nạp model khi server khởi động; notebook TestClient ngoài context có thể vẫn ghi nhận chi phí lần gọi đầu.

Mọi điểm đánh giá bởi giảng viên/người học và tác dụng lên điểm số đều đang ở trạng thái **chưa đánh giá**.
