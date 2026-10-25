# EduRisk AI — Hệ thống gợi ý chiến lược học tập cá nhân hóa

Dự án khóa luận tốt nghiệp KLTN 13 tại Trường Đại học Công Thương TP. Hồ Chí Minh (HUIT). Hệ thống kết hợp dự báo nguy cơ học tập bằng LightGBM với các không gian làm việc dành cho quản trị viên, cố vấn học tập, giảng viên và sinh viên.

**Trạng thái:** đang phát triển và kiểm thử tích hợp. Nội dung README được đối chiếu với mã nguồn ngày **12/10/2026**; các chức năng đã có được phân biệt với phần còn cần hoàn thiện.

**Cập nhật database 19/10/2026:** SQL/ORM đã đồng bộ 19 bảng, có Alembic `0002_normalize`, CHECK/UNIQUE và chính sách giữ lịch sử bằng RESTRICT. Xem [schema hiện hành](database/database_design_plan.md), [hướng dẫn migration/backup/khôi phục](docs/database/migrations.md) và [kết quả kiểm thử](reports/dailys/19-10-2026.md). Các mô tả schema/migration cũ bên dưới được thay thế bởi các tài liệu này.

## Mục lục

- [Mục tiêu và kiến trúc](#mục-tiêu-và-kiến-trúc)
- [Chức năng đã thực hiện](#chức-năng-đã-thực-hiện)
- [Mô hình và dữ liệu](#mô-hình-và-dữ-liệu)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cài đặt và chạy local](#cài-đặt-và-chạy-local)
- [Tài khoản và phân quyền](#tài-khoản-và-phân-quyền)
- [API chính](#api-chính)
- [Kiểm thử](#kiểm-thử)
- [Giới hạn và công việc tiếp theo](#giới-hạn-và-công-việc-tiếp-theo)
- [Tài liệu và quy trình Git](#tài-liệu-và-quy-trình-git)

## Mục tiêu và kiến trúc

Hệ thống hướng đến phát hiện sinh viên có nguy cơ học tập tại mốc quan sát 75% thời lượng học phần, trình bày các chỉ số hành vi học tập và hỗ trợ theo dõi kế hoạch can thiệp, nhiệm vụ bổ trợ, yêu cầu trợ giúp.

| Thành phần | Công nghệ và nhiệm vụ |
| --- | --- |
| Frontend | React 18, TypeScript 5.7, Vite 6, Tailwind CSS 3.4, Lucide; SPA điều hướng bằng hash |
| Backend | Python 3.12, FastAPI, Pydantic 2; API, xác thực và nghiệp vụ học tập |
| Database | PostgreSQL 15; SQLAlchemy 2 async và driver asyncpg |
| Xác thực | JWT access/refresh token; mật khẩu bcrypt; vai trò ADMIN, ADVISOR, LECTURER, STUDENT |
| Machine Learning | LightGBM, pandas, scikit-learn và artifact joblib; metadata HCO-VNLS tại cutoff 75% |
| Mã dùng chung | TypeScript types và định nghĩa đặc trưng trong `packages/shared` |
| Hạ tầng local | Docker Compose cho PostgreSQL và pgAdmin; backend/frontend chạy bằng Python và Node.js |

Luồng tổng quát: frontend gọi REST API → backend kiểm tra tài khoản/quyền trên các phân hệ → repository truy cập PostgreSQL; luồng dự báo sử dụng pipeline mô hình được nạp khi backend khởi động.

## Chức năng đã thực hiện

### Giao diện và nhận diện

- Giao diện nền trắng, chữ và viền phù hợp nền sáng; màu chủ đạo xanh dương `#005a9c`.
- Logo HUIT qua component `BrandLogo`, sử dụng tại sidebar, footer và trang đăng nhập.
- Sidebar thu gọn, navbar, thông báo kết quả và hộp thoại thao tác.
- Các trang Home, About, Contact, dashboard và không gian theo vai trò.
- Bỏ dòng hiển thị địa chỉ máy chủ ở dashboard/RiskGauge, giữ cấu hình kết nối API phục vụ nội bộ.

Logo hiện được tải từ [cổng sinh viên HUIT](https://sinhvien.huit.edu.vn/Content/AConfig/images/sv_logo_dashboard.png), phụ thuộc khả năng truy cập nguồn ngoài.

### Dashboard phân tích

- Form 17 đặc trưng đầu vào và các mẫu dữ liệu để thử giao diện.
- Gọi API dự báo, hiển thị nhãn nguy cơ và xác suất lớp nguy cơ.
- Đồng hồ RiskGauge, biểu đồ radar và gợi ý can thiệp theo chỉ số học tập.
- Lịch sử phân tích lưu trên trình duyệt; xuất CSV với UTF-8 BOM.

Gợi ý ở dashboard được xây dựng từ các quy tắc frontend trong `utils/recommendations.ts`. Lịch sử trình duyệt không phải nhật ký học tập tập trung hoặc dữ liệu đã được tách riêng theo tài khoản.

### Quản trị viên

Trang `#admin-users` đã tích hợp với API backend:

- Danh sách phân trang 25 tài khoản; thống kê trên trang hiện tại.
- Tìm tên, email, mã sinh viên/giảng viên; lọc vai trò và trạng thái trong trang đang tải.
- Cấp tài khoản sinh viên, giảng viên hoặc cố vấn, tạo hồ sơ phù hợp.
- Xem chi tiết, sửa thông tin và các trường hồ sơ tương ứng.
- Khóa/mở khóa tài khoản; chặn tự khóa ở backend.
- Xóa tài khoản với xác nhận bằng email; chặn tự xóa ở backend.
- Ghi audit log khi sửa/xóa; rollback khi gặp lỗi ràng buộc dữ liệu.
- Đặt lại mật khẩu với xác nhận mật khẩu mới, kiểm tra giới hạn bcrypt và thông báo kết quả.

API admin còn có quản lý học phần, mở lớp học phần, phân công cố vấn/giảng viên, danh sách và kích hoạt mô hình, nạp lại mô hình, dự báo hàng loạt và tra cứu audit log. Chưa có giao diện quản trị đầy đủ cho tất cả API này.

**Xóa tài khoản là xóa vĩnh viễn:** các hồ sơ và dữ liệu học tập phụ thuộc có thể bị xóa theo khóa ngoại CASCADE. Muốn giữ dữ liệu, dùng thao tác khóa tài khoản.

### Cố vấn học tập

Đã có trang `#advisor` và API cho danh sách lớp, sinh viên phụ trách, thống kê lớp, tổng quan/radar sinh viên, kế hoạch can thiệp, nhiệm vụ, ghi chú tư vấn và xuất báo cáo rủi ro Excel. Mức độ tích hợp giao diện tùy từng chức năng; quyền trên từng bản ghi cần tiếp tục rà soát.

### Giảng viên

Đã có trang `#lecturer` và API cho lớp học phần phụ trách, bảng nguy cơ, danh sách sinh viên, cập nhật đánh giá/tiến độ, giao nhiệm vụ bổ trợ và cảnh báo tới cố vấn.

### Sinh viên

Đã có trang `#student` và API cho hồ sơ cá nhân, học phần, dự báo/radar theo đăng ký học, kế hoạch can thiệp, nhiệm vụ, đánh dấu hoàn thành và gửi/xem yêu cầu trợ giúp.

### Hồ sơ và đăng nhập

- Trang `#profile` thay đổi nội dung và lối tắt theo vai trò.
- Sinh viên hiển thị MSSV; giảng viên hiển thị mã giảng viên, học hàm/học vị; cố vấn hiển thị đơn vị và phòng làm việc.
- Người dùng tự sửa họ tên và điện thoại; email và vai trò ở trang hồ sơ chỉ đọc.
- Sinh viên đăng nhập bằng MSSV; giảng viên, cố vấn, admin đăng nhập bằng email.
- Backend nhận `username` và giữ tương thích với payload `email` cũ.
- Tài khoản do admin cấp; chưa mở đăng ký công khai.
- API đổi mật khẩu cá nhân đã có; admin có thể đặt lại mật khẩu trên trang Quản lý tài khoản.

## Mô hình và dữ liệu

Nguồn metadata hiện tại: [THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json](apps/backend/artifacts/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json).

| Thuộc tính | Giá trị được ghi trong metadata |
| --- | --- |
| Tên mô hình | HCO-VNLS + LightGBM 80 cây — cutoff 75% |
| Mốc quan sát | `cutoff_fraction = 0.75` |
| Schema đầu vào | 17 cột |
| Nhãn nguy cơ | `positive_label = 1` |
| Ngưỡng phân loại | `threshold = 0.5` |
| Số dòng huấn luyện cuối | 19.712 |
| Số dòng test loại khỏi fit | 3.447 |
| Accuracy tham chiếu validation | 0,8741 |
| Average precision lớp nguy cơ | 0,8968 |
| Recall lớp nguy cơ | 0,6898 |

Ba chỉ số trên thuộc `validation_reference_train_only`, không phải kết quả test độc lập mới chạy. Không đồng nhất average precision với ROC-AUC; dữ liệu seed hiện gán giá trị gần 0,8968 vào cột `roc_auc`, cần chuẩn hóa lại ý nghĩa chỉ số.

Pipeline dự báo trả `prediction` bằng cách so xác suất lớp 1 với ngưỡng trong artifact. `confidence` là xác suất lớp nguy cơ, kể cả khi nhãn trả về là 0.

Cập nhật 18/10/2026: dự báo mới lưu đủ đầu vào và danh tính artifact để tái lập; cập nhật tiến độ tạo snapshot mới. Chưa có dự báo cho snapshot hiện hành được biểu diễn bằng `null`/`NOT_PREDICTED`, không gán an toàn. Cố vấn tổng hợp theo tất cả học phần. Database có sẵn cần nâng cấp bằng `python apps/backend/scripts/apply_prediction_integrity.py`; xem [hướng dẫn bảo toàn và replay dự báo](apps/backend/README.md#cập-nhật-lịch-sử-dự-báo-ngày-18102026).

17 đặc trưng gồm thông tin học phần/nhân khẩu học, tín chỉ, thời điểm đăng ký, tổng click, click tài nguyên/URL, ngày hoạt động, bài nộp/trễ hạn, tỷ lệ hoạt động/nộp bài, số ngày không hoạt động và click trong 7/30 ngày gần nhất. Xem [schema đầu vào](apps/backend/schemas/prediction.py) và [định nghĩa frontend](packages/shared/constants/fields.ts).

Mã huấn luyện cũ trong `packages/ml` và ba notebook cũ đã được loại khỏi nhánh hiện tại. Đường dẫn notebook/dữ liệu ghi trong metadata là nguồn gốc thực nghiệm, không bảo đảm còn có trong checkout. Dữ liệu OULAD đầy đủ cũng không được đóng gói vào repository.

## Cấu trúc dự án

```text
personalized-learning/
├── apps/
│   ├── backend/
│   │   ├── api/v1/endpoints/   # auth, admin, advisor, lecturer, student, health, predictions
│   │   ├── artifacts/          # Artifact mô hình và metadata
│   │   ├── core/               # Config, database, JWT và permissions
│   │   ├── ml/                 # Tải mô hình và suy luận
│   │   ├── models/             # SQLAlchemy models
│   │   ├── repositories/       # Truy vấn dữ liệu
│   │   ├── schemas/            # Pydantic request/response
│   │   ├── services/           # Xác thực, dự báo, audit
│   │   ├── tests/              # Unit test và kiểm thử luồng học tập
│   │   └── main.py             # FastAPI, lifespan, CORS, static mount
│   └── frontend/
│       ├── src/components/     # common, dashboard, recommendation, admin
│       ├── src/pages/          # Các trang SPA theo vai trò
│       ├── src/services/       # API client và admin client
│       ├── src/state/          # AppContext
│       ├── src/utils/          # CSV và gợi ý can thiệp
│       ├── package.json
│       └── vite.config.ts
├── packages/shared/            # Types và constants frontend
├── docker/postgres/init-scripts/# Schema và dữ liệu khởi tạo
├── database/                   # Thiết kế database
├── data/                       # Vùng dữ liệu local, dữ liệu lớn không commit
├── docs/                       # Product, kiến trúc, API, frontend, database, hướng dẫn
├── reports/                    # Báo cáo tiến độ và kế hoạch
├── .agents/                    # Quy định làm việc và Conventional Commits
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Cài đặt và chạy local

### 1. Yêu cầu

- Python 3.12; Node.js 20.19+ hoặc 22.12+ và npm cho môi trường Vite 6.
- Docker Desktop đang chạy nếu dùng PostgreSQL trong Compose.
- Artifact `apps/backend/artifacts/model_hco_vnls_lightgbm_cutoff75.joblib` tồn tại và tương thích thư viện.

Các lệnh dưới đây dùng PowerShell, bắt đầu tại thư mục gốc repository.

### 2. Môi trường Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Dependency backend/test đã được khai báo trong manifest được pin.
```

`requirements.txt` dùng manifest runtime/test trong `apps/backend`; scikit-learn 1.6.0 và LightGBM 4.7.0 khớp môi trường đã kiểm thử artifact. Cài backend gọn bằng `pip install -r apps/backend/requirements-dev.txt`.

### 3. Cấu hình môi trường

Sao chép `.env.example` thành `.env` nếu chưa có, rồi sửa giá trị cho môi trường local. Không ghi đè `.env` đang sử dụng.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Dùng chuỗi được sinh làm `SECRET_KEY` trong `.env`.

| Biến | Ý nghĩa |
| --- | --- |
| `DATABASE_URL` | URL PostgreSQL từ host; mặc định Compose mở cổng 5433 |
| `SECRET_KEY` | Khóa ký JWT bắt buộc; thay khóa mẫu |
| `MODEL_PATH` | Cấu hình cũ; API hiện chọn artifact từ bản ghi model active trong database |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Khởi tạo database trong Compose |
| `POSTGRES_HOST_PORT` | Cổng database trên host, mặc định 5433 |
| `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD` | Tài khoản quản trị pgAdmin |

Cấu hình URL theo dạng `postgresql://<user>:<password>@127.0.0.1:5433/<database>`. Backend chuyển sang driver `postgresql+asyncpg`.

`.env.example` đang chứa các giá trị phát triển mẫu. Frontend hiện lấy API base từ `AppContext`/localStorage; biến `VITE_API_BASE_URL` trong file mẫu chưa được sử dụng bởi luồng cấu hình này. API base phải là origin, ví dụ `http://127.0.0.1:8000`, không thêm `/api/v1` vì service tự ghép tiền tố.

### 4. PostgreSQL và pgAdmin

```powershell
docker compose up -d postgres pgadmin
docker compose ps
```

- PostgreSQL trên host: `127.0.0.1:5433`.
- pgAdmin: [http://localhost:5050](http://localhost:5050).
- SQL trong `docker/postgres/init-scripts` được chạy khi khởi tạo volume database mới; thay SQL không tự cập nhật volume đã có.

Compose có khai báo backend/frontend nhưng Dockerfile tương ứng hiện không có trong checkout. Hướng dẫn này chỉ dùng Compose cho database; không coi `docker compose up --build` toàn hệ thống là luồng đã hoàn thiện.

### 5. Backend

Trong terminal đã kích hoạt môi trường Python:

```powershell
cd apps/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- Health: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health).
- OpenAPI: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).

Backend xác nhận model active từ PostgreSQL ngay trong lifespan; thiếu database, sai số lượng active hoặc artifact không hợp lệ sẽ ngăn khởi động. Dashboard, batch và CLI dùng chung registry; activate/reload kiểm tra hợp đồng rồi commit cùng audit. Worker chọn lại danh tính model ở mỗi request và cache artifact theo SHA-256. Xem [cơ chế registry và vận hành nhiều worker](apps/backend/README.md#cập-nhật-registry-mô-hình-ngày-18102026). Đã smoke test startup, JWT, health và dự báo trên môi trường hiện có; chưa xác nhận cài mới toàn bộ hệ thống.

### 6. Frontend

Mở terminal khác tại gốc repository:

```powershell
cd apps/frontend
npm ci
npm run dev
```

Truy cập [http://localhost:5173](http://localhost:5173). API base mặc định khi chạy cổng 5173 là `http://127.0.0.1:8000`. Vite có cấu hình proxy `/api`, nhưng client hiện mặc định gọi trực tiếp origin backend.

Đóng gói frontend:

```powershell
npm run build
```

Build được tạo trong `apps/frontend/dist`, không commit vào Git. Khi có dist, backend mount tại [http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/). Nếu chưa có dist, fallback mount thư mục nguồn không thay thế quá trình build React/Vite.

## Tài khoản và phân quyền

| Vai trò | Đăng nhập trên AuthPage | Trang chính | Thông tin hồ sơ riêng |
| --- | --- | --- | --- |
| ADMIN | Email | `#admin-users` | Vai trò và thông tin quản trị |
| ADVISOR | Email | `#advisor` | Khoa/đơn vị, phòng làm việc |
| LECTURER | Email | `#lecturer` | Mã giảng viên, học hàm/học vị, đơn vị |
| STUDENT | MSSV | `#student` | Mã sinh viên |

Script `02_seed_data.sql` khởi tạo tài khoản admin `admin@huit.edu.vn`; lấy thông tin mật khẩu phát triển từ script và đổi trước khi sử dụng ngoài môi trường thử nghiệm. Các nút demo giảng viên/cố vấn trên frontend không bảo đảm có tài khoản tương ứng trong database vừa khởi tạo.

Quy trình cấp sinh viên: đăng nhập admin → Quản lý tài khoản → Cấp tài khoản → chọn Sinh viên → nhập họ tên, email liên hệ, MSSV, mật khẩu → cung cấp MSSV/mật khẩu cho sinh viên. Sinh viên cần có cả vai trò STUDENT và hồ sơ với `student_code` để đăng nhập bằng MSSV; email vẫn được lưu để liên hệ và quản lý.

Mật khẩu được lưu bằng bcrypt, không lưu mật khẩu gốc và không trả mã băm qua API chi tiết. Admin không thể xem lại mật khẩu ban đầu. API và hộp thoại admin đặt lại mật khẩu đã được bổ sung ngày 13/10/2026. Access/refresh token hiện lưu trong localStorage; cần đánh giá lại cách lưu token khi triển khai thực tế.

## API chính

Tiền tố chung: `/api/v1`. Các phân hệ nghiệp vụ dùng bearer access token và dependency kiểm tra vai trò; xem Swagger để biết schema đầy đủ.

### Xác thực

| Phương thức | Đường dẫn | Chức năng |
| --- | --- | --- |
| POST | `/auth/login` | Đăng nhập MSSV hoặc email |
| POST | `/auth/refresh` | Cấp cặp token mới |
| GET | `/auth/me` | Tài khoản hiện tại |
| PUT | `/auth/profile` | Sửa hồ sơ cá nhân |
| PUT | `/auth/change-password` | Đổi mật khẩu cá nhân |

Ví dụ đăng nhập sinh viên:

```json
{"username": "2001234567", "password": "<mat-khau-duoc-cap>"}
```

Giảng viên/cố vấn/admin dùng email trong `username`. Payload `email` cũ vẫn được chấp nhận; API chưa cấm sinh viên đăng nhập bằng email. Chỉ gửi một trong hai trường `username` hoặc `email`.

### Quản trị tài khoản và hệ thống

| Phương thức | Đường dẫn | Chức năng |
| --- | --- | --- |
| GET / POST | `/admin/users` | Danh sách / cấp tài khoản |
| GET / PUT / DELETE | `/admin/users/{user_id}` | Xem / sửa / xóa |
| PUT | `/admin/users/{user_id}/status` | Khóa hoặc mở khóa |
| PUT | `/admin/users/{user_id}/reset-password` | Admin cấp mật khẩu mới, không cần mật khẩu cũ |
| POST | `/admin/users/{user_id}/roles` | Cập nhật vai trò; chưa nối vào form sửa frontend |
| GET / POST | `/admin/academic/courses` | Danh sách / tạo học phần |
| POST | `/admin/academic/presentations` | Mở lớp học phần |
| POST | `/admin/academic/assign-advisor` | Phân công cố vấn |
| POST | `/admin/academic/assign-lecturer` | Phân công giảng viên |
| GET | `/admin/ml/models` | Danh sách phiên bản mô hình |
| POST | `/admin/ml/models/activate` | Kích hoạt phiên bản |
| POST | `/admin/ml/reload` | Nạp lại mô hình |
| POST | `/admin/ml/batch-predict` | Dự báo hàng loạt |
| GET | `/admin/system/audit-logs` | Nhật ký thao tác |

API PUT tài khoản nhận các trường cần thay đổi, không yêu cầu gửi lại toàn bộ hồ sơ. Lỗi thường gặp: 400 dữ liệu/phạm vi hồ sơ không phù hợp, 401 chưa xác thực, 403 thiếu quyền, 404 không tồn tại, 409 trùng dữ liệu hoặc xung đột ràng buộc, 422 không đúng schema.

Đặt lại mật khẩu qua Swagger: đăng nhập admin, dùng access token ở mục Authorize, lấy ID tài khoản từ danh sách `/admin/users`, rồi gọi `PUT /admin/users/{user_id}/reset-password` với body:

```json
{"new_password": "<mat-khau-moi-toi-thieu-6-ky-tu>"}
```

Mật khẩu tối thiểu 6 ký tự, tối đa 72 byte UTF-8; không được chỉ chứa khoảng trắng. Response chỉ gồm `message` và `user_id`. Audit action là `RESET_USER_PASSWORD`, không chứa mật khẩu hoặc mã băm. Đặt lại không kích hoạt tài khoản đã khóa và chưa thu hồi các JWT được cấp trước đó.

### Phân hệ học tập

| Phân hệ | API tiêu biểu |
| --- | --- |
| Cố vấn | `/advisor/classes`, `/advisor/students`, `/advisor/classes/{class_name}/statistics`, `/advisor/students/{student_id}/overview`, `/advisor/students/{student_id}/radar`, `/advisor/interventions`, `/advisor/advising-notes`, `/advisor/export/risk-report` |
| Giảng viên | `/lecturer/courses`, `/lecturer/courses/{presentation_id}/risk-board`, `/lecturer/courses/{presentation_id}/students`, `/lecturer/courses/{presentation_id}/students/{student_id}/assessment`, `/lecturer/courses/{presentation_id}/tasks`, `/lecturer/students/{student_id}/alert-advisor` |
| Sinh viên | `/student/profile`, `/student/courses`, `/student/courses/{enrollment_id}/risk-prediction`, `/student/courses/{enrollment_id}/radar`, `/student/tasks`, `/student/tasks/{task_id}/complete`, `/student/intervention-plans`, `/student/help-requests` |

### Dự báo độc lập

`POST /predictions/` nhận `{ "features": { ...17 đặc trưng... } }` và trả ví dụ:

```json
{"prediction": 1, "confidence": 0.82}
```

Từ ngày 18/10/2026, endpoint yêu cầu bearer access token của tài khoản đang hoạt động. Frontend đã gửi token khi dự báo; yêu cầu ẩn danh hoặc refresh token bị từ chối. Quy tắc quyền trên từng bản ghi và phạm vi ADMIN được mô tả tại [cập nhật phân quyền backend](apps/backend/README.md#cập-nhật-phân-quyền-ngày-18102026).

## Kiểm thử

Frontend:

```powershell
cd apps/frontend
npm run build
```

Backend, từ thư mục gốc với môi trường Python đã kích hoạt:

```powershell
cd apps/backend
python -m pytest tests/test_login_identifier.py tests/test_admin_accounts.py -q
```

Kết quả ghi nhận trước lần cập nhật tài liệu này: frontend build thành công; **14 test** trong hai file trên đạt. Test dùng mock, không xác nhận hành vi SQL trên PostgreSQL thật. Có cảnh báo deprecation Pydantic cần xử lý về sau.

Các test `test_auth.py`, `test_sprint3.py`, `test_sprint4.py`, `test_sprint5.py` kiểm tra các luồng khác. Cập nhật 18/10/2026: toàn bộ suite đạt 119 test và 48 subtest; chạy từ gốc repository bằng `python scripts/run_backend_tests.py -q` để dùng database riêng và rollback fixture.

Đã kiểm tra render trang hồ sơ cho bốn vai trò và khách; đã thử luồng cấp tài khoản/lọc/khóa trên trình duyệt bằng fixture. Đây là kiểm tra dữ liệu giả lập, không phải xác nhận vận hành với dữ liệu thật.

## Giới hạn và công việc tiếp theo

- Kiểm thử đầy đủ trên PostgreSQL, đặc biệt lỗi trùng mã, thay MSSV, phân quyền từng bản ghi và dữ liệu cascade khi xóa.
- Rà soát quyền trên các thao tác can thiệp, ghi chú, giao nhiệm vụ và endpoint dự báo. Phân vai trò trên giao diện không thay thế kiểm tra backend.
- Đồng bộ pipeline dự báo hàng loạt với schema 17 cột; hiện code batch có dữ liệu khác schema và fallback theo tỷ lệ nộp bài khi dự báo lỗi.
- Hoàn thiện Dockerfile backend/frontend, biến môi trường container, dependency và tương thích middleware.
- Chuẩn hóa số liệu mô hình trong seed, nội dung Home/Footer và metadata; không sử dụng các nhãn quảng bá làm bằng chứng hiệu năng.
- Mở rộng tìm kiếm/phân trang/lọc toàn hệ thống ở backend; hiện trang admin lọc trong trang.
- Bổ sung thu hồi phiên đăng nhập sau khi đặt lại mật khẩu và đánh giá chiến lược lưu token.
- Tách lịch sử trình duyệt theo tài khoản hoặc lưu ở backend.
- Chưa có bằng chứng triển khai LTI 1.3, TLS/AES toàn hệ thống, SLA 99,9% hoặc chứng nhận ISO/GDPR/FERPA. Các nội dung này là định hướng cần hiện thực và đánh giá, không phải trạng thái đã hoàn thành.

## Tài liệu và quy trình Git

- [Báo cáo tổng hợp ngày 12/10/2026](reports/dailys/12-10-2026.md).
- [Kế hoạch backend](reports/planning/11-10-2026.md).
- [Mục lục tài liệu](docs/README.md).
- [Phân tích và kiến trúc](docs/architecture/system_analysis_and_architecture.md).
- [Thiết kế database](database/database_design_plan.md).
- [Hướng dẫn database local](docs/database/setup.md) — đối chiếu thông số với `.env` đang dùng.
- [Quy định commit](.agents/commit_github.md).

Repository: [phantrongnguyen/personalized-learning](https://github.com/phantrongnguyen/personalized-learning). Nhánh cá nhân đang sử dụng: `phantrongnguyen`.

Commit theo Conventional Commits, ví dụ `feat(admin): add account management APIs`, `test(auth): cover student code login`, `docs(readme): document current project implementation`. Mỗi commit có một mục đích chính; không commit `.env`, thông tin bí mật, file build, môi trường ảo hoặc dữ liệu lớn. Rà soát diff và chạy kiểm tra phù hợp trước khi push; review qua PR trước khi merge nhánh chính.

Mã nguồn sử dụng [giấy phép MIT](LICENSE). Bản quyền trong LICENSE ghi năm 2026, HUIT — đề tài KLTN 13.


### Kiểm thử tích hợp ngày 18/10/2026

Từ gốc repository chạy `.venv/Scripts/python.exe scripts/run_backend_tests.py -q`. Runner tạo database riêng có hậu tố `_test`, chạy toàn bộ suite và kiểm tra dữ liệu 19 bảng không đổi sau rollback. Không bật RUN_COURSE_SCOPE_DB trên database ứng dụng. Frontend: `npm --prefix apps/frontend test` và `npm --prefix apps/frontend run build`.

Dockerfile backend/frontend, nginx proxy và healthcheck đã có. `docker compose up --build -d` dùng cấu hình .env; archive model/avatar được giữ trong volume. Để kiểm thử độc lập, dùng `docker-compose.verify.yml` với project `edurisk-verification`, hai biến VERIFY_DB_PASSWORD/VERIFY_SECRET_KEY và frontend port 13000; xem hướng dẫn đầy đủ trong apps/backend/README.md. Kết quả và giới hạn nằm trong reports/dailys/18-10-2026.md, mục 6.

### Chuẩn hóa radar và quy tắc gợi ý — 21/10/2026

Radar dùng mốc tham khảo minh họa chưa kiểm chứng, không phải Top 25% hay điểm năng lực. API đổi `percentile` thành `reference_score` và có giá trị null khi thiếu dữ liệu. Quy tắc Dashboard chỉ minh họa; luồng gợi ý giảng viên kiểm tra metadata bằng chứng trước khi đề xuất. Chưa có quy đổi tín chỉ/bằng cấp OULAD sang HUIT; đã bỏ suy luận quá tải từ 90 tín chỉ. Xem [định nghĩa dữ liệu, công thức và bảng quy tắc](docs/product/business-rules.md). Backend/frontend cần triển khai cùng phiên bản.
