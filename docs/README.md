# Tài liệu dự án

Điểm bắt đầu tra cứu tài liệu hệ thống gợi ý chiến lược học tập cá nhân hóa.

| Nhóm | Nội dung | Điểm bắt đầu |
| --- | --- | --- |
| Product | Đề cương khóa luận, yêu cầu, use case, quy tắc nghiệp vụ | [Đề cương khóa luận](product/thesis-proposal.md), [Yêu cầu](product/requirements.md), [use case](product/use-cases.md), [quy tắc](product/business-rules.md) |
| Architecture | Phân tích, thiết kế tổng thể, luồng dữ liệu | [Phân tích và kiến trúc](architecture/system_analysis_and_architecture.md), [thiết kế](architecture/system-design.md) |
| API | Xác thực, endpoint, hợp đồng tích hợp | [Tổng quan API](api/README.md) |
| Frontend | Cấu trúc giao diện, màn hình, tích hợp API | [Kiến trúc frontend](frontend/architecture.md) |
| Database | Lược đồ, sơ đồ, cài đặt, migration | [Thiết kế database](database/design.md) |
| Guides | Hướng dẫn chạy và kiểm thử | [Hướng dẫn](guides/README.md) |
| Research | Paper và cơ sở lý thuyết | [Tài liệu tham khảo](research/references.md) |
| Data | Nguồn và tài liệu dữ liệu | [Nguồn dữ liệu](data/README.md) |
| Images | Hình ảnh dùng trong tài liệu | `images/` |

## Quy ước duy trì

- Tài liệu mới đặt theo chủ đề; dùng tên file chữ thường, phân cách bằng dấu gạch ngang.
- Dùng liên kết tương đối; cập nhật liên kết khi đổi vị trí file.
- README tại mỗi ứng dụng tập trung vào cài đặt, chạy và build; tài liệu chi tiết đặt trong `docs`.
- Schema chi tiết hiện được duy trì tại `database/database_design_plan.md`; trang database trong `docs` liên kết tới nguồn này.
- Kết quả thực nghiệm và nhật ký công việc tiếp tục đặt tại `reports/`, `experiments/`.
- Các trang tổng quan mới là đầu mối tra cứu, không thay thế đặc tả chi tiết được liên kết. Khi mô tả cũ khác triển khai, đối chiếu mã nguồn và tài liệu cập nhật trước khi sử dụng.
