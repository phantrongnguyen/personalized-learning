# Nhật ký ngày 30/10/2026 — Bổ sung database và tinh giản ảnh báo cáo

- Lấy bản `bao_cao/KLTN_13_NguyenThiThuyTrang.docx` hiện tại làm nền, lưu bản nguồn riêng và giữ nguyên tệp gốc, styles, font, màu sắc, công thức và cách đánh số trang.
- Đối chiếu 19 bảng nghiệp vụ và 25 khóa ngoại giữa ORM, SQL baseline, signature schema và migration `0002_normalize`. Tài liệu drawio cũ thiếu năm bảng mở rộng; không dùng tài liệu này làm nguồn duy nhất. Docker không hoạt động trong phiên nên không tuyên bố kiểm tra trực tiếp database đang chạy.
- Dựng sơ đồ tổng thể thể hiện PK, FK và các quan hệ, chèn thành Hình 5.10 ở cuối mục 5.6.1 trên một trang ngang. Giữ Hình 5.7–5.9; các hình 5.10–5.12 cũ thành 5.11–5.13.
- Bỏ đúng các hình Chương 6 theo số cũ: 6.2, 6.3, 6.5, 6.8, 6.14, 6.15, 6.18, 6.19, 6.20 và 6.36. Giữ 33 ảnh gốc còn lại, rút gọn mô tả liên quan và phân biệt bộ 43 ảnh gốc với 33 hình đưa vào báo cáo.
- Cập nhật số hình, các danh mục tự động và bốn dải tham chiếu trong bảng truy vết yêu cầu ở Chương 5. Giữ nội dung Chương 1–4, số liệu trong các bảng, 69 công thức Word và 32 tài liệu tham khảo.
- Xuất bằng Word riêng, render và xem toàn bộ 144 trang; sau sửa tham chiếu cuối, render lại và kiểm tra các trang thay đổi. Kiểm tra số trang phần nội dung liên tục, không có bookmark thiếu, lỗi trường, trang trắng, nội dung vượt biên trang hoặc chú thích hình tách khỏi ảnh.
- Đầu ra: `E:\KLTN-DataScience\bao_cao\BaoCaoTienDo_KLTN_13_30-10.docx`.
- Mã tái tạo: `bao_cao/cap_nhat_30_10_src`; nguồn đóng băng, hình ERD và biên bản kiểm tra: `bao_cao/cap_nhat_30_10_output`.
- Không sửa mô hình, mã ứng dụng hoặc database, không chạy lại tìm kiếm/thực nghiệm; không commit/push. Nhánh đọc đối chiếu: `vobachkimthinh`, HEAD `7195ab2`.

SHA-256 bản giao: `6d7c01298121b295f1aa533845f08fb8e098bcf26d24fb844733303990915a2e`.
