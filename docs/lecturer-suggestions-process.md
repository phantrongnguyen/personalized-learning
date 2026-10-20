# Nhật ký triển khai gợi ý cho giảng viên

## Bước 1 - Khảo sát trước khi sửa

- Git: nhánh `nguyengiabao`; chỉ `notebooks/` và `outputs/` chưa được theo dõi. Không sửa/xóa hai thư mục này.
- Bốn README được theo dõi: README gốc, backend, frontend và docker. Chỉ cập nhật hai README đầu.
- Không có `.codegraph/`; đã kiểm tra API, models, repository, frontend, test liên quan và `gb:apps/backend/app/services/support.py` trực tiếp.
- Risk board hiện lấy snapshot mới nhất, prediction cùng snapshot, nhưng mặc định 0/SAFE khi thiếu prediction. API giao task chỉ nhận plan ACTIVE đúng sinh viên/học phần.
- Snapshot chỉ có chỉ số tổng hợp tại cutoff, JSON mở rộng tùy chọn; không có bảng chi tiết bài/hạn nộp, xác nhận log đầy đủ, hay ngày quan sát bắt buộc. `created_at` là ngày ghi DB, không phải ngày cutoff.
- Advisor/admin tạo plan cho enrollment có PredictionRun; lecturer không có quyền tạo. Không tạo plan/prediction giả.
- Tests: `test_course_scope.py` (PostgreSQL opt-in rollback), `test_sprint3.py`/`test_sprint4.py` (demo DB), `test_database_predictions.py`.

## Bước 2 - Quyết định thiết kế

- GET chỉ đọc theo học phần/sinh viên, kiểm tra quyền và enrollment. Tách dự báo model, quy tắc bằng chứng và trạng thái plan; ưu tiên do giảng viên tự chọn.
- Không coi `created_at` là ngày cutoff. Yêu cầu metadata xác nhận rõ ràng trước khi diễn giải cửa sổ hoạt động/tính đầy đủ của bài đánh giá.
- Không triển khai G01; G02 (nếu có xác nhận dữ liệu) chỉ mời kiểm tra số liệu tổng hợp, không định danh bài. G03/G04 là cửa sổ tại cutoff, không phải hiện tại.

## Bước 3 - Triển khai và kiểm chứng

1. Tạo `support_suggestions.py`: chỉ đọc snapshot CUTOFF_75; xác nhận ngày cutoff, nguồn, thời gian và hai cờ đầy đủ riêng. Không dùng ngày ghi DB làm ngày quan sát; lịch sử chỉ phản ánh cutoff.
2. Tạo GET có RBAC/ownership/enrollment; tách prediction và model metadata khỏi gợi ý quy tắc. Truy vấn plan ACTIVE cùng enrollment để UI biết có thể giao không. Không thêm phương thức ghi hoặc bảng mới.
3. Sửa risk-board/students: khi thiếu prediction cùng snapshot mới nhất hiển thị `NOT_PREDICTED`/null; khi thiếu snapshot, số liệu tổng hợp cũng null chứ không ngụ ý 0. G03/G04 chỉ dùng log đầy đủ và nhất quán; G02_AGGREGATE chỉ kiểm tra tổng hợp; không có G01/theo bài. Không tạo ngưỡng mức độ mới.
4. Frontend đọc căn cứ/giới hạn/phiên bản, chọn gợi ý thành nháp, giảng viên sửa title, mô tả, chỉ số mục tiêu, ưu tiên rồi bấm giao. Nếu thiếu plan thì không hiển thị form giao; hiển thị hướng dẫn cố vấn/admin. Khi đổi sinh viên/học phần, bỏ phản hồi GET cũ.
5. Tests: quy tắc đủ/thiếu dữ liệu, snapshot cũ, mốc 7/30, số liệu mâu thuẫn, ngưỡng model 0.5, RBAC chéo học phần và GET không ghi task. Cập nhật README gốc và backend; không sửa README frontend/docker.
6. Kiểm chứng cuối: pytest cần `-o asyncio_mode=auto` do fixture async sẵn có; build lần đầu báo nullable risk, đã sửa. Sau sửa: 18 unit tests (gồm database_predictions) đạt, 16 DB rollback opt-in đạt; frontend build đạt. Đã chạy lại sau thay đổi logic: 18 unit tests và 16 DB rollback tests đạt; `npm run build` đạt. Sau đó sửa nhãn UI và văn bản tài liệu, chạy lại frontend build thành công; không thay đổi quy tắc/API.

## Giới hạn và bàn giao

- Các snapshot hiện có không có metadata xác nhận: gợi ý sẽ trả `insufficient_data` mặc định, không dựng tín hiệu giả. Nguồn nhập phải kiểm tra log/assessment trước khi gắn cờ; API không tự kiểm toán log gốc.
- Không có dữ liệu bài/hạn nộp/gia hạn theo bài. GET không tạo plan; giảng viên chỉ giao được khi cố vấn/admin đã tạo plan ACTIVE hợp lệ dựa trên PredictionRun thật.
- Không chạy sprint demo tests có thể ghi dữ liệu demo; test scope dùng transaction rollback.
- Commit dự kiến: `feat: add evidence-gated lecturer suggestions and review flow`. Không push.


## Tệp thay đổi và commit

- Backend: `apps/backend/services/support_suggestions.py`, `apps/backend/api/v1/endpoints/lecturer.py`, `apps/backend/repositories/academic_repo.py`, `apps/backend/schemas/advisor_lecturer.py`.
- Tests: `apps/backend/tests/test_support_suggestions.py`, `apps/backend/tests/test_course_scope.py`.
- Frontend/contracts: `apps/frontend/src/pages/LecturerPage.tsx`, `apps/frontend/src/services/api.ts`, `packages/shared/types/index.ts`.
- Tài liệu: `README.md`, `apps/backend/README.md`, `docs/lecturer-suggestions-process.md`. Hai README còn lại giữ nguyên. Không chạm `notebooks/`, `outputs/`.
- Không có schema/migration. Cam kết: commit rõ nghĩa, không push.
