# Kiểm thử trình duyệt tích hợp — 21/10/2026

## Chạy bộ kiểm thử

Từ gốc repository, với dependency backend đã cài và PostgreSQL local đang chạy:

```powershell
npm --prefix apps/frontend ci
npm --prefix apps/frontend exec -- playwright install chromium
.venv/Scripts/python.exe scripts/run_browser_tests.py
```

Runner dùng database được cấu hình để kết nối tới **server PostgreSQL local**, nhưng luôn tạo database mới tên `e2e_<random>_test` cho dữ liệu kiểm thử. User PostgreSQL cần CREATEDB. Không truyền URL ứng dụng vào lệnh Playwright trực tiếp; config chỉ chạy với cờ, tên database và URL loopback do runner thiết lập.

Runner build React hiện tại, áp dụng Alembic/seed vào database riêng, khởi động FastAPI ở cổng loopback ngẫu nhiên và phục vụ frontend đã build tại `/app`. Nó đặt SECRET_KEY ngẫu nhiên và thư mục avatar riêng. Cuối cùng dừng backend và DROP đúng database vừa tạo, kể cả kiểm thử lỗi; không drop/reset database ứng dụng.

Playwright được pin `@playwright/test=1.64.1`; Chromium được cài từ công cụ chính thức. Không mock API ứng dụng hoặc thay JWT bằng localStorage giả: mọi vai trò đăng nhập qua form thật và gọi backend/DB thật. Việc chuẩn bị trạng thái bằng API được tách khỏi thao tác UI theo [hướng dẫn API testing](https://playwright.dev/docs/api-testing); quản lý server do runner Python đảm nhiệm thay vì `webServer` của [cấu hình Playwright](https://playwright.dev/docs/test-webserver).

## Ranh giới được kiểm chứng

| Bước | Cách chạy và xác minh |
| --- | --- |
| Tạo tài khoản sinh viên | Admin đăng nhập và điền modal cấp tài khoản trên browser |
| Tạo/phân công giảng viên, cố vấn, học phần | API thật để chuẩn bị fixture; không gọi đây là kiểm thử màn hình phân công |
| Enrollment và snapshot đầu vào | `e2e/import_fixture.py` ghi fixture vào database tạm có guard; hiện chưa có API/UI nhập enrollment/snapshot ban đầu |
| Thiếu metadata/plan | Giảng viên mở Xem gợi ý; kiểm tra thông báo thiếu căn cứ, thiếu plan, không có form giao |
| Rà soát snapshot | Browser chọn minh họa, kiểm tra checkbox mặc định false, nhập căn cứ, lưu và tải gợi ý thật |
| Dự báo | API admin batch chạy artifact thật trên snapshot đã rà soát; không mock xác suất/nhãn |
| Plan | Cố vấn đăng nhập, chọn enrollment, tạo plan và task đầu tiên qua UI |
| Giao task | Giảng viên chọn gợi ý, sửa title/description/priority/target rồi bấm giao qua UI |
| Hoàn thành và nhắc nhở | Sinh viên đăng nhập bằng MSSV, xem chuông thông báo, hoàn thành hai task qua UI; xác minh thông báo hết và thống kê API không còn task chờ |
| Phân quyền | Request tới học phần khác bị 403, học phần đó không xuất hiện trên UI; sinh viên không được đọc portal giảng viên |
| Đăng nhập sai | Form nhận 401 và vẫn ở màn hình xác thực |

Đây là **luồng tích hợp có trình duyệt, API chuẩn bị và bước nhập DB được công bố**, không phải tất cả bước đều qua UI. Không thêm màn hình nghiệp vụ mới chỉ để làm đầy kiểm thử. Test HTTP/DB đã có tiếp tục bao phủ các ràng buộc và biến thể sâu hơn.

## Bằng chứng và giới hạn

- `reports/test-results/browser/results.json`: kết quả theo test và từng `test.step`.
- `run.json`: base commit, checksum diff tracked, checksum manifest nguồn gồm cả tệp mới chưa commit, URL/database tạm, mã thoát và trạng thái dọn database.
- `environment.json`: phiên bản Node/Python/PostgreSQL/Playwright/Chromium được ghi nhận.
- `source-manifest.json`: hash từng tệp code/config liên quan; dùng cùng commit/diff để xác định checkout đang kiểm thử. Không đưa `.env` hoặc dữ liệu nguồn bị ignore vào manifest.
- `missing-evidence.png`, `student-tasks.png`, `completed.png`: ảnh browser thật trên fixture; trace/ảnh lỗi được giữ khi test thất bại, không báo retry là pass vì `retries=0`.
- Thư mục bằng chứng bị Git ignore. Trace chứa token/tài khoản **kiểm thử** nên không tự công bố toàn bộ trace; chỉ chia sẻ bằng chứng đã kiểm tra phù hợp.

Hiện chạy Chromium headless một worker. Chưa phải kiểm thử đa trình duyệt, tải/nhiều máy, kiểm chứng nguồn LMS thực hoặc đánh giá tác động học tập. Điều hướng sau reload đi qua sidebar vì app khôi phục phiên rồi mặc định trang chủ; test không giả định tự giữ màn hình nghiệp vụ. Các lỗi locator/điều hướng trong lúc xây test được sửa trước lượt xác nhận cuối.
