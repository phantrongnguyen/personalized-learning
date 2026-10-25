# Tích hợp API frontend

- [Lớp dịch vụ frontend](../../apps/frontend/src/services/): đối chiếu cách gọi API hiện hành.
- [Trạng thái ứng dụng](../../apps/frontend/src/state/).
- [Tài liệu API](../api/README.md), [xác thực](../api/authentication.md).
- [Hợp đồng dữ liệu và quy tắc](../product/business-rules.md).
- [Kiểm thử trình duyệt](../guides/browser-testing.md).

Khi thay đổi hợp đồng API, cập nhật nơi gọi dịch vụ, kiểu dữ liệu, trạng thái giao diện và tài liệu nghiệp vụ liên quan. Đối chiếu request/response với OpenAPI của backend cùng phiên bản.
