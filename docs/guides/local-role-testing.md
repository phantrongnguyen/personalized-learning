# Kiểm thử giao diện sinh viên và giảng viên trên máy local

## Địa chỉ và dữ liệu hiện có

- Giao diện Vite (code mới nhất đang chạy): **http://127.0.0.1:5173/**.
- Swagger API: http://127.0.0.1:8000/docs; health: http://127.0.0.1:8000/api/v1/health.
- PostgreSQL trong Docker: container `kltn13_postgres`, cổng host 5433. Backend `/app/` có thể là bản `dist` cũ; khi thử thay đổi frontend hãy dùng cổng 5173.
- Database local hiện chỉ có admin `admin@huit.edu.vn` / `admin` (tài khoản seed phát triển). **Chưa có** tài khoản sinh viên/giảng viên, enrollment, phân công học phần hay plan để thử hai vai trò ngay. Đổi mật khẩu admin trước khi dùng ngoài môi trường local. Không dùng dữ liệu giả lập để báo cáo hiệu quả model.

## Kịch bản demo có gắn nhãn GIẢ LẬP

1. Trên trang đăng nhập, chọn **Giảng viên / Cố vấn / Quản trị viên** và đăng nhập admin. Trong **Quản lý tài khoản → Cấp tài khoản**, tạo hai tài khoản riêng, mật khẩu tự đặt: `demo.student@huit.edu.vn` (vai trò **Sinh viên**, mã **2045230068**) và `demo.lecturer@huit.edu.vn` (vai trò **Giảng viên**, mã **GVDEMO01**, điền Khoa/Bộ môn). Không dùng chung tài khoản cho hai vai trò.
2. **Chỉ trên database local sau khi đã xác nhận đúng container**, chạy script `database/demo_student_2045230068.sql` bằng lệnh dưới đây. Script tạo học phần `AAA / DEMO2045230068`, lượt học, snapshot, dự báo **GIẢ LẬP 0,82** và plan/task **GIẢ LẬP** sau khi hồ sơ sinh viên trên tồn tại. Nó không suy luận từ LightGBM và không ghi đè artifact app.
3. Gán giảng viên vừa tạo vào đúng học phần demo bằng SQL bên dưới. Đây là phân công trong database local để quyền lecturer có thể thấy lớp; không phải thao tác triển khai production.
4. Đăng xuất. Chọn loại tài khoản **Sinh viên**, đăng nhập bằng **MSSV 2045230068** và mật khẩu đã đặt (không dùng email). Mở **Không gian học tập**, chọn `AAA / DEMO2045230068`, xem dự báo/radar và nhiệm vụ `[DEMO]`. Các chỉ số này là dữ liệu giả, **không phải kết quả model thật**.
5. Đăng xuất. Chọn **Giảng viên / Cố vấn / Quản trị viên**, đăng nhập `demo.lecturer@huit.edu.vn`. Mở **Lớp học phần phụ trách**, chọn học phần demo và sinh viên, bấm **Xem gợi ý**. Snapshot demo thiếu metadata xác nhận nguồn và độ đầy đủ nên trạng thái dự kiến là **`insufficient_data`**; không tự sinh gợi ý có căn cứ. Có plan ACTIVE demo nên giảng viên có thể tự soạn nháp `[DEMO]`, chỉnh sửa rồi chủ động bấm **Giao**. Đăng nhập lại sinh viên để xem task; không xem nhiệm vụ demo là gợi ý đã xác minh từ LMS.
6. Để kiểm thử quy tắc G02/G03/G04 trên dữ liệu thực, cần pipeline nạp `support_evidence` có nguồn, thời điểm cutoff và xác nhận độ đầy đủ. **Không đặt giả** `activity_complete`/`assessments_complete` thành true để ép ra gợi ý. Khi thiếu plan ACTIVE hợp lệ, không thể giao task trong luồng giảng viên; advisor/admin cần tạo plan từ PredictionRun thật trước.

### Chạy seed demo (PowerShell tại gốc repo)

```powershell
$docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
& $docker ps --filter 'name=kltn13_postgres'
Get-Content -Raw .\database\demo_student_2045230068.sql |
  & $docker exec -i kltn13_postgres psql -v ON_ERROR_STOP=1 -U postgres -d personalized_learning_db
```

Sau khi tạo lecturer và chạy seed demo, chỉ trong cùng database local:

```powershell
$sql = @"
INSERT INTO course_lecturers (lecturer_id, presentation_id, role_in_course)
SELECT lp.id, cp.id, 'GIANG_VIEN_CHINH'
FROM lecturer_profiles lp
JOIN users u ON u.id = lp.user_id
CROSS JOIN course_presentations cp
WHERE u.email = 'demo.lecturer@huit.edu.vn'
  AND cp.code_presentation = 'DEMO2045230068'
  AND cp.course_id = (SELECT id FROM courses WHERE code_module = 'AAA')
ON CONFLICT (lecturer_id, presentation_id) DO NOTHING;
"@
$sql | & $docker exec -i kltn13_postgres psql -v ON_ERROR_STOP=1 -U postgres -d personalized_learning_db
```

Nếu không có hàng nào được thêm, kiểm tra lại email, hồ sơ lecturer và học phần demo; `ON CONFLICT DO NOTHING` cũng khiến việc chạy lại không tạo hàng trùng. Chưa chạy những lệnh thay đổi DB này thay bạn.

Nếu web chưa mở, khởi động Docker Desktop và làm theo [hướng dẫn chạy local](../../README.md#cài-đặt-và-chạy-local). Từ gốc repo, backend chạy với `cd apps/backend; ../../.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`; terminal khác chạy `cd apps/frontend; npm run dev -- --host 127.0.0.1`. Không xóa volume DB đang có. Kết quả model đã chốt và các hình phục vụ báo cáo nằm tại [MODEL_FINAL](../../reports/model_final/MODEL_FINAL.md), **không phải** dashboard sinh viên.
