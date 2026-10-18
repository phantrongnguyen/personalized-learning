# Backend EduRisk AI — Tài liệu kỹ thuật và đánh giá

Tài liệu đối chiếu mã nguồn trong working tree ngày **13/10/2026**, bao gồm các thay đổi local chưa commit. Đây là mô tả hiện trạng triển khai, không phải cam kết rằng mọi chức năng đã chạy thành công trên database thật. Nguồn chính: `main.py`, `api/router.py`, `api/v1/endpoints`, `schemas`, `repositories`, `services`, `models`, `core`, `ml` và `../../docker/postgres/init-scripts/01_init_schema.sql`.

**Phạm vi:** 53 operation ứng dụng (52 dưới `/api/v1` và GET `/`), 53 schema Pydantic và 19 bảng SQL. Phần 1–12 giải thích kiến trúc, nghiệp vụ, database, đánh giá và kiểm thử; phụ lục A liệt kê mọi operation; phụ lục B mô tả từng field request/response; phụ lục C chứa DDL đầy đủ.

> **Ghi chú ngày 14/10/2026:** Nội dung dưới đây giữ mốc khảo sát 13/10. Luồng dự báo từ database, xử lý lỗi batch và hiển thị radar đã được sửa sau đó; kết quả mới nằm trong [báo cáo 14/10](../../reports/dailys/14-10-2026.md).

### Cập nhật phân quyền ngày 18/10/2026

Phần cập nhật này thay thế các mô tả phân quyền cũ bên dưới nếu có khác biệt. Chi tiết triển khai và kết quả kiểm tra được ghi trong [báo cáo 18/10](../../reports/dailys/18-10-2026.md).

| Phạm vi | Quy tắc hiện tại |
| --- | --- |
| `/admin/*` | Yêu cầu ADMIN; các thao tác quản trị toàn hệ thống nằm tại đây |
| `/advisor/*` | ADVISOR hoặc ADMIN qua cổng vai trò; dữ liệu vẫn giới hạn theo hồ sơ cố vấn và phân công của chính tài khoản, gồm tạo kế hoạch, ghi chú, sửa kế hoạch và thêm nhiệm vụ |
| `/lecturer/*` | LECTURER hoặc ADMIN qua cổng vai trò; thao tác trên học phần bắt buộc có hồ sơ giảng viên và phân công tương ứng |
| `/student/*` | STUDENT hoặc ADMIN qua cổng vai trò; chỉ truy cập hồ sơ, đăng ký, nhiệm vụ và yêu cầu của chính tài khoản |
| `POST /predictions/` | Mọi tài khoản đang hoạt động có access token hợp lệ; không cho truy cập ẩn danh hoặc dùng refresh token |

ADMIN chỉ được miễn kiểm tra vai trò tại các portal, không được bỏ qua quyền sở hữu hoặc mạo danh hồ sơ khác. Đây là thay đổi so với việc ADMIN trước đây có thể bỏ qua phân công khi tạo kế hoạch hoặc thao tác học phần. Khi chưa có hồ sơ, các API danh sách cá nhân trả danh sách rỗng; các API cần hồ sơ trả 400 (cố vấn), 403 (giảng viên) hoặc 404 (sinh viên).

- Ghi chú tư vấn kiểm tra sinh viên của enrollment thuộc cố vấn trước khi lưu; thiếu enrollment trả 404, ngoài phân công trả 403.
- Cảnh báo giảng viên bắt buộc có `presentation_id`; thiếu/null trả 422, ngoài phân công trả 403, sinh viên không thuộc học phần trả 404.
- Yêu cầu trợ giúp chỉ nhận `ADVISOR` hoặc `LECTURER`. Người nhận được chỉ định phải còn hoạt động, có đúng vai trò và được phân công. Yêu cầu gửi giảng viên bắt buộc chọn học phần mà sinh viên theo học. Khi không chỉ định người nhận, hệ thống chọn người phụ trách hợp lệ mới nhất; nếu chưa có thì lưu yêu cầu chưa gán người nhận (`target_user_id = null`).
- Frontend React gửi bearer token khi gọi dự báo; client gọi API trực tiếp cũng phải bổ sung token.

Kiểm thử quyền trên PostgreSQL sử dụng fixture riêng trong outer transaction và rollback sau từng test:

```powershell
python scripts/run_backend_tests.py -q -k 'CourseScopeTests or PredictionAccess'
```

Chạy từ gốc repository với môi trường Python có các dependency backend. Runner tự bật cờ opt-in sau khi chọn database riêng; test xác thực dự báo vẫn có thể chạy riêng không cần database.

### Cập nhật lịch sử dự báo ngày 18/10/2026

Cập nhật tiến độ có thay đổi chỉ số sẽ tạo snapshot mới, sao chép các chỉ số còn lại và ghi `snapshot_metadata` trong `raw_features_json`: nguồn `lecturer_assessment`, thời điểm quan sát, người cập nhật và ID snapshot trước. Chỉ cập nhật kết quả cuối kỳ không tạo snapshot. Nếu chưa có snapshot nền, cập nhật chỉ số trả 409 để tránh tạo dữ liệu hành vi giả từ giá trị 0.

Database có cột nullable `prediction_runs.inference_context`, lưu đủ 17 đầu vào thực tế, phiên bản model, threshold và SHA-256 của artifact. Trigger chặn sửa snapshot đã được dự báo, cũng như sửa đầu vào, danh tính model và kết quả của một dự báo đã lưu. Cơ chế này bảo vệ cập nhật; chính sách xóa CASCADE vẫn cần rà soát ở công việc database tiếp theo.

Artifact được lưu trong `artifacts/archive/<sha256>.joblib` từ đúng các byte đã nạp. Thư mục này bị bỏ qua bởi Git và phải được sao lưu cùng database khi vận hành. Không xóa artifact mà các bản ghi dự báo còn tham chiếu. Dữ liệu dự báo cũ có `inference_context = null` được ghi nhận là `LEGACY_UNVERIFIED`; không dựng lại thông tin từ hồ sơ hoặc registry hiện tại.

Database mới chạy script 03 qua Compose. Với database đã tồn tại, chạy từ gốc repository trước khi dùng mã mới:

```powershell
python apps/backend/scripts/apply_prediction_integrity.py
```

Script bổ sung cột và trigger trong một transaction, có thể chạy lại; đã áp dụng trên database local trong phiên này. Đây là bước nâng cấp phục vụ bảo toàn dự báo, chưa thay thế hệ thống Alembic được lên kế hoạch.

Kiểm tra lại một bản ghi có provenance, độc lập với hồ sơ hiện tại:

```powershell
python apps/backend/scripts/replay_prediction.py --prediction-id <UUID>
```

Lệnh kiểm tra checksum trước khi giải mã artifact, dùng đúng đầu vào/threshold đã lưu, rồi đối chiếu nhãn và xác suất. Bản ghi cũ thiếu context hoặc thiếu/hỏng artifact sẽ báo lỗi rõ ràng.

Quy ước kết quả hiện hành:

- Mỗi enrollment chỉ dùng dự báo mới nhất thuộc snapshot mới nhất, sắp xếp theo thời điểm rồi ID. Snapshot mới chưa dự báo không kế thừa kết quả cũ.
- API sinh viên trả 200 với `risk_probability: null`, `risk_level: "NOT_PREDICTED"` và danh sách khuyến nghị rỗng nếu enrollment hợp lệ chưa có dự báo hiện hành. Enrollment ngoài quyền vẫn trả 404.
- Cố vấn tổng hợp tất cả học phần: có bất kỳ môn nhãn 1 thì HIGH_RISK và lấy xác suất lớn nhất trong các môn nguy cơ cao; chỉ SAFE khi có học phần và tất cả đều được dự báo, đều nhãn 0. Các trường hợp còn lại là NOT_PREDICTED. Response kèm số môn đã/chưa dự báo và số môn nguy cơ cao.
- Các nhãn dùng `prediction_label` đã lưu, không tính lại bằng ngưỡng cố định 0.5. Trường `latest_risk_*` ở overview được giữ tên để tương thích nhưng mang ý nghĩa tổng hợp nêu trên.
- Thống kê lớp tách `safe_count`, `high_risk_count`, `not_predicted_count`; trung bình chỉ tính trên xác suất đã biết, trả null khi không có. Excel giữ ô xác suất trống và thêm số học phần chưa dự báo.
- Tạo kế hoạch mới yêu cầu dự báo của snapshot hiện hành; kế hoạch/nhiệm vụ cũ vẫn được giữ để theo dõi.
- `StudentFeatures` dùng chung cho dự báo thủ công và dữ liệu database: số đếm nguyên không âm, tỷ lệ trong [0,1], số hữu hạn, tín chỉ dương và danh mục OULAD hợp lệ. `date_registration` là số ngày nguyên có thể âm.
- Dự báo thủ công trả thêm `provenance`; frontend lưu vào lịch sử trình duyệt cùng bộ đầu vào. Endpoint này không tự tạo enrollment, snapshot hay prediction_run trong database. Khuyến nghị/radar sau dự báo dùng dữ liệu của lần phân tích đó.

### Cập nhật registry mô hình ngày 18/10/2026

`services/model_registry.py` là nguồn chọn model chung cho startup, health, dự báo thủ công, batch và CLI. Mỗi request truy vấn đúng một `ml_models.is_active = true`; không dùng `app.state.model` hoặc `MODEL_PATH` để chọn model nữa. Thiếu hoặc có nhiều model active thì từ chối dự báo, không dùng lại một model mặc định trong RAM.

- Khi khởi động, model active chưa có thông tin runtime được kiểm tra từ artifact nguồn rồi lưu hợp đồng vào `metadata_json.validated_runtime`. Các lần khởi động sau dùng artifact lưu theo SHA-256 đã xác nhận. Phải có database và artifact hợp lệ để startup thành công.
- Hợp đồng gồm model ID/version, SHA-256, threshold, cutoff 0.75, positive label 1 và thứ tự 17 cột. Kiểm tra metadata nhúng, metadata registry và metadata JSON ngoài nếu có; kiểm tra schema/lớp của pipeline và chạy một dự báo thử.
- Với model mới, `metadata_json.metadata_file_path` có thể chỉ rõ file JSON tuyệt đối hoặc tương đối với thư mục artifact. Nếu không chỉ định, registry tìm file cùng tên đuôi `.json`; artifact mặc định dùng `THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json`. Metadata nhúng phải đủ hợp đồng; mọi khai báo bổ sung đều phải khớp.
- Activate kiểm tra artifact trước khi đổi cờ active. Đổi cờ, runtime metadata và audit log được commit trong cùng transaction; lỗi nạp, kiểm tra, audit hoặc commit sẽ rollback. Model đã có runtime không được thay byte/threshold/cutoff/version tại chỗ; cần đăng ký một phiên bản mới.
- Reload kiểm tra lại đúng model đang active trong database. Reload không chuyển về file cấu hình hoặc tự kích hoạt model khác; nguồn hỏng không làm mất bản artifact đã xác nhận và model cũ vẫn sử dụng được.
- PostgreSQL advisory transaction lock tuần tự hóa activate/reload/khởi tạo giữa các tiến trình. Cache mỗi worker có tối đa 4 mục, dùng danh tính đã xác nhận làm khóa; mỗi request đọc lại database trước khi chọn cache. Worker thấy model mới ở request tiếp theo sau commit, không cần broadcast hoặc restart.
- Request đã bắt đầu tiếp tục dùng model đã chọn lúc bắt đầu; batch không đổi model giữa các sinh viên trong cùng lượt chạy. Cache có thể chứa candidate của transaction thất bại, nhưng candidate không thể được chọn nếu database chưa công bố active tương ứng.
- Các worker/replica phải dùng cùng database và truy cập cùng nội dung `artifacts/archive` tại đường dẫn tương ứng, ví dụ qua volume chung. Worker lạnh thiếu/hỏng artifact trả lỗi, không dùng phiên bản khác để thay thế. Cache trong RAM đã giữ artifact hợp lệ có thể tiếp tục phục vụ đúng danh tính đó.
- Provenance của dự báo mới bổ sung `model_id`, `cutoff_fraction`, `positive_label`. Kết quả batch có model ID/version, threshold và SHA-256; reload trả danh tính trong `model`. Health trả cùng danh tính khi sẵn sàng, HTTP 503 khi không thể xác nhận model active.

Không cần migration SQL mới cho công việc này: runtime dùng cột JSONB đã có. Partial unique index cho cờ active vẫn thuộc công việc 4; guard runtime từ chối trạng thái sai và khóa advisory chỉ bảo đảm tuần tự cho những thao tác đi qua registry.

Kiểm thử registry: `python scripts/run_backend_tests.py -q -k Registry`. Test dùng hai instance registry có cache riêng, API thực qua ASGI và PostgreSQL; có kiểm tra khóa bằng hai kết nối riêng. Chưa chạy thử tải nhiều tiến trình hệ điều hành hoặc nhiều máy.

## 1. Tổng quan và mức độ hoàn thiện

Backend phục vụ hệ thống cảnh báo nguy cơ học tập và hỗ trợ can thiệp cho bốn vai trò ADMIN, ADVISOR, LECTURER, STUDENT. Các chức năng đã có: xác thực JWT, quản trị tài khoản, học phần và phân công, đọc kết quả dự báo, radar, kế hoạch can thiệp, nhiệm vụ, ghi chú tư vấn, yêu cầu trợ giúp, xuất báo cáo Excel và audit log.

**Đánh giá:** kiến trúc phù hợp với dự án khóa luận và giai đoạn tích hợp, nhưng chưa đủ bằng chứng để coi là sẵn sàng vận hành production. Vấn đề chính là kiểm tra quyền trên bản ghi, tính đúng đắn của dự báo hàng loạt, sự khác biệt giữa DDL và ORM, cùng độ bao phủ kiểm thử tích hợp. Không gán điểm số chất lượng hoặc hiệu năng khi chưa có benchmark và tiêu chí đo.

| Khía cạnh | Điểm đã làm được | Giới hạn hiện tại |
| --- | --- | --- |
| Kiến trúc | Tách router, schema, repository, service, ORM và ML | Một phần nghiệp vụ/SQL còn nằm trực tiếp trong endpoint; transaction chưa có một quy ước chung |
| Xác thực | Access/refresh token có phân loại; kiểm tra user và trạng thái từ DB mỗi request | Chưa có logout/thu hồi token, rotation có lưu trạng thái hoặc hạn chế thử đăng nhập |
| Phân quyền | Guard theo vai trò và kiểm tra sở hữu ở nhiều API đọc/sửa | Một số API tạo dữ liệu chỉ kiểm tra vai trò |
| Database | Quan hệ nghiệp vụ rõ, UUID, FK, unique, JSONB và index | DDL khác ORM; chưa thấy hệ thống migration versioned |
| ML | Artifact, metadata, 17 đặc trưng, threshold trong artifact | Batch thiếu cột, fallback bị ghi như ML; active model DB không quyết định artifact trong RAM |
| Khả năng mở rộng | Async SQLAlchemy, pool kết nối | N+1 query; batch và xuất Excel chạy ngay trong request; thiếu giới hạn phân trang |
| Quan sát | Audit cho một số thao tác admin; health model | Thiếu readiness DB, request ID, metrics, log xử lý lỗi chuẩn hóa |
| Kiểm thử | Có test mock và các kịch bản nghiệp vụ | Test mock không xác minh FK, cascade, constraint, SQL hay race condition trên PostgreSQL |

## 2. Công nghệ và cấu trúc

| Thành phần | Hiện trạng |
| --- | --- |
| API | Python, FastAPI, Uvicorn |
| Validation/config | Pydantic 2, pydantic-settings, `.env` tại gốc repository |
| Persistence | SQLAlchemy 2 async, asyncpg, PostgreSQL 15 trong Compose |
| Authentication | python-jose JWT, bcrypt trực tiếp; không dùng passlib trong helper hiện tại |
| ML | joblib artifact, pandas DataFrame, pipeline scikit-learn/LightGBM |
| Report | openpyxl, StreamingResponse trả XLSX |
| Test | pytest, unittest.mock, httpx; kịch bản async cần pytest-asyncio |

```text
apps/backend/
├── main.py                    # app, lifespan, middleware, static frontend
├── api/router.py              # ghép router dưới /api/v1
├── api/v1/endpoints/           # auth/admin/advisor/lecturer/student/health/predictions
├── core/                      # settings, database, security, permissions
├── schemas/                   # request/response Pydantic
├── models/                    # SQLAlchemy models
├── repositories/              # user, student, academic queries
├── services/                  # auth, prediction, radar, audit
├── ml/                        # artifact loader và inference
├── artifacts/                 # joblib và metadata JSON
└── tests/                     # unit/mock và kịch bản tích hợp
```

## 3. Kiến trúc và luồng xử lý

### 3.1. Kiến trúc hiện tại

Backend là một ứng dụng đơn khối có phân module, không phải kiến trúc microservices. PostgreSQL là persistence chung; model nằm trong bộ nhớ từng process backend. Không thấy message broker, worker, cache phân tán hay scheduler trong mã nguồn backend được rà soát.

```mermaid
flowchart LR
    C[Postman / React] --> A[FastAPI routers]
    A --> P[JWT và RequireRoles]
    P --> D[AsyncSession PostgreSQL]
    A --> V[Pydantic schemas]
    A --> R[Repositories / SQL trong endpoint]
    R --> D
    A --> S[Auth / Radar / Audit / Prediction services]
    S --> D
    S --> M[Registry active từ PostgreSQL và cache theo SHA-256]
    L[Lifespan / Reload] --> M
    J[Artifact joblib] --> L
```

1. FastAPI nhận request, parse path/query/body và resolve dependency.
2. API bảo vệ lấy Bearer token qua `OAuth2PasswordBearer`, giải mã và yêu cầu `type=access`.
3. Backend đọc user/roles/profile từ DB, từ chối tài khoản khóa; `RequireRoles` kiểm tra vai trò.
4. Endpoint/repository kiểm tra phạm vi bản ghi nếu đã được triển khai, thực hiện truy vấn/ghi dữ liệu.
5. Endpoint hoặc repository commit; `get_db` rollback khi exception đi ra khỏi dependency và đóng session.
6. Response được serialize theo `response_model` nếu endpoint khai báo; nhiều API admin trả ORM/dict trực tiếp và chưa có response schema riêng.

Việc dùng async DB giúp request chờ I/O không giữ luồng theo cách đồng bộ, nhưng không làm các tác vụ CPU như ML hoặc tạo Excel tự động thành tác vụ nền.

### 3.2. Vòng đời và trạng thái model

`lifespan` khởi tạo registry từ model active trong PostgreSQL và xác nhận artifact trước khi phục vụ request. Cache giữ artifact theo danh tính đã xác nhận; database được đọc lại khi chọn model cho mỗi request. Loader có shim `_RemainderColsList` dùng API nội bộ sklearn để hỗ trợ unpickle; shim không bảo đảm tương thích mọi phiên bản.

Mỗi worker có bản model riêng. `/admin/ml/reload` chỉ thay model của process nhận request; chưa có cơ chế đồng bộ worker. `/admin/ml/models/activate` chỉ đổi `is_active` trong DB, không đổi `settings.model_path` và không nạp artifact của record được chọn.

### 3.3. Hai luồng dự báo khác nhau

**Dự báo độc lập:** `POST /predictions/` → `PredictionRequest` → `PredictionService.execute` → `predict` → DataFrame theo `model['feature_columns']` → `pipeline.predict_proba` → xác suất lớp 1 → so threshold. Chỉ trả kết quả; không ghi snapshot, prediction_run hay audit. Endpoint hiện public.

**Dự báo hàng loạt:** lấy active model record → quét toàn bộ snapshots → tạo feature dict → gọi predictor → ghi PredictionRun → commit → ghi audit và commit riêng. Hiện không chỉ chọn snapshot mới, không kiểm tra cutoff, không có chống tạo bản ghi trùng khi chạy lại. Feature dict thiếu `code_module`, có `num_of_prev_attempts` ngoài schema và dùng giá trị nhân khẩu/tín chỉ/đăng ký cố định. Exception bị nuốt và thay bằng `0.55` nếu `submission_rate < 0.7`, ngược lại `0.2`; kết quả này vẫn gắn `model_id` của mô hình ML. Đây là sai lệch về nguồn gốc dự báo cần sửa trước khi sử dụng kết quả batch làm bằng chứng AI.

### 3.4. Radar và khuyến nghị

Radar gồm tổng click, ngày hoạt động, tỷ lệ ngày hoạt động, click 7 ngày, tỷ lệ nộp bài và kỷ luật đúng hạn. Benchmark cố định trong `radar_service.py`: 350 click, 40 ngày, 0.45 tỷ lệ ngày, 30 click/7 ngày, 0.95 tỷ lệ nộp bài. Điểm phần lớn là `min(100, value/benchmark*100)`; kỷ luật là `max(0, 1-late_submissions*0.25)*100`.

Trường tên `percentile` thực tế là tỷ lệ đối sánh benchmark, **không phải percentile thống kê từ phân phối sinh viên**. Chưa có tính toán xác nhận benchmark thuộc top 25% trong runtime. Không có chặn dưới 0 cho tất cả chiều, nên dữ liệu âm có thể cho điểm âm. Khi không có snapshot, API radar dùng 0 cho các chỉ số; riêng kỷ luật có thể thành 100 vì số bài trễ bằng 0.

Khuyến nghị sinh viên là quy tắc trong `student_repo.get_enrollment_prediction`: nguy cơ >=0.5, số ngày hoạt động <20, bài trễ >0, click 7 ngày <15. Không phải recommendation model được huấn luyện; nhiều màn hình dùng ngưỡng 0.5 cố định thay vì ngưỡng của model record/artifact.

## 4. Xác thực, phân quyền và quy ước API

- Origin local: `http://127.0.0.1:8000`; mọi nghiệp vụ có prefix `/api/v1`.
- JSON request; UUID cho hầu hết ID, role ID là số nhỏ. Ngày dạng `YYYY-MM-DD`, thời gian là datetime ISO khi serialize.
- Header bảo vệ: `Authorization: Bearer <access_token>`.
- Login nhận `username` hoặc `email`, không gửi cả hai. Identifier có `@` được tra theo email; còn lại theo student_code. Backend vẫn cho sinh viên đăng nhập bằng email khi tài khoản tồn tại.
- Access token chứa `sub`, `email`, `roles`, `exp`, `type=access`; refresh token tương tự với `type=refresh`. Guard lấy vai trò hiện tại từ DB nên sửa roles có hiệu lực ở request sau.
- Mặc định access 1.440 phút, refresh 7 ngày; giá trị có thể bị override bởi `.env`. Refresh cấp cặp token mới nhưng không vô hiệu refresh token cũ.
- ADMIN qua guard của mọi vai trò, nhưng API student/advisor/lecturer vẫn có thể đòi profile/phân công của tài khoản admin. Không hiểu ADMIN bypass guard là mọi API tự động có dữ liệu toàn hệ thống.
- Các endpoint nghiệp vụ hiện mặc định HTTP 200 khi thành công, kể cả POST tạo mới và DELETE; chưa có khai báo 201/204 riêng.
- Lỗi HTTPException thường là `{"detail":"..."}`; lỗi validation 422 có `detail` dạng danh sách. Có thể có 500 do constraint chưa được xử lý.
- `/auth/login` được khai báo là tokenUrl OAuth2 nhưng nhận JSON thay vì OAuth2 form. Trong Postman nên login raw JSON và cấu hình Bearer trực tiếp.

| Mã | Ý nghĩa hiện tại |
| --- | --- |
| 400 | Nghiệp vụ không hợp lệ, email/mã học phần trùng được kiểm tra trước, thiếu prediction/plan |
| 401 | Thiếu/sai/hết hạn token, sai loại token, sai login |
| 403 | Tài khoản khóa, sai vai trò hoặc ngoài phạm vi khi API có ownership check |
| 404 | Không tồn tại hoặc không thuộc phạm vi; một số API cố ý dùng chung thông báo |
| 409 | Xung đột unique khi sửa user; lỗi ràng buộc khi xóa user |
| 422 | Body/path/query không khớp schema; predictor bắt ValueError/TypeError |
| 503 | `/predictions/` không có model trong app.state |
| 500 | Lỗi không được chuyển đổi, hoặc reload model thất bại |

## 5. Danh mục API

Danh mục đầy đủ, tham số, request/response schema và các nhánh lỗi được trích xuất từ AST ở phụ lục cuối tài liệu. API count đếm từng cặp method/path; GET và POST cùng path là hai operation. Các đường dẫn ở phụ lục đã có prefix đầy đủ.

### 5.1. Endpoint nền tảng

| Method | Path | Quyền | Kết quả |
| --- | --- | --- | --- |
| GET | `/` | Public | Message, `/docs`, `/app` |
| GET | `/api/v1/health` | Public | `status: ok/degraded`, `model_loaded`; không kiểm tra DB |
| POST | `/api/v1/predictions/` | Public | prediction và xác suất lớp nguy cơ; không persistence |

FastAPI còn sinh `/docs`, `/redoc`, `/openapi.json` và `/docs/oauth2-redirect`; đây là route framework, không tính vào operation nghiệp vụ. `/app` là static mount: ưu tiên frontend/dist nếu có, ngược lại mount thư mục frontend; source React không thay thế build Vite.

### 5.2. Auth

`POST /auth/login`, `POST /auth/refresh` public. `GET /auth/me`, `PUT /auth/profile`, `PUT /auth/change-password` dùng tài khoản xác thực bất kỳ. Profile chỉ sửa full_name, phone_number, avatar_url. Change-password cần old_password đúng và new_password tối thiểu 6 ký tự. Helper bcrypt hiện cắt mật khẩu dài quá 72 byte; reset admin có validator chống quá dài nhưng create/change-password chưa đồng nhất.

### 5.3. Admin

Quản trị users, roles, trạng thái, reset password; tạo/list courses; tạo presentations; phân công advisor/lecturer; list/activate/reload models; batch prediction; audit logs. `GET /users` có skip=0, limit=50; audit skip=0, limit=100 và action tùy chọn. Hai endpoint chưa giới hạn min/max pagination.

User PUT nhận subset trường, không phải thay thế toàn bộ resource. Profile phải phù hợp trường sửa; payload rỗng 400. Reset password trả message và user_id, không trả mật khẩu/hash, không mở khóa và không thu hồi token. DELETE user xóa vĩnh viễn qua FK cascade; backend chặn tự xóa và tự khóa nhưng chưa thấy bảo vệ admin cuối cùng hoặc tự bỏ vai trò ADMIN.

Create user chọn profile bằng `if/elif`: nếu gửi nhiều vai trò, có thể chỉ tạo một profile; STUDENT thiếu student_code hoặc LECTURER thiếu lecturer_code vẫn có thể được tạo user không có profile. Role code ở create chỉ được tìm trong DB, chưa xác nhận mọi code hợp lệ hoặc danh sách không rỗng. Update roles có kiểm tra code nhưng không tạo/xóa profile theo vai trò.

### 5.4. Advisor

Đọc classes/students, statistics, overview, radar, plans, notes và export XLSX theo advisor profile/phân công. Sửa plan và thêm task vào plan có join AdvisorStudent kiểm tra phạm vi. API tạo plan và tạo advising note hiện **chưa kiểm tra sinh viên/enrollment thuộc advisor**. Tạo plan cần PredictionRun gần nhất của sinh viên; không yêu cầu prediction phải high risk. Danh sách lớp hiện gán high_risk_count=0 và safe_count=total_students, khác endpoint statistics có tính thực tế.

### 5.5. Lecturer

Đọc risk-board/students và sửa assessment gọi `_ensure_course_ownership`; enrollment được kiểm tra thuộc presentation/student ở repository. API giao task hiện không gọi ownership helper, cũng không kiểm tra student thuộc presentation. Nó tìm một ACTIVE plan của sinh viên và thêm task category HOC_THUAT, không lưu presentation_id vào task. Alert advisor không kiểm tra phạm vi sinh viên và gán `target_user_id=current_user.id` (giảng viên), chưa resolve tài khoản cố vấn nhận cảnh báo.

### 5.6. Student

Đọc hồ sơ/courses/prediction/radar/tasks/plans/help requests của chính profile. Prediction và radar kiểm tra enrollment thuộc sinh viên; hoàn thành task join plan theo student. `PATCH /tasks/{task_id}/complete` cần JSON object, có thể `{}`; feedback tùy chọn. Không có thao tác đánh dấu chưa hoàn thành. Repository complete chưa chặn task của plan đã COMPLETED/CANCELLED và cập nhật timestamp lại khi gọi lặp.

Help request tạo status PENDING; schema chỉ mô tả target_role và chưa kiểm tra role/target_user/presentation theo quan hệ được phân công. Chưa có API dành cho cố vấn/giảng viên đọc và phản hồi help request, dù DB có response_note và status.

## 6. Database

### 6.1. Nguồn schema và quy ước

Có **19 bảng** trong DDL khởi tạo. DDL là mô tả khi tạo volume mới, không bảo đảm schema database đang chạy đã giống file. ORM là ánh xạ ứng dụng; chưa thấy Alembic hoặc migration versioned trong repository. SQL init chạy theo Docker entrypoint khi data directory mới, không chạy lại để nâng cấp database có dữ liệu.

`uuid-ossp` và `pgcrypto` được bật; ID dùng `gen_random_uuid()` trong DDL, ORM thường dùng `uuid.uuid4`. Thời gian DDL là TIMESTAMPTZ; ORM dùng timezone-aware datetime. JSONB dùng cho raw_features_json và metadata_json. Default ORM và default DB khác lớp thực thi, không được coi là thay thế nhau.

### 6.2. Nhóm bảng và quan hệ

| Nhóm | Bảng | Vai trò |
| --- | --- | --- |
| Identity | users, roles, user_roles | Tài khoản, danh mục vai trò, quan hệ N-N |
| Profile | student_profiles, advisor_profiles, lecturer_profiles | Hồ sơ riêng, mỗi loại UNIQUE user_id |
| Academic | courses, course_presentations, student_enrollments | Học phần, kỳ/lớp học phần, đăng ký sinh viên |
| Assignment | advisor_students, course_lecturers | Phân công chủ nhiệm và giảng dạy |
| Features/ML | student_feature_snapshots, ml_models, prediction_runs | Snapshot hành vi, metadata model, lần dự báo |
| Intervention | intervention_plans, intervention_tasks, advising_notes | Kế hoạch, nhiệm vụ, ghi chép theo enrollment |
| Support/audit | student_help_requests, audit_logs | Trợ giúp/cảnh báo và lịch sử thao tác |

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : grants
    users ||--o| student_profiles : profile
    users ||--o| advisor_profiles : profile
    users ||--o| lecturer_profiles : profile
    courses ||--o{ course_presentations : opens
    course_presentations ||--o{ student_enrollments : contains
    student_profiles ||--o{ student_enrollments : enrolls
    student_enrollments ||--o{ student_feature_snapshots : snapshots
    student_feature_snapshots ||--o{ prediction_runs : predicts
    ml_models ||--o{ prediction_runs : model
    prediction_runs ||--o{ intervention_plans : informs
    student_profiles ||--o{ intervention_plans : receives
    intervention_plans ||--o{ intervention_tasks : contains
    advisor_profiles ||--o{ advisor_students : assigned
    student_profiles ||--o{ advisor_students : assigned
    lecturer_profiles ||--o{ course_lecturers : teaches
    course_presentations ||--o{ course_lecturers : assigned
    student_enrollments ||--o{ advising_notes : notes
    advisor_profiles ||--o{ advising_notes : writes
    student_profiles ||--o{ student_help_requests : sends
    users |o--o{ student_help_requests : target
    course_presentations |o--o{ student_help_requests : context
    users |o--o{ prediction_runs : triggers
    users |o--o{ audit_logs : acts
```

**Phân biệt ID:** user_id là users.id; student_id/advisor_id/lecturer_id là ID bảng profile tương ứng. presentation_id là lớp học phần; enrollment_id là đăng ký của một sinh viên trong lớp. Không gửi user_id vào field student_id chỉ vì cùng có kiểu UUID.

### 6.3. Constraint và xóa dữ liệu

- UNIQUE email, role code, student_code, lecturer_code, profile.user_id, model.version.
- UNIQUE composite: user_roles(user_id,role_id), presentations(course_id,code_presentation), enrollments(student_id,presentation_id), course_lecturers(lecturer_id,presentation_id), advisor_students(advisor_id,student_id).
- advisor_students unique không gồm academic_year nên không lưu được nhiều phân công cùng cặp advisor/student qua nhiều năm.
- CHECK DDL: gender M/F; age_band 0-35/35-55/55<=; prediction_label 0/1; priority HIGH/MEDIUM/LOW; help target_role ADVISOR/LECTURER; help status PENDING/IN_PROGRESS/RESOLVED.
- Chưa có CHECK đầy đủ cho probability/rate [0,1], số đếm không âm, plan.status, task.category, final_result, một model active hoặc một plan active mỗi sinh viên.
- CASCADE users → profiles và user_roles; student → enrollment → snapshots → predictions → plans → tasks. Notes/assignments/help requests cũng có cascade theo profile/enrollment. Xóa tài khoản sinh viên có thể xóa lịch sử học tập sâu.
- DDL prediction_runs.model_id dùng RESTRICT, nhằm giữ model còn được tham chiếu. triggered_by_user_id và audit.user_id SET NULL; help target_user/presentation SET NULL.
- audit_logs.target_id là UUID thông thường, không FK; audit vẫn có thể giữ target ID sau khi resource bị xóa.
- Không có trigger updated_at trong SQL init; ORM onupdate chỉ có tác dụng khi cập nhật qua ORM, không áp dụng tự động cho mọi UPDATE SQL ngoài ứng dụng.

### 6.4. Index và hiệu năng

DDL có index mã sinh viên, enrollment theo student/presentation, snapshots(enrollment_id,cutoff_stage), prediction(created_at DESC)/snapshot_id, plans(student_id,status), tasks(plan_id,is_completed). UNIQUE đã tạo index riêng nên index student_code có thể trùng chức năng. Các truy vấn latest snapshot/latest prediction cần đo EXPLAIN ANALYZE trước khi thêm index composite `(enrollment_id, created_at DESC)` và `(snapshot_id, created_at DESC)`. Có thể cân nhắc audit(action,created_at) và assignment theo filter thực tế.

`get_advisor_students` thực hiện query prediction và plan/tasks cho từng sinh viên; `get_course_students`, `get_course_risk_board` đọc snapshot/prediction theo từng enrollment; list lecturer courses đếm từng presentation. Đây là N+1 query nhìn thấy trong code, chưa có số đo latency. Nên dùng subquery/window function cho bản ghi mới nhất, aggregate và pagination thay vì tăng pool như giải pháp chính.

### 6.5. Khác biệt DDL/ORM đáng chú ý

| Vị trí | DDL | ORM / schema ứng dụng | Ảnh hưởng |
| --- | --- | --- | --- |
| prediction_runs.model_id | ON DELETE RESTRICT | ON DELETE CASCADE | Tạo DB bằng ORM khác chính sách giữ lịch sử của SQL init |
| courses presentations/enrollments | Composite UNIQUE có trong DDL | Các composite này chưa khai báo ở models/academic.py | create_all nếu được dùng sẽ thiếu ràng buộc |
| ml_models.version | UNIQUE VARCHAR(30) | VARCHAR(50), không unique | Khác giới hạn và tính duy nhất |
| ml_models.is_active | DEFAULT TRUE | default=False | Tạo qua SQL và ORM khác trạng thái mặc định |
| ml_models name/path | VARCHAR(150)/VARCHAR(500) | VARCHAR(100)/VARCHAR(255) | Giới hạn dữ liệu khác |
| enrollment.date_registration | DEFAULT -10 | default=0 | Feature đầu vào có thể khác theo cách import |
| presentation.length | DEFAULT 260 | ORM không default; API default 268 | Cần thống nhất ý nghĩa độ dài học phần |
| advisor.office_location | VARCHAR(255) | ORM/API max 100 | API chỉ nhận subset khả năng lưu DB |
| task.target_metric | VARCHAR(255) | ORM VARCHAR(100) | Khác giới hạn khi tạo schema bằng ORM |
| task.priority | CHECK chỉ HIGH/MEDIUM/LOW | Schema TaskCreateIn mô tả thêm URGENT | URGENT qua Pydantic rồi có thể lỗi constraint 500 |
| profile/label/help CHECK | DDL có CHECK | ORM nhiều bảng không mô tả CHECK | Schema tạo bằng ORM sẽ có kiểm soát khác |

Phụ lục DDL phía dưới giữ nguyên khai báo cột/default/FK/check/unique để tham chiếu đầy đủ. Để xác nhận DB thật cần introspection schema/constraint trên PostgreSQL, chưa thực hiện trong lần viết tài liệu này.

## 7. Mô hình và dữ liệu đầu vào

Artifact: `artifacts/model_hco_vnls_lightgbm_cutoff75.joblib`. Metadata: [THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json](artifacts/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json).

| Metadata | Giá trị |
| --- | --- |
| Mô hình | HCO-VNLS + LightGBM 80 cây — cutoff 75% |
| Positive label / threshold | 1 / 0.5 |
| Train rows / test excluded | 19.712 / 3.447 |
| Validation accuracy | 0.8740849195 |
| Validation average precision risk | 0.8967566497 |
| Validation recall risk | 0.6898029135 |
| Phiên bản nguồn | Python 3.12.6, sklearn 1.6.0, LightGBM 4.7.0, pandas 2.2.2, joblib 1.4.2 |

Đây là số liệu `validation_reference_train_only` trong metadata, không phải test độc lập chạy trong lần đánh giá này. Average precision không phải ROC-AUC; cần đối chiếu và sửa dữ liệu seed đang sử dụng chỉ số này trong cột roc_auc. Metadata ghi đường dẫn dữ liệu/notebook nguồn nhưng không xác nhận các file đó còn trong checkout.

17 field được mô tả đầy đủ trong phụ lục StudentFeatures. Predictor chọn đúng tên/thứ tự cột từ artifact, vì vậy thiếu cột có thể phát sinh KeyError. `/predictions/` chỉ bắt ValueError/TypeError; KeyError từ artifact/schema không đồng bộ có thể thành 500. Schema hiện khai báo numeric float mà chưa giới hạn số âm, rate, giá trị hữu hạn và category; cần validate theo domain, không chỉ theo kiểu dữ liệu.

## 8. Đánh giá rủi ro và ưu tiên cải thiện

Các phát hiện dưới đây dựa trên source; chưa phải xác nhận khai thác thực tế hoặc benchmark. P1: ưu tiên sửa trước khi dùng dữ liệu thật/đưa ra ngoài; P2: cần sửa để tích hợp và vận hành đáng tin cậy; P3: cải thiện chất lượng/bảo trì.

| Mức | Phát hiện và bằng chứng | Tác động | Hướng xử lý |
| --- | --- | --- | --- |
| P1 | advisor.create_intervention_plan không gọi advisor_owns_student; create_advising_note không kiểm tra enrollment | Cố vấn có thể ghi dữ liệu cho sinh viên ngoài phân công nếu biết UUID hợp lệ | Guard ownership chung, kiểm tra trước query/insert; test hai cố vấn khác lớp |
| P1 | lecturer.assign_course_task không kiểm tra presentation ownership/student enrollment; alert_advisor không kiểm tra phạm vi | Giao task/cảnh báo ngoài lớp phụ trách | Kiểm tra course assignment và enrollment; lưu ngữ cảnh học phần; resolve đúng cố vấn nhận |
| P1 | admin.batch_predict thiếu code_module và nuốt mọi exception | Quy tắc fallback bị lưu như dự báo model; báo cáo nguy cơ sai nguồn gốc | Join course/profile/enrollment để dựng đúng 17 field; lỗi phải được báo riêng, không giả lập ML |
| P1 | activate chỉ đổi DB; reload vẫn đọc settings.model_path | PredictionRun có thể gắn phiên bản khác model thật trong RAM | Artifact registry, kiểm tra checksum/schema, activate load đúng file và gắn version vào runtime |
| P1 | predictions public, không rate limit; login cũng không throttling | Suy luận có thể bị lạm dụng, đăng nhập thử nhiều lần | Quyền truy cập theo use case; rate limit và giới hạn kích thước/thời gian |
| P2 | password helper truncate >72 byte; create/change thiếu giới hạn byte | Hai mật khẩu có cùng tiền tố dài có thể tương đương bcrypt | Một validator dùng chung, từ chối vượt giới hạn thay vì cắt |
| P2 | Reset/change-password không thu hồi access/refresh token | Phiên cũ tiếp tục hoạt động sau đổi mật khẩu | token version hoặc session store; refresh rotation và revoke |
| P2 | Create user không validate role/profile đầy đủ, if/elif nhiều vai trò | Tài khoản có quyền nhưng thiếu hồ sơ; dữ liệu nghiệp vụ không dùng được | Quy tắc role/profile rõ; validate trước transaction và xử lý IntegrityError |
| P2 | Một số constraint/FK insert không được map lỗi HTTP | Dữ liệu sai có thể thành 500 thay vì lỗi nghiệp vụ | Domain validation + handler rollback/409/422 thống nhất |
| P2 | Audit create/batch commit sau business commit; reload đổi RAM trước commit audit | Thất bại audit có thể trả lỗi dù hành động đã xảy ra | Commit DB/audit cùng transaction; thiết kế nhất quán khi thay runtime |
| P2 | Batch quét tất cả snapshots, chạy lại thêm records; execution_time_ms từng run cố định 10 | Trùng kết quả, thống kê thời gian không thật, request lâu | Chọn snapshot/cutoff/model hợp lệ; idempotency; đo thời gian; queue worker khi cần |
| P2 | Không prediction thường bị gán 0/SAFE; classes gán toàn bộ SAFE | Đồng nhất thiếu dữ liệu với an toàn | Trạng thái UNKNOWN/NOT_PREDICTED, thống kê riêng và nhất quán |
| P2 | Assessment sửa snapshot đã dùng để dự báo; không snapshot mới/re-predict | Mất khả năng tái lập vì input thay đổi sau khi lưu prediction | Snapshot bất biến/versioned, liên kết input hash, tạo dự báo mới |
| P2 | Lệch DDL/ORM và thiếu migration | Môi trường khác nhau có constraint/cascade khác | Alembic làm nguồn migration, kiểm tra drift và migration trên DB thử |
| P2 | Wildcard CORS và allow_private_network trong main.py | Cấu hình dev chưa giới hạn origin; tham số có thể không hợp phiên bản Starlette cài | Xác minh phiên bản runtime và allowlist origin theo môi trường |
| Đã xử lý 18/10 | Manifest backend runtime/test khai báo asyncpg, joblib, bcrypt, pytest-asyncio và SQLAlchemy asyncio | Đã dựng image Python sạch | Xem requirements trong apps/backend |
| P2 | Không thấy Dockerfile tương ứng cấu hình backend/frontend trong Compose | Không thể coi compose build toàn bộ là luồng hoàn chỉnh | Thêm Dockerfile, biến SECRET_KEY/MODEL_PATH, health và deployment checks |
| P3 | get_client_ip tin X-Forwarded-For do client gửi | Audit IP có thể bị giả nếu không qua proxy đáng tin | Trust proxy allowlist; chuẩn hóa IP tại reverse proxy |
| P3 | N+1, list không pagination và limit admin không giới hạn | Latency/bộ nhớ tăng theo dữ liệu | Batch query, bounded pagination, đo EXPLAIN/latency trước tối ưu |
| P3 | Schema dùng str thay Enum, thiếu bounds/length; profile update cho phép chuỗi rỗng | Constraint DB và API không khớp | Enum/Literal và validation domain dùng chung |
| P3 | Thiếu API enrollment/snapshot ingestion/help response | Luồng nghiệp vụ chưa khép kín từ API | Thiết kế import có kiểm soát, đăng ký học và hộp thư xử lý trợ giúp |

Điểm mạnh cần giữ: get_current_user xác minh trạng thái/role hiện tại; dữ liệu user response không chứa hash; reset password dùng SecretStr và không ghi mật khẩu vào audit; user edit/reset/delete có xử lý rollback; student ownership và các API advisor đọc/sửa plan đã có ràng buộc; selectinload tránh lazy-load một số quan hệ trong async response.

## 9. Cài đặt và chạy local

Chạy từ gốc repository, dùng Python 3.12. Không ghi đè `.env` đang sử dụng.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Các dependency này đã nằm trong manifest backend được pin phiên bản.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d postgres pgadmin
cd apps/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Cập nhật 18/10/2026: manifest runtime/test đã đầy đủ; Dockerfile backend/frontend đã được bổ sung và kiểm thử trong stack riêng. Database Compose mở cổng host 5433, bên trong 5432. pgAdmin mặc định cổng 5050. Xem hướng dẫn công việc 5 ở cuối tài liệu.

| Biến | Công dụng |
| --- | --- |
| DATABASE_URL | Bắt buộc; dạng postgresql://USER:PASSWORD@127.0.0.1:5433/DB; backend chuyển sang asyncpg |
| SECRET_KEY | Bắt buộc; khóa ký JWT riêng môi trường, không dùng khóa mẫu khi vận hành |
| ALGORITHM | Mặc định HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Mặc định 1440 |
| REFRESH_TOKEN_EXPIRE_DAYS | Field settings mặc định 7 |
| MODEL_PATH | Cấu hình cũ; không còn chọn model phục vụ API. Artifact phục vụ lấy từ model active trong database |
| APP_NAME / APP_VERSION | Metadata ứng dụng |
| POSTGRES_USER/PASSWORD/DB/HOST_PORT | Cấu hình Compose; phải khớp DATABASE_URL |

BACKEND_HOST/PORT trong `.env.example` không tự thay lệnh uvicorn; `main.py` chạy trực tiếp hardcode host/port. Cần kiểm tra traceback nếu startup lỗi middleware/artifact/dependency. Không xóa volume để áp dụng schema mới vào DB có dữ liệu; dùng migration và backup.

## 10. Kiểm thử API bằng Postman

1. Import `http://127.0.0.1:8000/openapi.json` hoặc tải JSON rồi import file.
2. Environment: base_url=`http://127.0.0.1:8000`, access_token, refresh_token; chọn đúng environment.
3. GET `{{base_url}}/api/v1/health`: public, model_loaded=true khi model sẵn sàng; chưa kiểm tra DB.
4. POST `{{base_url}}/api/v1/auth/login`, No Auth, Body raw JSON; không dùng OAuth2 form.
5. Lưu token từ response; Collection Authorization Bearer Token=`{{access_token}}`. Các request bảo vệ inherit collection auth.
6. GET auth/me → admin/users → tạo tài khoản thử → login MSSV → student/profile/courses. Giữ token riêng từng vai trò.
7. Test chéo phạm vi bằng hai advisor/lecturer/student có dữ liệu khác nhau; biết UUID người khác không được cấp quyền ghi/đọc.

Login mẫu (thay mật khẩu thực tế; seed local admin mặc định là admin):

```json
{"username":"admin@huit.edu.vn","password":"<mat-khau-admin>"}
```

Post-response script cho login và refresh:

```javascript
pm.test('HTTP 200', () => pm.response.to.have.status(200));
if (pm.response.code === 200) {
  const data = pm.response.json();
  pm.environment.set('access_token', data.access_token);
  pm.environment.set('refresh_token', data.refresh_token);
}
```

Refresh public: `POST /api/v1/auth/refresh`, body `{"refresh_token":"{{refresh_token}}"}`. `/auth/me` phải trả 401 khi dùng refresh token thay access token.

Tạo student qua admin/users:

```json
{
  "email":"postman.student@example.com",
  "password":"Postman123!",
  "full_name":"Sinh viên Postman",
  "role_codes":["STUDENT"],
  "student_code":"PM20260001",
  "gender":"M",
  "highest_education":"A Level or Equivalent",
  "age_band":"0-35"
}
```

Lấy user ID từ response; student profile ID nằm trong student_profile.id. Sinh viên mới chưa có enrollments nên courses/tasks rỗng là bình thường. Chưa có public registration hoặc API enrollment creation trong backend hiện tại.

Dự báo độc lập `POST {{base_url}}/api/v1/predictions/`, No Auth:

```json
{
  "features": {
    "code_module":"AAA", "gender":"M",
    "highest_education":"A Level or Equivalent", "age_band":"0-35",
    "studied_credits":60, "date_registration":-10,
    "total_clicks_to_t":1500, "clicks_resource_to_t":400,
    "clicks_url_to_t":200, "active_days_to_t":45,
    "assessments_submitted_to_t":5, "late_submissions_to_t":1,
    "active_day_ratio":0.5, "submission_rate":0.6,
    "days_since_last_activity":3, "clicks_recent_7":80,
    "clicks_recent_30":350
  }
}
```

Response có prediction 0/1 và confidence trong [0,1]; confidence là xác suất nguy cơ, không phải độ tin cậy của nhãn đã chọn. Không cố định xác suất mẫu thành assertion nếu không khóa artifact/input/version.

| Nhóm test | Trường hợp cần xác minh |
| --- | --- |
| Auth | Login đúng/sai, gửi hai identifier, thiếu identifier, token hết hạn/sai loại, user khóa |
| Admin | Vai trò khác gọi admin bị 403; trùng email/mã; missing profile; tự khóa/xóa; reset length/UTF-8; rollback/audit |
| Ownership | Sinh viên khác enrollment/task; advisor khác lớp; lecturer khác presentation/student |
| DB | FK không tồn tại, unique, cascade/restrict/set null, migration drift, rollback sau lỗi |
| ML | Đủ/thiếu field, giá trị ngoài domain, batch dùng đúng model/input, không fallback giả ML, chạy lặp |
| Workflow | Prediction → plan/tasks → student complete → advisor stats; help request → xử lý khi API được bổ sung |
| Report | XLSX đúng dữ liệu/phạm vi, không gán thiếu prediction thành SAFE, tải file được |

## 11. Kiểm thử tự động và giới hạn bằng chứng

Có các file test_auth, test_sprint3/4/5, test_login_identifier, test_admin_accounts, test_admin_password_reset. Ba file cuối dùng mock và/hoặc dependency override; không xác nhận hoạt động SQL thực trên PostgreSQL. Các kịch bản sprint/auth phụ thuộc dữ liệu và môi trường, cần đọc fixture trước khi chạy trên database có giá trị vì test có thể ghi dữ liệu.

```powershell
# Từ gốc repository, nhóm mock/unit
.\.venv\Scripts\python.exe -m pytest apps/backend/tests/test_login_identifier.py apps/backend/tests/test_admin_accounts.py apps/backend/tests/test_admin_password_reset.py -q

# Chỉ chạy trên database thử nghiệm có cấu hình/dữ liệu phù hợp
cd apps/backend
python -m pytest tests -q
```

Lần rà soát này thử đọc health/OpenAPI qua localhost nhưng môi trường thực thi chặn socket (WinError 10013); không xác nhận server hay database qua HTTP. Kết quả chạy nhóm test được ghi ở ghi chú xác minh cuối tài liệu. Không sử dụng kết quả unit/mock để kết luận end-to-end đạt.

**Kết quả kiểm tra ngày 13/10/2026:** lệnh pytest cho ba file mock/unit thu thập 19 test, nhưng cả 19 gặp lỗi setup; lỗi đầu tiên báo async autouse fixture `cleanup_db_connections` không có plugin/hook xử lý. `pip show pytest-asyncio` xác nhận plugin không được cài trong `.venv` hiện tại. Có 7 cảnh báo deprecation Pydantic. Các test chưa chạy đến assertion, vì vậy đây là lỗi cấu hình môi trường test, không phải kết luận 19 chức năng nghiệp vụ lỗi. Cần cài pytest-asyncio và cấu hình async fixture đúng chế độ (ví dụ auto hoặc dùng `pytest_asyncio.fixture` phù hợp) rồi chạy lại.

Thử chạy unittest trực tiếp từ backend để tránh fixture pytest không hoàn tất trong phiên kiểm tra và đã được dừng; không có kết quả pass để báo cáo. Đã kiểm tra nội dung tài liệu bằng AST: đủ 52 operation `/api/v1`, 53 lớp schema và 19 khối CREATE TABLE; code fence cân bằng. Không chạy các kịch bản tích hợp ghi dữ liệu vào PostgreSQL thật.

## 12. Lộ trình đề xuất

1. Sửa ownership cho tất cả API ghi; thêm test chéo user/lớp/học phần và giới hạn predictions/login.
2. Sửa batch dựng đúng input từ DB; bỏ fallback im lặng; đồng bộ model registry/artifact/runtime và threshold.
3. Thống nhất DDL/ORM bằng migration; bổ sung constraints trạng thái/rate, chính sách lưu lịch sử/cascade và snapshot bất biến.
4. Chuẩn hóa role/profile, validator password, lỗi HTTP và transaction/audit; thêm thu hồi phiên sau đổi mật khẩu.
5. Hoàn thiện API enrollment/import snapshots, help-request response, dữ liệu UNKNOWN và thống kê đúng.
6. Tối ưu query sau khi đo; bounded pagination; job nền cho batch/export lớn; metrics/readiness/log cấu trúc.
7. Khóa dependency, hoàn thiện Docker, chạy integration/E2E trên PostgreSQL thử và load test trước khi triển khai.


## Phụ lục A. Toàn bộ operation API theo mã nguồn

Tham số dưới đây bỏ các dependency nội bộ (`db`, `current_user`, `request`). `{...}` là path; `payload`/`data` là JSON body; các tham số còn lại là query. Kiểu response là tên schema Pydantic ở phụ lục B. Lỗi liệt kê ở từng operation chỉ gồm HTTPException trực tiếp trong handler; lỗi dependency/repository/validation vẫn áp dụng theo mục 4.

### A.auth. `auth`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **POST** `/api/v1/auth/login` | Public | `payload: LoginRequest` (bắt buộc) | `TokenResponse` — Đăng nhập tài khoản | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/auth.py:22` |
| **POST** `/api/v1/auth/refresh` | Public | `payload: RefreshRequest` (bắt buộc) | `TokenResponse` — Cấp mới token | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/auth.py:32` |
| **GET** `/api/v1/auth/me` | JWT bất kỳ | Không | `UserOut` — Lấy thông tin tài khoản hiện tại | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/auth.py:42` |
| **PUT** `/api/v1/auth/profile` | JWT bất kỳ | `payload: UserUpdateProfile` (bắt buộc) | `UserOut` — Cập nhật hồ sơ cá nhân | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/auth.py:50` |
| **PUT** `/api/v1/auth/change-password` | JWT bất kỳ | `payload: ChangePasswordRequest` (bắt buộc) | `—` — Đổi mật khẩu | status.HTTP_400_BAD_REQUEST: 'Mật khẩu hiện tại không chính xác' | `apps/backend/api/v1/endpoints/auth.py:70` |

### A.admin. `admin`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **GET** `/api/v1/admin/users` | ADMIN | `skip: int` = `0`<br>`limit: int` = `50` | `List[UserOut]` — Danh sách người dùng | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:68` |
| **GET** `/api/v1/admin/users/{user_id}` | ADMIN | `user_id: uuid.UUID` (bắt buộc) | `UserOut` — Xem chi tiết tài khoản | 404: 'Người dùng không tồn tại' | `apps/backend/api/v1/endpoints/admin.py:91` |
| **PUT** `/api/v1/admin/users/{user_id}/reset-password` | ADMIN | `user_id: uuid.UUID` (bắt buộc)<br>`payload: AdminPasswordResetIn` (bắt buộc) | `AdminPasswordResetOut` — Admin đặt lại mật khẩu tài khoản | 404: 'Người dùng không tồn tại' | `apps/backend/api/v1/endpoints/admin.py:100` |
| **PUT** `/api/v1/admin/users/{user_id}` | ADMIN | `user_id: uuid.UUID` (bắt buộc)<br>`payload: AdminUserUpdateIn` (bắt buộc) | `UserOut` — Sửa thông tin tài khoản | 404: 'Người dùng không tồn tại'<br>400: 'Không có thông tin cập nhật'<br>400: f'Tài khoản không có hồ sơ phù hợp để sửa {field}'<br>409: 'Email, mã sinh viên hoặc mã giảng viên đã được sử dụng' | `apps/backend/api/v1/endpoints/admin.py:126` |
| **DELETE** `/api/v1/admin/users/{user_id}` | ADMIN | `user_id: uuid.UUID` (bắt buộc) | `—` — Xóa tài khoản và hồ sơ liên quan | 400: 'Không thể xóa tài khoản đang sử dụng'<br>404: 'Người dùng không tồn tại'<br>409: 'Không thể xóa do tài khoản còn dữ liệu liên kết. Hãy khóa tài khoản.' | `apps/backend/api/v1/endpoints/admin.py:157` |
| **POST** `/api/v1/admin/users` | ADMIN | `payload: AdminUserCreateIn` (bắt buộc) | `UserOut` — Tạo mới tài khoản người dùng | status.HTTP_400_BAD_REQUEST: 'Email này đã được sử dụng trong hệ thống' | `apps/backend/api/v1/endpoints/admin.py:177` |
| **PUT** `/api/v1/admin/users/{user_id}/status` | ADMIN | `user_id: uuid.UUID` (bắt buộc)<br>`payload: UserStatusUpdateIn` (bắt buộc) | `—` — Kích hoạt hoặc khóa tài khoản | 400: 'Không thể khóa tài khoản đang sử dụng'<br>status.HTTP_404_NOT_FOUND: 'Người dùng không tồn tại' | `apps/backend/api/v1/endpoints/admin.py:250` |
| **POST** `/api/v1/admin/users/{user_id}/roles` | ADMIN | `user_id: uuid.UUID` (bắt buộc)<br>`payload: UserRolesUpdateIn` (bắt buộc) | `UserOut` — Cập nhật vai trò của người dùng | status.HTTP_404_NOT_FOUND: 'Người dùng không tồn tại'<br>status.HTTP_400_BAD_REQUEST: 'Danh sách vai trò không được để trống'<br>status.HTTP_400_BAD_REQUEST: f'Vai trò không hợp lệ: {missing}' | `apps/backend/api/v1/endpoints/admin.py:279` |
| **GET** `/api/v1/admin/academic/courses` | ADMIN | Không | `—` — Danh sách học phần OULAD | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:326` |
| **POST** `/api/v1/admin/academic/courses` | ADMIN | `payload: CourseCreateIn` (bắt buộc) | `—` — Tạo mới học phần | status.HTTP_400_BAD_REQUEST: 'Mã môn học đã tồn tại' | `apps/backend/api/v1/endpoints/admin.py:336` |
| **POST** `/api/v1/admin/academic/presentations` | ADMIN | `payload: CoursePresentationCreateIn` (bắt buộc) | `—` — Mở kỳ học / lớp học phần | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:358` |
| **POST** `/api/v1/admin/academic/assign-advisor` | ADMIN | `payload: AssignAdvisorIn` (bắt buộc) | `—` — Phân công GVCN cho sinh viên theo lớp sinh hoạt | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:376` |
| **POST** `/api/v1/admin/academic/assign-lecturer` | ADMIN | `payload: AssignLecturerIn` (bắt buộc) | `—` — Phân công GVBM phụ trách lớp học phần | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:393` |
| **GET** `/api/v1/admin/ml/models` | ADMIN | Không | `List[MLModelOut]` — Danh sách các phiên bản mô hình ML | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:412` |
| **POST** `/api/v1/admin/ml/reload` | ADMIN | Không | `—` — Nạp lại mô hình LightGBM vào bộ nhớ RAM máy chủ | status.HTTP_500_INTERNAL_SERVER_ERROR: f'Lỗi khi nạp lại mô hình: {str(e)}' | `apps/backend/api/v1/endpoints/admin.py:422` |
| **POST** `/api/v1/admin/ml/models/activate` | ADMIN | `payload: ActivateModelIn` (bắt buộc) | `MLModelOut` — Kích hoạt một phiên bản mô hình ML | status.HTTP_404_NOT_FOUND: 'Phiên bản mô hình không tồn tại' | `apps/backend/api/v1/endpoints/admin.py:448` |
| **POST** `/api/v1/admin/ml/batch-predict` | ADMIN | Không | `BatchPredictResultOut` — Quét và dự báo rủi ro hàng loạt mốc Cutoff 75% | status.HTTP_400_BAD_REQUEST: 'Chưa có mô hình ML nào được kích hoạt' | `apps/backend/api/v1/endpoints/admin.py:478` |
| **GET** `/api/v1/admin/system/audit-logs` | ADMIN | `skip: int` = `0`<br>`limit: int` = `100`<br>`action: Optional[str]` = `None` | `List[AuditLogOut]` — Tra cứu nhật ký thao tác hệ thống | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/admin.py:577` |

### A.advisor. `advisor`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **GET** `/api/v1/advisor/classes` | ADVISOR / ADMIN | Không | `List[ClassOverviewOut]` — Danh sách lớp sinh hoạt phụ trách | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/advisor.py:54` |
| **GET** `/api/v1/advisor/students` | ADVISOR / ADMIN | `class_name: Optional[str]` = `None` | `List[AdvisorStudentSummaryOut]` — Danh sách sinh viên lớp chủ nhiệm | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/advisor.py:65` |
| **POST** `/api/v1/advisor/interventions` | ADVISOR / ADMIN | `payload: PlanCreateIn` (bắt buộc) | `PlanOut` — Lập kế hoạch can thiệp cho sinh viên | status.HTTP_400_BAD_REQUEST: 'Sinh viên chưa có bản ghi dự báo nguy cơ học máy (PredictionRun)' | `apps/backend/api/v1/endpoints/advisor.py:77` |
| **POST** `/api/v1/advisor/advising-notes` | ADVISOR / ADMIN | `payload: NoteCreateIn` (bắt buộc) | `NoteOut` — Ghi chép sổ tay tư vấn sinh viên | status.HTTP_400_BAD_REQUEST: 'Tài khoản chưa có hồ sơ Cố vấn học tập (AdvisorProfile)' | `apps/backend/api/v1/endpoints/advisor.py:114` |
| **GET** `/api/v1/advisor/classes/{class_name}/statistics` | ADVISOR / ADMIN | `class_name: str` (bắt buộc) | `ClassStatisticsOut` — Thống kê tình hình rủi ro của một lớp sinh hoạt | status.HTTP_404_NOT_FOUND: 'Không tìm thấy lớp này hoặc bạn không được phân công chủ nhiệm' | `apps/backend/api/v1/endpoints/advisor.py:165` |
| **GET** `/api/v1/advisor/students/{student_id}/overview` | ADVISOR / ADMIN | `student_id: uuid.UUID` (bắt buộc) | `StudentOverviewOut` — Báo cáo 360° về sinh viên lớp chủ nhiệm | status.HTTP_404_NOT_FOUND: 'Sinh viên không tồn tại trong lớp chủ nhiệm của bạn' | `apps/backend/api/v1/endpoints/advisor.py:185` |
| **GET** `/api/v1/advisor/students/{student_id}/radar` | ADVISOR / ADMIN | `student_id: uuid.UUID` (bắt buộc)<br>`enrollment_id: Optional[uuid.UUID]` = `None` | `RadarDataOut` — Biểu đồ Radar năng lực 6D của sinh viên (theo học phần) | status.HTTP_404_NOT_FOUND: 'Không tìm thấy dữ liệu radar cho sinh viên/học phần yêu cầu' | `apps/backend/api/v1/endpoints/advisor.py:205` |
| **GET** `/api/v1/advisor/interventions` | ADVISOR / ADMIN | `status_filter: Optional[str]` = `None` | `List[PlanOut]` — Danh sách kế hoạch can thiệp của lớp chủ nhiệm | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/advisor.py:225` |
| **PUT** `/api/v1/advisor/interventions/{plan_id}` | ADVISOR / ADMIN | `plan_id: uuid.UUID` (bắt buộc)<br>`payload: PlanUpdateIn` (bắt buộc) | `PlanOut` — Cập nhật kế hoạch can thiệp | status.HTTP_404_NOT_FOUND: 'Kế hoạch can thiệp không tồn tại hoặc không thuộc lớp chủ nhiệm của bạn' | `apps/backend/api/v1/endpoints/advisor.py:237` |
| **POST** `/api/v1/advisor/interventions/{plan_id}/tasks` | ADVISOR / ADMIN | `plan_id: uuid.UUID` (bắt buộc)<br>`payload: TaskCreateIn` (bắt buộc) | `TaskOut` — Bổ sung nhiệm vụ vào kế hoạch can thiệp | status.HTTP_404_NOT_FOUND: 'Kế hoạch can thiệp không tồn tại hoặc không thuộc lớp chủ nhiệm của bạn' | `apps/backend/api/v1/endpoints/advisor.py:265` |
| **GET** `/api/v1/advisor/students/{student_id}/notes` | ADVISOR / ADMIN | `student_id: uuid.UUID` (bắt buộc) | `List[NoteOut]` — Ghi chép sổ tay tư vấn của sinh viên | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/advisor.py:295` |
| **GET** `/api/v1/advisor/export/risk-report` | ADVISOR / ADMIN | `class_name: Optional[str]` = `None` | `—` — Xuất báo cáo nguy cơ của lớp chủ nhiệm ra Excel (.xlsx) | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/advisor.py:309` |

### A.lecturer. `lecturer`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **GET** `/api/v1/lecturer/courses` | LECTURER / ADMIN | Không | `List[LecturerCourseOut]` — Danh sách lớp học phần giảng dạy | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/lecturer.py:62` |
| **GET** `/api/v1/lecturer/courses/{presentation_id}/risk-board` | LECTURER / ADMIN | `presentation_id: uuid.UUID` (bắt buộc) | `List[StudentRiskInCourseOut]` — Bảng cảnh báo nguy cơ học phần | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/lecturer.py:73` |
| **GET** `/api/v1/lecturer/courses/{presentation_id}/students` | LECTURER / ADMIN | `presentation_id: uuid.UUID` (bắt buộc) | `List[CourseStudentOut]` — Danh sách sinh viên lớp học phần | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/lecturer.py:83` |
| **PUT** `/api/v1/lecturer/courses/{presentation_id}/students/{student_id}/assessment` | LECTURER / ADMIN | `presentation_id: uuid.UUID` (bắt buộc)<br>`student_id: uuid.UUID` (bắt buộc)<br>`payload: AssessmentUpdateIn` (bắt buộc) | `—` — Cập nhật điểm/tiến độ đánh giá của sinh viên trong lớp học phần | status.HTTP_404_NOT_FOUND: 'Không tìm thấy sinh viên trong lớp học phần này' | `apps/backend/api/v1/endpoints/lecturer.py:96` |
| **POST** `/api/v1/lecturer/courses/{presentation_id}/tasks` | LECTURER / ADMIN | `presentation_id: uuid.UUID` (bắt buộc)<br>`payload: CourseTaskAssignIn` (bắt buộc) | `TaskOut` — Giao bài tập bổ trợ môn học cho sinh viên | status.HTTP_400_BAD_REQUEST: 'Sinh viên chưa có kế hoạch can thiệp nào đang hoạt động' | `apps/backend/api/v1/endpoints/lecturer.py:122` |
| **POST** `/api/v1/lecturer/students/{student_id}/alert-advisor` | LECTURER / ADMIN | `student_id: uuid.UUID` (bắt buộc)<br>`payload: AlertAdvisorIn` (bắt buộc) | `—` — Gửi cảnh báo học vụ tới Giáo viên chủ nhiệm | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/lecturer.py:157` |

### A.student. `student`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **GET** `/api/v1/student/profile` | STUDENT / ADMIN | Không | `StudentProfileDetailOut` — Hồ sơ cá nhân sinh viên | status.HTTP_404_NOT_FOUND: 'Không tìm thấy hồ sơ sinh viên' | `apps/backend/api/v1/endpoints/student.py:41` |
| **GET** `/api/v1/student/courses` | STUDENT / ADMIN | Không | `List[StudentCourseItemOut]` — Danh sách môn học đang theo học | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/student.py:69` |
| **GET** `/api/v1/student/courses/{enrollment_id}/risk-prediction` | STUDENT / ADMIN | `enrollment_id: uuid.UUID` (bắt buộc) | `RiskPredictionOut` — Dự báo rủi ro học tập môn học tại Cutoff 75% | status.HTTP_404_NOT_FOUND: 'Không tìm thấy hồ sơ sinh viên'<br>status.HTTP_404_NOT_FOUND: 'Chưa có dữ liệu dự báo cho học phần này hoặc bạn không có quyền xem' | `apps/backend/api/v1/endpoints/student.py:80` |
| **GET** `/api/v1/student/courses/{enrollment_id}/radar` | STUDENT / ADMIN | `enrollment_id: uuid.UUID` (bắt buộc) | `RadarDataOut` — Biểu đồ Radar Năng lực 6D đối sánh Benchmark Top 25% | status.HTTP_404_NOT_FOUND: 'Không tìm thấy hồ sơ sinh viên'<br>status.HTTP_404_NOT_FOUND: 'Không tìm thấy học phần này' | `apps/backend/api/v1/endpoints/student.py:99` |
| **GET** `/api/v1/student/tasks` | STUDENT / ADMIN | Không | `List[StudentTaskItemOut]` — Danh sách nhiệm vụ can thiệp sư phạm cần làm | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/student.py:153` |
| **GET** `/api/v1/student/intervention-plans` | STUDENT / ADMIN | `status_filter: Optional[str]` = `None` | `List[PlanOut]` — Danh sách kế hoạch can thiệp sư phạm của bản thân | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/student.py:164` |
| **PATCH** `/api/v1/student/tasks/{task_id}/complete` | STUDENT / ADMIN | `task_id: uuid.UUID` (bắt buộc)<br>`payload: TaskCompleteIn` (bắt buộc) | `StudentTaskItemOut` — Đánh dấu hoàn thành nhiệm vụ can thiệp | status.HTTP_404_NOT_FOUND: 'Không tìm thấy hồ sơ sinh viên'<br>status.HTTP_404_NOT_FOUND: 'Không tìm thấy nhiệm vụ can thiệp của bạn' | `apps/backend/api/v1/endpoints/student.py:176` |
| **GET** `/api/v1/student/help-requests` | STUDENT / ADMIN | Không | `List[HelpRequestOut]` — Danh sách các yêu cầu trợ giúp đã gửi | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/student.py:193` |
| **POST** `/api/v1/student/help-requests` | STUDENT / ADMIN | `payload: HelpRequestCreateIn` (bắt buộc) | `HelpRequestOut` — Tạo yêu cầu trợ giúp gửi GVCN hoặc GVBM | status.HTTP_404_NOT_FOUND: 'Không tìm thấy hồ sơ sinh viên' | `apps/backend/api/v1/endpoints/student.py:211` |

### A.health. `health`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **GET** `/api/v1/health` | Public | Không | `—` — health_check | Theo dependency/validation/nghiệp vụ | `apps/backend/api/v1/endpoints/health.py:7` |

### A.predictions. `predictions`

| Method/path | Quyền | Tham số và body | Response / tác dụng | Lỗi trực tiếp | Nguồn |
| --- | --- | --- | --- | --- | --- |
| **POST** `/api/v1/predictions/` | Public | `data: PredictionRequest` (bắt buộc) | `PredictionResponse` — Dự đoán bằng Machine Learning | 503: 'Model chưa sẵn sàng'<br>422: f'Dữ liệu đầu vào không hợp lệ: {exc}' | `apps/backend/api/v1/endpoints/predictions.py:17` |

Tổng số: **52 operation dưới /api/v1**, cộng GET `/` là **53 operation ứng dụng**. Các route docs/static được mô tả riêng.

## Phụ lục B. Từ điển request/response schema

Các bảng sau trích nguyên kiểu annotation và biểu thức default/Field; `Field(...)` là bắt buộc, `Field(None, ...)` là tùy chọn. `Optional` biểu thị nhận null, không luôn đồng nghĩa field được bỏ qua nếu không có default. Các validator bổ sung được ghi dưới từng schema; ý nghĩa nghiệp vụ xem mục 4–8.

### B. Module `admin.py`

#### `AdminUserCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `email` | `EmailStr` | `—` — bắt buộc |
| `password` | `str` | `Field(..., min_length=6)` |
| `full_name` | `str` | `—` — bắt buộc |
| `phone_number` | `Optional[str]` | `None` |
| `role_codes` | `List[str]` | `Field(..., description="Ví dụ: ['ADMIN'] hoặc ['ADVISOR'] hoặc ['LECTURER'] hoặc ['STUDENT']")` |
| `student_code` | `Optional[str]` | `None` |
| `gender` | `Optional[str]` | `'M'` |
| `highest_education` | `Optional[str]` | `'HE Qualification'` |
| `age_band` | `Optional[str]` | `'0-35'` |
| `department` | `Optional[str]` | `'Khoa CNTT'` |
| `lecturer_code` | `Optional[str]` | `None` |

#### `UserStatusUpdateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `is_active` | `bool` | `—` — bắt buộc |

#### `AdminPasswordResetIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `new_password` | `SecretStr` | `Field(..., min_length=6, max_length=72)` |

Cấu hình: `ConfigDict(extra='forbid')`.

Validator `validate_password`:

```python
@field_validator('new_password')
@classmethod
def validate_password(cls, value: SecretStr):
    password = value.get_secret_value()
    if not password.strip():
        raise ValueError('Mật khẩu không được chỉ chứa khoảng trắng')
    if len(password.encode('utf-8')) > 72:
        raise ValueError('Mật khẩu không được vượt quá 72 byte UTF-8')
    return value
```

#### `AdminPasswordResetOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `message` | `str` | `—` — bắt buộc |
| `user_id` | `uuid.UUID` | `—` — bắt buộc |

#### `AdminUserUpdateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `email` | `Optional[EmailStr]` | `None` |
| `full_name` | `Optional[str]` | `Field(None, min_length=1, max_length=150)` |
| `phone_number` | `Optional[str]` | `Field(None, max_length=20)` |
| `student_code` | `Optional[str]` | `Field(None, min_length=1, max_length=50)` |
| `lecturer_code` | `Optional[str]` | `Field(None, min_length=1, max_length=50)` |
| `department` | `Optional[str]` | `Field(None, min_length=1, max_length=150)` |
| `academic_rank` | `Optional[str]` | `Field(None, min_length=1, max_length=50)` |
| `office_location` | `Optional[str]` | `Field(None, max_length=100)` |

Cấu hình: `ConfigDict(extra='forbid')`.

Validator `nonempty`:

```python
@field_validator('email', 'full_name', 'student_code', 'lecturer_code', 'department', 'academic_rank', mode='before')
@classmethod
def nonempty(cls, value):
    if value is None or not str(value).strip():
        raise ValueError('Trường này không được để trống')
    return str(value).strip()
```

#### `UserRolesUpdateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `role_codes` | `List[str]` | `—` — bắt buộc |

#### `CourseCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `code_module` | `str` | `—` — bắt buộc |
| `name` | `str` | `—` — bắt buộc |
| `credits_default` | `int` | `30` |
| `description` | `Optional[str]` | `None` |

#### `CoursePresentationCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `course_id` | `uuid.UUID` | `—` — bắt buộc |
| `code_presentation` | `str` | `—` — bắt buộc |
| `module_presentation_length` | `int` | `268` |
| `start_date` | `Optional[date]` | `None` |

#### `AssignAdvisorIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `advisor_id` | `uuid.UUID` | `—` — bắt buộc |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `academic_year` | `str` | `'2026-2027'` |
| `class_name` | `str` | `—` — bắt buộc |

#### `AssignLecturerIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `lecturer_id` | `uuid.UUID` | `—` — bắt buộc |
| `presentation_id` | `uuid.UUID` | `—` — bắt buộc |
| `role_in_course` | `str` | `'GIANG_VIEN_CHINH'` |

#### `MLModelOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `model_name` | `str` | `—` — bắt buộc |
| `version` | `str` | `—` — bắt buộc |
| `threshold` | `float` | `—` — bắt buộc |
| `cutoff_fraction` | `float` | `—` — bắt buộc |
| `accuracy` | `Optional[float]` | `None` |
| `roc_auc` | `Optional[float]` | `None` |
| `is_active` | `bool` | `—` — bắt buộc |
| `created_at` | `datetime` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `ActivateModelIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `model_id` | `uuid.UUID` | `—` — bắt buộc |

#### `BatchPredictResultOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `total_snapshots_scanned` | `int` | `—` — bắt buộc |
| `predictions_generated` | `int` | `—` — bắt buộc |
| `high_risk_count` | `int` | `—` — bắt buộc |
| `safe_count` | `int` | `—` — bắt buộc |
| `execution_time_ms` | `int` | `—` — bắt buộc |

#### `AuditLogOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `user_id` | `Optional[uuid.UUID]` | `None` |
| `user_full_name` | `Optional[str]` | `None` |
| `user_email` | `Optional[str]` | `None` |
| `action` | `str` | `—` — bắt buộc |
| `target_type` | `Optional[str]` | `None` |
| `target_id` | `Optional[uuid.UUID]` | `None` |
| `detail` | `Optional[str]` | `None` |
| `ip_address` | `Optional[str]` | `None` |
| `created_at` | `datetime` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

### B. Module `advisor_lecturer.py`

#### `ClassOverviewOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `class_name` | `str` | `—` — bắt buộc |
| `academic_year` | `str` | `—` — bắt buộc |
| `total_students` | `int` | `—` — bắt buộc |
| `high_risk_count` | `int` | `—` — bắt buộc |
| `safe_count` | `int` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `AdvisorStudentSummaryOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `gender` | `str` | `—` — bắt buộc |
| `class_name` | `str` | `—` — bắt buộc |
| `risk_probability` | `Optional[float]` | `0.0` |
| `risk_level` | `str` | `'SAFE'` |
| `has_active_plan` | `bool` | `False` |
| `uncompleted_tasks_count` | `int` | `0` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `TaskCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `category` | `str` | `Field(..., description='CHUYEN_CAN, HOC_THUAT, TIEN_DO, TAM_LY')` |
| `priority` | `str` | `Field('MEDIUM', description='LOW, MEDIUM, HIGH, URGENT')` |
| `title` | `str` | `—` — bắt buộc |
| `description` | `str` | `—` — bắt buộc |
| `target_metric` | `str` | `'Tăng lượt tương tác / Hoàn thành bài tập'` |

#### `TaskOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `plan_id` | `uuid.UUID` | `—` — bắt buộc |
| `category` | `str` | `—` — bắt buộc |
| `priority` | `str` | `—` — bắt buộc |
| `title` | `str` | `—` — bắt buộc |
| `description` | `str` | `—` — bắt buộc |
| `target_metric` | `str` | `—` — bắt buộc |
| `is_completed` | `bool` | `—` — bắt buộc |
| `completed_at` | `Optional[datetime]` | `None` |
| `student_feedback` | `Optional[str]` | `None` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `PlanCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `target_completion_date` | `Optional[date]` | `None` |
| `advisor_note_summary` | `Optional[str]` | `None` |
| `tasks` | `List[TaskCreateIn]` | `[]` |

#### `PlanOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `prediction_run_id` | `uuid.UUID` | `—` — bắt buộc |
| `status` | `str` | `—` — bắt buộc |
| `target_completion_date` | `Optional[date]` | `None` |
| `advisor_note_summary` | `Optional[str]` | `None` |
| `created_at` | `datetime` | `—` — bắt buộc |
| `tasks` | `List[TaskOut]` | `[]` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `NoteCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `meeting_date` | `date` | `—` — bắt buộc |
| `meeting_type` | `str` | `'ONLINE'` |
| `content` | `str` | `—` — bắt buộc |
| `agreed_actions` | `Optional[str]` | `None` |

#### `NoteOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `advisor_id` | `uuid.UUID` | `—` — bắt buộc |
| `meeting_date` | `date` | `—` — bắt buộc |
| `meeting_type` | `str` | `—` — bắt buộc |
| `content` | `str` | `—` — bắt buộc |
| `agreed_actions` | `Optional[str]` | `None` |
| `created_at` | `datetime` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `ClassStatisticsOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `class_name` | `str` | `—` — bắt buộc |
| `academic_year` | `Optional[str]` | `None` |
| `total_students` | `int` | `—` — bắt buộc |
| `high_risk_count` | `int` | `—` — bắt buộc |
| `safe_count` | `int` | `—` — bắt buộc |
| `avg_risk_probability` | `float` | `0.0` |
| `students_with_active_plan` | `int` | `0` |
| `outstanding_tasks` | `int` | `0` |

#### `PlanUpdateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `status` | `Optional[str]` | `Field(None, description='ACTIVE, COMPLETED, CANCELLED')` |
| `target_completion_date` | `Optional[date]` | `None` |
| `advisor_note_summary` | `Optional[str]` | `None` |

#### `StudentOverviewOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `email` | `str` | `—` — bắt buộc |
| `gender` | `str` | `—` — bắt buộc |
| `class_name` | `Optional[str]` | `None` |
| `highest_education` | `Optional[str]` | `None` |
| `age_band` | `Optional[str]` | `None` |
| `courses` | `List[Dict[str, Any]]` | `[]` |
| `latest_risk_probability` | `float` | `0.0` |
| `latest_risk_level` | `str` | `'SAFE'` |
| `latest_model_version` | `Optional[str]` | `None` |
| `active_plan` | `Optional[PlanOut]` | `None` |
| `notes_count` | `int` | `0` |
| `help_requests_count` | `int` | `0` |

#### `LecturerCourseOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `presentation_id` | `uuid.UUID` | `—` — bắt buộc |
| `code_module` | `str` | `—` — bắt buộc |
| `course_name` | `str` | `—` — bắt buộc |
| `code_presentation` | `str` | `—` — bắt buộc |
| `module_length` | `int` | `—` — bắt buộc |
| `role_in_course` | `str` | `—` — bắt buộc |
| `total_students` | `int` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `StudentRiskInCourseOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `total_clicks` | `int` | `0` |
| `late_submissions` | `int` | `0` |
| `submission_rate` | `float` | `0.0` |
| `risk_probability` | `float` | `0.0` |
| `risk_status` | `str` | `'SAFE'` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `CourseTaskAssignIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `title` | `str` | `—` — bắt buộc |
| `description` | `str` | `—` — bắt buộc |
| `priority` | `str` | `'HIGH'` |
| `target_metric` | `str` | `'Hoàn thành bài tập ôn tập môn học'` |

#### `CourseStudentOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `gender` | `str` | `'M'` |
| `final_result` | `Optional[str]` | `None` |
| `total_clicks` | `int` | `0` |
| `late_submissions` | `int` | `0` |
| `submission_rate` | `float` | `0.0` |
| `risk_probability` | `float` | `0.0` |
| `risk_status` | `str` | `'SAFE'` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `AssessmentUpdateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `assessments_submitted` | `Optional[int]` | `Field(None, ge=0)` |
| `late_submissions` | `Optional[int]` | `Field(None, ge=0)` |
| `submission_rate` | `Optional[float]` | `Field(None, ge=0.0, le=1.0)` |
| `final_result` | `Optional[str]` | `Field(None, description='PASS, FAIL, WITHDRAWN, DISTINCTION')` |

#### `AlertAdvisorIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `subject` | `str` | `'Cảnh báo học tập bất thường môn học'` |
| `content` | `str` | `—` — bắt buộc |

### B. Module `auth.py`

#### `LoginRequest`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `username` | `Optional[str]` | `Field(None, min_length=1, max_length=255)` |
| `email` | `Optional[EmailStr]` | `None` |
| `password` | `str` | `Field(..., min_length=1, example='123')` |

Validator `validate_identifier`:

```python
@model_validator(mode='after')
def validate_identifier(self):
    if self.username is not None:
        self.username = self.username.strip()
    if not self.username and (not self.email):
        raise ValueError('Vui lòng nhập mã số sinh viên hoặc email')
    if self.username and self.email:
        raise ValueError('Chỉ gửi một tên đăng nhập')
    return self
```

#### `TokenResponse`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `access_token` | `str` | `—` — bắt buộc |
| `refresh_token` | `str` | `—` — bắt buộc |
| `token_type` | `str` | `'bearer'` |
| `expires_in` | `int` | `—` — bắt buộc |

#### `RefreshRequest`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `refresh_token` | `str` | `—` — bắt buộc |

#### `RoleOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `int` | `—` — bắt buộc |
| `code` | `str` | `—` — bắt buộc |
| `name` | `str` | `—` — bắt buộc |

#### `StudentProfileOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `gender` | `str` | `—` — bắt buộc |
| `highest_education` | `str` | `—` — bắt buộc |
| `age_band` | `str` | `—` — bắt buộc |
| `imd_band` | `Optional[str]` | `None` |
| `region` | `Optional[str]` | `None` |
| `disability` | `str` | `—` — bắt buộc |

#### `AdvisorProfileOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `department` | `str` | `—` — bắt buộc |
| `office_location` | `Optional[str]` | `None` |

#### `LecturerProfileOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `lecturer_code` | `str` | `—` — bắt buộc |
| `department` | `str` | `—` — bắt buộc |
| `academic_rank` | `str` | `—` — bắt buộc |

#### `UserOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `email` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `avatar_url` | `Optional[str]` | `None` |
| `phone_number` | `Optional[str]` | `None` |
| `is_active` | `bool` | `—` — bắt buộc |
| `roles` | `List[RoleOut]` | `[]` |
| `student_profile` | `Optional[StudentProfileOut]` | `None` |
| `advisor_profile` | `Optional[AdvisorProfileOut]` | `None` |
| `lecturer_profile` | `Optional[LecturerProfileOut]` | `None` |
| `created_at` | `datetime` | `—` — bắt buộc |

#### `UserUpdateProfile`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `full_name` | `Optional[str]` | `None` |
| `phone_number` | `Optional[str]` | `None` |
| `avatar_url` | `Optional[str]` | `None` |

#### `ChangePasswordRequest`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `old_password` | `str` | `—` — bắt buộc |
| `new_password` | `str` | `Field(..., min_length=6)` |

### B. Module `prediction.py`

#### `StudentFeatures`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `code_module` | `str` | `Field(examples=['AAA'])` |
| `gender` | `str` | `Field(examples=['M'])` |
| `highest_education` | `str` | `Field(examples=['A Level or Equivalent'])` |
| `age_band` | `str` | `Field(examples=['18-23'])` |
| `studied_credits` | `float` | `Field(examples=[60.0])` |
| `date_registration` | `float` | `Field(examples=[-10.0])` |
| `total_clicks_to_t` | `float` | `Field(examples=[1500.0])` |
| `clicks_resource_to_t` | `float` | `Field(examples=[400.0])` |
| `clicks_url_to_t` | `float` | `Field(examples=[200.0])` |
| `active_days_to_t` | `float` | `Field(examples=[45.0])` |
| `assessments_submitted_to_t` | `float` | `Field(examples=[5.0])` |
| `late_submissions_to_t` | `float` | `Field(examples=[1.0])` |
| `active_day_ratio` | `float` | `Field(examples=[0.5])` |
| `submission_rate` | `float` | `Field(examples=[0.6])` |
| `days_since_last_activity` | `float` | `Field(examples=[3.0])` |
| `clicks_recent_7` | `float` | `Field(examples=[80.0])` |
| `clicks_recent_30` | `float` | `Field(examples=[350.0])` |

#### `PredictionRequest`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `features` | `StudentFeatures` | `—` — bắt buộc |

#### `PredictionResponse`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `prediction` | `Any` | `—` — bắt buộc |
| `confidence` | `float \| None` | `None` |

### B. Module `student.py`

#### `StudentProfileDetailOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `student_code` | `str` | `—` — bắt buộc |
| `full_name` | `str` | `—` — bắt buộc |
| `email` | `str` | `—` — bắt buộc |
| `gender` | `str` | `—` — bắt buộc |
| `highest_education` | `str` | `—` — bắt buộc |
| `age_band` | `str` | `—` — bắt buộc |
| `imd_band` | `Optional[str]` | `None` |
| `region` | `Optional[str]` | `None` |
| `disability` | `str` | `—` — bắt buộc |
| `studied_credits_total` | `int` | `0` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `StudentCourseItemOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `code_module` | `str` | `—` — bắt buộc |
| `course_name` | `str` | `—` — bắt buộc |
| `code_presentation` | `str` | `—` — bắt buộc |
| `studied_credits` | `int` | `—` — bắt buộc |
| `final_result` | `Optional[str]` | `None` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `RiskPredictionOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `code_module` | `str` | `—` — bắt buộc |
| `cutoff_stage` | `str` | `—` — bắt buộc |
| `risk_probability` | `float` | `—` — bắt buộc |
| `risk_level` | `str` | `—` — bắt buộc |
| `model_version` | `str` | `—` — bắt buộc |
| `predicted_at` | `datetime` | `—` — bắt buộc |
| `pedagogical_recommendations` | `List[str]` | `[]` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `RadarDimension`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `metric` | `str` | `—` — bắt buộc |
| `student_value` | `float` | `—` — bắt buộc |
| `benchmark_value` | `float` | `—` — bắt buộc |
| `percentile` | `float` | `—` — bắt buộc |

#### `RadarDataOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `enrollment_id` | `uuid.UUID` | `—` — bắt buộc |
| `code_module` | `str` | `—` — bắt buộc |
| `dimensions` | `List[RadarDimension]` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `StudentTaskItemOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `plan_id` | `uuid.UUID` | `—` — bắt buộc |
| `category` | `str` | `—` — bắt buộc |
| `priority` | `str` | `—` — bắt buộc |
| `title` | `str` | `—` — bắt buộc |
| `description` | `str` | `—` — bắt buộc |
| `target_metric` | `str` | `—` — bắt buộc |
| `is_completed` | `bool` | `—` — bắt buộc |
| `completed_at` | `Optional[datetime]` | `None` |
| `student_feedback` | `Optional[str]` | `None` |

Cấu hình: `ConfigDict(from_attributes=True)`.

#### `TaskCompleteIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `student_feedback` | `Optional[str]` | `Field(None, description='Ghi chú phản hồi khi hoàn thành')` |

#### `HelpRequestCreateIn`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `target_role` | `str` | `Field(..., description='ADVISOR hoặc LECTURER')` |
| `presentation_id` | `Optional[uuid.UUID]` | `None` |
| `target_user_id` | `Optional[uuid.UUID]` | `None` |
| `subject` | `str` | `Field(..., min_length=3)` |
| `content` | `str` | `Field(..., min_length=5)` |

#### `HelpRequestOut`

| Field | Kiểu | Default / constraint |
| --- | --- | --- |
| `id` | `uuid.UUID` | `—` — bắt buộc |
| `target_role` | `str` | `—` — bắt buộc |
| `presentation_id` | `Optional[uuid.UUID]` | `None` |
| `target_user_id` | `Optional[uuid.UUID]` | `None` |
| `subject` | `str` | `—` — bắt buộc |
| `content` | `str` | `—` — bắt buộc |
| `status` | `str` | `—` — bắt buộc |
| `response_note` | `Optional[str]` | `None` |
| `created_at` | `datetime` | `—` — bắt buộc |
| `updated_at` | `datetime` | `—` — bắt buộc |

Cấu hình: `ConfigDict(from_attributes=True)`.

## Phụ lục C. Từ điển database đầy đủ theo SQL init

Khai báo dưới đây giữ nguyên cột, kiểu, nullability, default, FK và table constraint trong `../../docker/postgres/init-scripts/01_init_schema.sql`. Database thực tế có thể khác nếu volume đã được khởi tạo trước đó.

### C. `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    avatar_url VARCHAR(500),
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `roles`

```sql
CREATE TABLE IF NOT EXISTS roles (
    id SMALLSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);
```

### C. `user_roles`

```sql
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

### C. `student_profiles`

```sql
CREATE TABLE IF NOT EXISTS student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_code VARCHAR(50) UNIQUE NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('M', 'F')),
    highest_education VARCHAR(100) NOT NULL,
    age_band VARCHAR(20) NOT NULL CHECK (age_band IN ('0-35', '35-55', '55<=')),
    imd_band VARCHAR(50),
    region VARCHAR(100),
    disability VARCHAR(10) NOT NULL DEFAULT 'N'
);
```

### C. `advisor_profiles`

```sql
CREATE TABLE IF NOT EXISTS advisor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(150) NOT NULL,
    office_location VARCHAR(255),
    lms_api_key VARCHAR(255)
);
```

### C. `courses`

```sql
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_module VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    credits_default INT NOT NULL DEFAULT 30,
    description TEXT
);
```

### C. `course_presentations`

```sql
CREATE TABLE IF NOT EXISTS course_presentations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    code_presentation VARCHAR(20) NOT NULL,
    start_date DATE,
    module_presentation_length INT NOT NULL DEFAULT 260,
    CONSTRAINT uq_course_presentation UNIQUE (course_id, code_presentation)
);
```

### C. `student_enrollments`

```sql
CREATE TABLE IF NOT EXISTS student_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    presentation_id UUID NOT NULL REFERENCES course_presentations(id) ON DELETE CASCADE,
    date_registration INT NOT NULL DEFAULT -10,
    date_unregistration INT,
    studied_credits INT NOT NULL DEFAULT 60,
    num_of_prev_attempts INT NOT NULL DEFAULT 0,
    final_result VARCHAR(20),
    CONSTRAINT uq_student_presentation UNIQUE (student_id, presentation_id)
);
```

### C. `student_feature_snapshots`

```sql
CREATE TABLE IF NOT EXISTS student_feature_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES student_enrollments(id) ON DELETE CASCADE,
    cutoff_stage VARCHAR(30) NOT NULL DEFAULT 'CUTOFF_75',
    total_clicks_to_t INT NOT NULL DEFAULT 0,
    clicks_resource_to_t INT NOT NULL DEFAULT 0,
    clicks_url_to_t INT NOT NULL DEFAULT 0,
    active_days_to_t INT NOT NULL DEFAULT 0,
    active_day_ratio FLOAT NOT NULL DEFAULT 0.0,
    days_since_last_activity INT NOT NULL DEFAULT 0,
    clicks_recent_7 INT NOT NULL DEFAULT 0,
    clicks_recent_30 INT NOT NULL DEFAULT 0,
    assessments_submitted_to_t INT NOT NULL DEFAULT 0,
    late_submissions_to_t INT NOT NULL DEFAULT 0,
    submission_rate FLOAT NOT NULL DEFAULT 0.0,
    raw_features_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `ml_models`

```sql
CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(150) NOT NULL,
    version VARCHAR(30) UNIQUE NOT NULL,
    model_file_path VARCHAR(500) NOT NULL,
    threshold FLOAT NOT NULL DEFAULT 0.5,
    cutoff_fraction FLOAT NOT NULL DEFAULT 0.75,
    accuracy FLOAT,
    roc_auc FLOAT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `prediction_runs`

```sql
CREATE TABLE IF NOT EXISTS prediction_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID NOT NULL REFERENCES student_feature_snapshots(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE RESTRICT,
    prediction_label SMALLINT NOT NULL CHECK (prediction_label IN (0, 1)),
    risk_probability FLOAT NOT NULL,
    execution_time_ms INT,
    triggered_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `intervention_plans`

```sql
CREATE TABLE IF NOT EXISTS intervention_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_run_id UUID NOT NULL REFERENCES prediction_runs(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    target_completion_date DATE,
    advisor_note_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `intervention_tasks`

```sql
CREATE TABLE IF NOT EXISTS intervention_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES intervention_plans(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    target_metric VARCHAR(255) NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    student_feedback TEXT
);
```

### C. `advising_notes`

```sql
CREATE TABLE IF NOT EXISTS advising_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES student_enrollments(id) ON DELETE CASCADE,
    advisor_id UUID NOT NULL REFERENCES advisor_profiles(id) ON DELETE CASCADE,
    meeting_date DATE NOT NULL DEFAULT CURRENT_DATE,
    meeting_type VARCHAR(50) NOT NULL DEFAULT 'IN_PERSON',
    content TEXT NOT NULL,
    agreed_actions TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `lecturer_profiles`

```sql
CREATE TABLE IF NOT EXISTS lecturer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lecturer_code VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(150) NOT NULL,
    academic_rank VARCHAR(50) DEFAULT 'Giảng viên',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `course_lecturers`

```sql
CREATE TABLE IF NOT EXISTS course_lecturers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lecturer_id UUID NOT NULL REFERENCES lecturer_profiles(id) ON DELETE CASCADE,
    presentation_id UUID NOT NULL REFERENCES course_presentations(id) ON DELETE CASCADE,
    role_in_course VARCHAR(50) NOT NULL DEFAULT 'GIANG_VIEN_CHINH',
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_lecturer_presentation UNIQUE (lecturer_id, presentation_id)
);
```

### C. `advisor_students`

```sql
CREATE TABLE IF NOT EXISTS advisor_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_id UUID NOT NULL REFERENCES advisor_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    academic_year VARCHAR(20) NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_advisor_student UNIQUE (advisor_id, student_id)
);
```

### C. `student_help_requests`

```sql
CREATE TABLE IF NOT EXISTS student_help_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    target_role VARCHAR(20) NOT NULL CHECK (target_role IN ('ADVISOR', 'LECTURER')),
    target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    presentation_id UUID REFERENCES course_presentations(id) ON DELETE SET NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'RESOLVED')),
    response_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. `audit_logs`

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    detail TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### C. Index khai báo riêng

```sql
CREATE INDEX IF NOT EXISTS idx_student_profiles_code ON student_profiles(student_code);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON student_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_presentation ON student_enrollments(presentation_id);
CREATE INDEX IF NOT EXISTS idx_feature_snapshots_enrollment ON student_feature_snapshots(enrollment_id, cutoff_stage);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at_desc ON prediction_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_snapshot ON prediction_runs(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_intervention_plans_student ON intervention_plans(student_id, status);
CREATE INDEX IF NOT EXISTS idx_intervention_tasks_plan_status ON intervention_tasks(plan_id, is_completed);
```

UNIQUE/PRIMARY KEY còn tạo index tự động; danh sách trên chỉ gồm CREATE INDEX tường minh.

## Bổ sung ngày 16/10/2026: tải ảnh đại diện

`POST /api/v1/auth/profile/avatar` nhận `multipart/form-data` với field `file` và Bearer access token. Endpoint chỉ cập nhật tài khoản đang đăng nhập; response là UserOut với avatar_url mới. GET /auth/me trả lại URL này ở những phiên sau.

- Chấp nhận JPG/PNG/WebP tối đa 5 MiB và 20 megapixel; kiểm tra nội dung bằng Pillow, sửa hướng EXIF, cắt vuông 512×512, chuyển JPEG và loại metadata gốc.
- Ảnh lưu trong apps/backend/uploads/avatars; có thể đổi bằng biến môi trường AVATAR_UPLOAD_DIR (đường dẫn tương đối tính từ gốc repository).
- Ảnh được phục vụ qua /media/avatars/<uuid-file>.jpg. Khi đổi thư mục lưu, phải giữ dữ liệu ảnh tương ứng hoặc chuyển ảnh sang thư mục mới. Khi triển khai container cần volume bền vững cho thư mục ảnh.
- users.avatar_url lưu đường dẫn tương đối; frontend ghép với apiBase nên hoạt động khi Vite và backend khác origin.
- Lưu DB thất bại: rollback và xóa tệp mới. Sau khi commit thành công: dọn ảnh cũ do hệ thống sinh cho chính user đó; không xóa URL ngoài hoặc ảnh người khác.
- Thêm dependency python-multipart và Pillow trong requirements.txt; ảnh tải lên được bỏ qua bởi Git.

Đã chạy 13 kiểm thử avatar, bao gồm PostgreSQL/JWT thật với tài khoản fixture trong outer transaction được rollback và thư mục ảnh tạm. Frontend build thành công. Không thay đổi avatar của tài khoản người dùng thực trong quá trình kiểm thử.

## Bổ sung ngày 16/10/2026: nhắc nhở môn học

GET /api/v1/student/reminders dùng Bearer token, vai trò STUDENT hoặc ADMIN và hồ sơ sinh viên của chính người gọi. Endpoint không nhận student_id từ client, không tạo dữ liệu mẫu và không cần migration.

Thông báo được tính từ task chưa hoàn thành thuộc plan ACTIVE, join plan → prediction → snapshot → enrollment → presentation/course. Cả student_id trên plan và enrollment đều phải khớp sinh viên. Kết quả gộp theo enrollment, đếm task duy nhất và chọn hạn kế hoạch gần nhất trong các task còn lại. Ngày hiện tại dùng múi giờ Việt Nam (UTC+7).

- overdue/danger: hạn đã qua.
- due_soon/warning: đến hạn hôm nay hoặc trong 3 ngày tới.
- pending/info: còn nhiệm vụ nhưng chưa gần hạn, hoặc chưa có hạn.
- Task đã hoàn thành và plan không ACTIVE không sinh nhắc nhở.
- ID xác định từ enrollment, hạn, mức nhắc nhở và tập task; thay đổi nhiệm vụ/hạn/mức khẩn cấp tạo ID mới để có thể hiện lại là chưa đọc.

Response gồm id, enrollment_id, code_module, course_name, code_presentation, title, message, pending_tasks, due_date, days_remaining, state và level. Danh sách ưu tiên quá hạn trước, rồi sắp đến hạn, rồi pending. Trạng thái đã đọc nằm trong localStorage riêng từng tài khoản/trình duyệt, không đồng bộ nhiều thiết bị.

Đã chạy 10 kiểm thử quy tắc/API giả lập và 1 kiểm thử PostgreSQL về quyền sở hữu/task hoàn thành với fixture rollback. Backend đang chạy trả HTTP 200 cho tài khoản 2045230069: AAA có 12 task chưa hoàn thành, hạn kế hoạch gần nhất 14/10/2026, quá hạn 2 ngày tại thời điểm kiểm tra 16/10; request không token trả 401. Frontend build thành công. Chưa có push khi đóng trang, email, SMS hoặc scheduler gửi thông báo ngoài ứng dụng.


## Kiểm thử PostgreSQL và Docker — công việc 5, ngày 18/10/2026

Dùng Python 3.12 và cài manifest nhỏ dành riêng backend:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r apps/backend/requirements-dev.txt
.venv/Scripts/python.exe scripts/run_backend_tests.py -q --junitxml=reports/test-results/task5-backend.xml
npm --prefix apps/frontend ci
npm --prefix apps/frontend test
npm --prefix apps/frontend run build
```

Chạy lệnh từ gốc repository. Runner dùng DATABASE_URL trong .env để kết nối server, tạo database có tên gốc + `_test`, khởi tạo schema/seed/trigger, rồi truyền TEST_DATABASE_URL cho pytest. Có thể chọn database riêng bằng TEST_DATABASE_URL, nhưng tên phải kết thúc `_test` và khác database ứng dụng. User PostgreSQL cần CREATEDB khi database chưa tồn tại. Runner không drop database; so sánh số dòng và hash nội dung của cả 19 bảng trước/sau để phát hiện fixture chưa rollback. Sequence có thể tăng dù transaction rollback. Fixture dùng outer transaction và savepoint kể cả khi endpoint gọi commit. Chạy pytest trực tiếp không cấu hình TEST_DATABASE_URL sẽ chặn kết nối database; các test tích hợp bỏ qua nếu chưa opt-in.

Runtime được pin cùng scikit-learn 1.6.0, LightGBM 4.7.0, numpy 1.26.4, pandas 2.2.3. SQLAlchemy phải cài extra `[asyncio]` để có greenlet; lỗi thiếu greenlet đã được phát hiện bằng image cài sạch và sửa.

Chạy stack phát triển hiện tại: cấu hình .env từ .env.example, SECRET_KEY riêng và DOCKER_DATABASE_URL khớp POSTGRES_USER/PASSWORD/DB, rồi `docker compose up --build -d`. Frontend dùng nginx port 3000, proxy `/api/` và `/media/` tới backend. Archive model và avatar có volume riêng. Init SQL chỉ tự chạy khi volume PostgreSQL mới; database đang có vẫn cần script nâng cấp phù hợp. Không xóa volume đang dùng để áp dụng schema.

Stack kiểm thử riêng (không dùng volume/container của hệ thống hiện tại):

```powershell
# Tạo file .cache/task5-docker.env, chỉ chứa hai giá trị ngẫu nhiên:
# VERIFY_DB_PASSWORD=<chuỗi hex riêng>
# VERIFY_SECRET_KEY=<chuỗi ngẫu nhiên riêng>
docker compose --env-file .cache/task5-docker.env -p edurisk-verification -f docker-compose.verify.yml up --build -d
.venv/Scripts/python.exe scripts/verify_stack.py
# Khi xong, dừng stack riêng và giữ lại volume:
docker compose --env-file .cache/task5-docker.env -p edurisk-verification -f docker-compose.verify.yml stop
```

Truy cập http://127.0.0.1:13000. Stack riêng đặt access token 1 phút để kiểm tra refresh; cấu hình ứng dụng chính không đổi. Seed admin của database tạo mới là admin@huit.edu.vn / admin (chỉ dùng thử local). HTTP smoke tạo thêm một tài khoản fixture cho kiểm tra đổi tài khoản. Không dùng script này trỏ vào server vận hành.

Frontend dùng chung authenticatedFetch cho toàn bộ request có xác thực, refresh một lần khi 401 và gom request đồng thời; không refresh khi chỉ bị 403 trên bản ghi. Refresh bị 401/403 sẽ kết thúc phiên; lỗi mạng/5xx giữ token để thử lại. Request cũ bị hủy khi đổi tài khoản, refresh đến muộn không khôi phục phiên đã logout. Lịch sử lưu theo API base và UUID user, không nhập lịch sử dùng chung v2 vào tài khoản mới. Logout xóa dữ liệu đang hiển thị nhưng giữ lịch sử riêng của từng tài khoản trên trình duyệt.

Bằng chứng và giới hạn chi tiết: reports/dailys/18-10-2026.md, mục 6. Không coi test workflow này là bằng chứng đánh giá hiệu quả cá nhân hóa hoặc migration đã hoàn thành.
