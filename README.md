# EduRisk AI — Gợi ý chiến lược học tập cá nhân hóa

Dự án khóa luận KLTN 13, HUIT: dự báo nguy cơ học tập bằng LightGBM và hỗ trợ giảng viên/cố vấn xác minh bằng chứng, lập kế hoạch, giao nhiệm vụ và theo dõi sinh viên.

**Hiện trạng đối chiếu mã nguồn: 04/11/2026.** Hệ thống đang phát triển và kiểm thử; kết quả OULAD không chứng minh hiệu quả tại HUIT. Diễn biến theo ngày nằm trong [CHANGELOG](CHANGELOG.md), không phải hướng dẫn vận hành.

## Tài liệu chuẩn theo chủ đề

| Chủ đề | Nguồn chuẩn |
| --- | --- |
| Cài đặt nhanh và trạng thái chung | README này |
| Backend, quyền, registry và replay | [Backend](apps/backend/README.md); hợp đồng endpoint khi server chạy: [OpenAPI](http://127.0.0.1:8000/openapi.json) |
| Frontend, API origin và phiên | [Frontend](apps/frontend/README.md) |
| Docker và stack kiểm chứng | [Docker](docker/README.md) |
| Schema | [Thiết kế database](database/database_design_plan.md) |
| Migration, backup và phục hồi | [Migration](docs/database/migrations.md) |
| Quy tắc radar/gợi ý | [Quy tắc nghiệp vụ](docs/product/business-rules.md) |
| Kết luận thực nghiệm và giới hạn | [Thực nghiệm](reports/evaluation/THESIS_EXPERIMENTS.md) |
| Mã/pipeline ML | [ML](packages/ml/README.md) |
| Metric artifact ứng dụng / tái chạy | [Biên bản ứng dụng](reports/model_final/MODEL_FINAL.md) / [rerun 25/10](packages/ml/reports/rerun-20261025/README.md) |
| Cách duy trì và kiểm tra tài liệu | [Quy ước tài liệu](docs/documentation-policy.md) |

[Mục lục docs](docs/README.md) cung cấp các tài liệu bổ sung. Nhật ký theo ngày và Git giữ lịch sử; không duy trì bản sao README cũ song song với nguồn chuẩn.

## Kiến trúc và chức năng

React 18 + TypeScript + Vite → FastAPI/Pydantic → SQLAlchemy async/PostgreSQL 15. Pipeline scikit-learn/LightGBM được registry chọn từ bản ghi model active trong database và cache theo SHA-256. Schema hiện hành là Alembic `0002_normalize`, 19 bảng nghiệp vụ cùng bảng version.

- **ADMIN:** quản lý tài khoản; API học phần, phân công, mô hình, batch và audit. Giao diện chưa bao phủ toàn bộ API quản trị.
- **ADVISOR:** sinh viên được phân công, nguy cơ theo các học phần, kế hoạch, nhiệm vụ, ghi chú và báo cáo Excel.
- **LECTURER:** học phần phụ trách, bảng nguy cơ, tiến độ, xác nhận nguồn snapshot, gợi ý hỗ trợ và giao nhiệm vụ.
- **STUDENT:** học phần cá nhân, dự báo/radar, nhiệm vụ, nhắc nhở và yêu cầu trợ giúp.
- **Dashboard:** nhập 17 đặc trưng OULAD, gọi dự báo có xác thực, xem xác suất/provenance, radar và quy tắc minh họa; xuất lịch sử CSV.

Quyền bản ghi được kiểm tra ở backend. ADMIN qua được cổng vai trò của portal nhưng vẫn cần hồ sơ/phân công tương ứng; thao tác toàn hệ thống nằm ở `/admin/*`.

Dự báo thủ công và batch database dùng chung `StudentFeatures` và registry. Batch từ chối dữ liệu không hợp lệ, không thay kết quả ML bằng fallback tỷ lệ nộp bài. Snapshot mới chưa được dự báo trả `NOT_PREDICTED`/null, không kế thừa dự báo cũ hoặc coi là an toàn. Provenance và archive artifact cho phép replay các dự báo có đủ context; dữ liệu legacy thiếu context không được dựng lại giả định.

Lịch sử Dashboard lưu tối đa 50 mục trong localStorage, tách theo **tài khoản và API origin**, chưa phải lịch sử tập trung trên server. Access/refresh token vẫn lưu localStorage; đổi/reset mật khẩu chưa thu hồi JWT cũ. Radar dùng mốc tham khảo minh họa, không phải percentile hay điểm năng lực đã kiểm chứng. Gợi ý giảng viên có kiểm tra nguồn/cutoff/digest/người xác nhận; chưa có kết quả đánh giá chuyên gia hoặc hiệu quả can thiệp thực tế.

## Cài đặt local — PowerShell, từ gốc repository

Yêu cầu Python 3.12, Node.js 22 và npm, PostgreSQL 15 hoặc Docker Desktop. Artifact được đóng gói tại [apps/backend/artifacts](apps/backend/artifacts/). Không cần dữ liệu OULAD thô để phục vụ artifact; tái huấn luyện có yêu cầu riêng trong tài liệu ML.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Sửa `.env`: dùng chuỗi vừa sinh làm `SECRET_KEY`, chọn mật khẩu database riêng; đồng bộ `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` và `DOCKER_DATABASE_URL`. Không ghi đè `.env` đang sử dụng. URL từ host dùng `127.0.0.1:5433`; URL backend trong Compose dùng `postgres:5432`. Thông tin mẫu chỉ dành cho phát triển.

```powershell
docker compose up -d postgres pgadmin
docker compose ps
```

Volume mới chạy SQL `01`–`04`, seed và marker Alembic. Volume đã có không tự cập nhật khi sửa SQL: làm theo [migration/backup](docs/database/migrations.md) trước khi chạy backend. Không dùng reset volume để nâng cấp dữ liệu đang sử dụng.

Chạy backend tại gốc:

```powershell
.venv/Scripts/python.exe -m uvicorn main:app --app-dir apps/backend --host 127.0.0.1 --port 8000 --reload
```

Backend cần database cùng đúng một model active và artifact hợp lệ ngay khi startup. Xem [Swagger](http://127.0.0.1:8000/docs) và [health](http://127.0.0.1:8000/api/v1/health).

Trong terminal khác tại gốc:

```powershell
npm --prefix apps/frontend ci
npm --prefix apps/frontend run dev
```

Mở [frontend local](http://localhost:5173). API base là **origin**, ví dụ `http://127.0.0.1:8000`, không thêm `/api/v1`. Thứ tự chọn: localStorage đã lưu → `VITE_API_BASE_URL` → mặc định theo origin/cổng. Biến Vite được đặt trong `apps/frontend/.env.local` hoặc môi trường tiến trình trước dev/build; Vite hiện không cấu hình đọc `.env` ở gốc repo. Xem [cấu hình frontend](apps/frontend/README.md#api-base-và-môi-trường).

```powershell
npm --prefix apps/frontend run build
```

Build vào `apps/frontend/dist`; backend phục vụ tại [app](http://127.0.0.1:8000/app/). Fallback mount nguồn không thay thế build. Muốn chạy toàn bộ container, dùng [hướng dẫn Docker](docker/README.md); Dockerfile backend/frontend, nginx proxy và healthcheck đã có.

## Đăng nhập và tài khoản

Tài khoản do admin cấp, chưa mở đăng ký công khai. Sinh viên dùng MSSV; giảng viên/cố vấn/admin dùng email. Backend nhận `username`, tương thích payload `email` cũ và vẫn cho sinh viên đăng nhập bằng email. Seed database mới có admin `admin@huit.edu.vn` / `admin`, chỉ dùng thử local; đổi mật khẩu trước khi dùng ngoài môi trường thử nghiệm. Khóa tài khoản để giữ dữ liệu; xóa có thể bị RESTRICT vì dữ liệu lịch sử, không giả định mọi quan hệ đều CASCADE.

## Mô hình và cách đọc metric

Không sao chép bảng metric rời nguồn. [Tài liệu thực nghiệm](reports/evaluation/THESIS_EXPERIMENTS.md) phân biệt:

- Artifact đóng gói trong app: SHA-256 `90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db`.
- Artifact rerun 25/10: SHA-256 `50811be18f112283f25de864a9d5b99b63501f8f1579c455ac10860a55828df0`; không tự thay artifact app.

Cả hai dùng OULAD, cutoff 75%, threshold 0,5 và test lịch sử, không phải holdout HUIT mới. Validation train-only không phải test artifact refit; average precision không phải ROC-AUC. Registry database có thể kích hoạt phiên bản khác: danh tính model thực đang phục vụ lấy từ health/provenance, không suy ra từ tên file mặc định.

## Kiểm thử và kiểm tra tài liệu

```powershell
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
.venv/Scripts/python.exe -m pytest apps/backend/tests -q
.venv/Scripts/python.exe scripts/run_backend_tests.py -q
.venv/Scripts/python.exe scripts/run_browser_tests.py
.venv/Scripts/python.exe scripts/check_docs.py
```

Lệnh pytest trực tiếp chạy phần độc lập và bỏ qua ca cần điều kiện/database; runner backend cần PostgreSQL cùng quyền tạo database `_test`, chạy migration và kiểm tra rollback. Browser runner tạo database tạm riêng và cần Chromium của Playwright; xem tài liệu frontend. Không tính test bỏ qua là test đã đạt.

Kiểm chứng ngày **04/11/2026**: frontend 32 test đạt và build thành công; backend chạy độc lập 100 test, 48 subtest đạt, 68 test bỏ qua; runner tích hợp bị từ chối kết nối PostgreSQL. Đây không phải xác nhận cài mới/Docker/E2E thành công trong ngày này. Chi tiết trong [báo cáo rà soát](reports/project-review-2026-11-04.md).

`check_docs.py` kiểm tra offline liên kết nội bộ/anchor trong bộ tài liệu chuẩn, đường dẫn script/Dockerfile, các lệnh được quản lý và provenance metric; không tự khởi động dịch vụ, chạy migration hay xác nhận URL bên ngoài hoạt động.

## Giới hạn và việc tiếp theo

Ưu tiên quản lý phiên/thu hồi refresh, validation mật khẩu và quan hệ đặc trưng, đánh giá chuyên gia thật, mapping dữ liệu HUIT, tìm kiếm/phân trang phía server, batch job và CI. Chưa có bằng chứng SLA, chứng nhận bảo mật hoặc hiệu quả can thiệp học tập. [Báo cáo rà soát](reports/project-review-2026-11-04.md) trình bày mức ưu tiên và bằng chứng.

Mã nguồn theo [MIT](LICENSE). Quy trình đóng góp: [CONTRIBUTING](CONTRIBUTING.md), [Conventional Commits](.agents/commit_github.md).
