# Xác thực và phân quyền

Backend kiểm tra Bearer access token, tài khoản hiện hành và trạng thái hoạt động trong [permissions.py](../../apps/backend/core/permissions.py). OAuth2 dependency khai báo đường dẫn đăng nhập `/api/v1/auth/login`.

- [README backend](../../apps/backend/README.md): payload đăng nhập, API tài khoản và nghiệp vụ theo vai trò.
- [Mã nguồn xác thực và bảo mật](../../apps/backend/core/security.py).
- [Kiểm thử theo vai trò](../guides/local-role-testing.md).

Tra cứu schema request/response chính xác ở OpenAPI của backend đang chạy. Khi thêm endpoint, kiểm tra cả quyền theo vai trò và quyền trên bản ghi.
