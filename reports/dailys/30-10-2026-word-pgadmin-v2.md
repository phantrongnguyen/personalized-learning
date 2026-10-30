# Cập nhật hình ERD trong báo cáo ngày 30/10/2026

- Docker Desktop không khởi động được; người dùng xác nhận đã bấm Reset to factory defaults. Chưa xác minh phục hồi được database Docker cũ.
- Tạo riêng database `kltn13_erd_30102026` trên PostgreSQL 18 cục bộ từ ba tệp SQL chuẩn của repo: `01_init_schema.sql`, `03_prediction_integrity.sql`, `04_schema_version.sql`. Không nạp seed hoặc dữ liệu nghiệp vụ và không sửa database đang có khác.
- Đối chiếu catalog thực tế: 19 bảng nghiệp vụ, một bảng `alembic_version`, 25 khóa ngoại, không có bản ghi nghiệp vụ. Kiểm tra tên cột, PK, FK và hành vi xóa với metadata schema.
- Mở pgAdmin 4 phiên bản 9.15 bằng profile riêng, dùng ERD For Database và chức năng xuất PNG của pgAdmin. Giữ toàn bộ dữ liệu mô hình ERD; sắp vị trí bảng và ẩn các hàng không phải khóa ở lớp trình bày để hình tổng thể dễ đọc. Lưu cả mô hình đầy đủ, ảnh đầy đủ cột và ảnh giao diện làm bằng chứng.
- Thay riêng Hình 5.10 trong bản sao báo cáo; bổ sung diễn giải rõ đây là database tái lập theo schema SQL, không phải database Docker cũ. Cập nhật danh mục bằng Word và căn giữa hình trên trang ngang.
- Kiểm tra 144 trang đã render; giữ 69 công thức Word, styles, numbering và nội dung bảng. Không đổi kết quả mô hình hoặc mã ứng dụng. Bản báo cáo 30/10 gốc được giữ nguyên.
- Đã dừng phiên trình duyệt headless và pgAdmin riêng phục vụ tác vụ; giữ PostgreSQL và database schema để có thể kiểm tra lại.

Đầu ra: `E:\KLTN-DataScience\bao_cao\BaoCaoTienDo_KLTN_13_30-10v2.docx`.

SHA256: `198568078e924726a89e58992b642bf998ef9baf9395da60237142895e4359a6`.

Mã tái tạo và kiểm tra: `bao_cao/pgadmin_30_10_v2_src`. Bằng chứng và bản render kiểm tra: `bao_cao/pgadmin_30_10_v2_output`.
