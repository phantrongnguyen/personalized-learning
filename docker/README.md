# Docker EduRisk AI

Nguồn chuẩn cho cấu hình container, đối chiếu **04/11/2026**. [Cài đặt local](../README.md), [migration và backup](../docs/database/migrations.md). Diễn biến cũ xem [changelog](../CHANGELOG.md); dùng cấu hình và quy trình hiện hành ở trang này.

## Thành phần

- PostgreSQL 15: schema 19 bảng nghiệp vụ, seed, trigger và marker Alembic qua SQL `01`–`04` khi volume mới.
- pgAdmin tùy chọn: quản trị database.
- Backend: [Dockerfile](backend/Dockerfile), Python 3.12, Uvicorn, healthcheck gọi `/api/v1/health`.
- Frontend: [Dockerfile](../apps/frontend/Dockerfile), Node build → nginx; [proxy](frontend/nginx.conf) chuyển `/api/` và `/media/` sang backend.

Compose chính: [docker-compose.yml](../docker-compose.yml). Backend cần database/model hợp lệ trong lifespan; frontend đợi backend healthy.

## Stack local

Từ gốc repository, tạo `.env` từ mẫu nếu chưa có. Đặt SECRET_KEY và mật khẩu riêng; đồng bộ biến POSTGRES với DATABASE_URL (host) và DOCKER_DATABASE_URL (container). Compose không tự suy ra DOCKER_DATABASE_URL từ POSTGRES_PASSWORD. Xem [README](../README.md#cài-đặt-local--powershell-từ-gốc-repository).

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 backend frontend
```

Mặc định: frontend [localhost:3000](http://localhost:3000), API [localhost:8000/docs](http://localhost:8000/docs), PostgreSQL host 5433, pgAdmin [localhost:5050](http://localhost:5050). Trong mạng Docker, PostgreSQL là `postgres:5432`, không phải localhost. Port/user/database có thể đổi trong `.env` theo Compose.

Vite mặc định cùng origin trong bundle container, nginx proxy tới backend; cấu hình API origin trình duyệt đã lưu có thể ghi đè mặc định. VITE_API_BASE_URL không phải biến runtime của nginx; xem [frontend](../apps/frontend/README.md#api-base-và-môi-trường).

Volume `postgres_data`, `model_archive`, `avatar_uploads` cần được bảo toàn/backup. SQL init không chạy lại trên volume đã có; nâng cấp theo [Alembic/backup](../docs/database/migrations.md), không dùng `down -v` làm migration. Backend không tự nâng schema khi khởi động.

## Stack kiểm chứng cô lập

[Compose verify](../docker-compose.verify.yml) dùng project, volume, database và port riêng. Từ gốc, tạo secret dạng hex để không gặp ký tự đặc biệt trong URL:

```powershell
$env:VERIFY_DB_PASSWORD = python -c "import secrets; print(secrets.token_hex(24))"
$env:VERIFY_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(48))"
docker compose -p edurisk-verification -f docker-compose.verify.yml up --build -d
docker compose -p edurisk-verification -f docker-compose.verify.yml ps
.venv/Scripts/python.exe scripts/verify_stack.py
```

Frontend kiểm chứng ở [127.0.0.1:13000](http://127.0.0.1:13000). Script smoke tạo tài khoản fixture và dùng seed admin `admin@huit.edu.vn` / `admin` trong stack riêng; không trỏ vào hệ thống vận hành. Access token ở verify có hạn 1 phút, không thay cấu hình stack chính. Giữ nguyên hai biến trong terminal khi chạy các lệnh Compose tiếp theo; nếu dùng lại volume verify, cần dùng lại mật khẩu đã tạo cho volume đó. Dừng mà không xóa dữ liệu:

```powershell
docker compose -p edurisk-verification -f docker-compose.verify.yml stop
```

Có Dockerfile không đồng nghĩa đã kiểm chứng deploy hiện tại. Báo cáo cũ là bằng chứng theo ngày; lần rà soát 04/11 không chạy lại stack Docker. Lỗi PostgreSQL từ chối kết nối cần xử lý trước khi xác nhận integration thành công.
