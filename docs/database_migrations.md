# Migration database — 19/10/2026

Alembic dùng asyncpg theo [hướng dẫn chính thức](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic). Chạy từ gốc repository; URL lấy từ cấu hình `.env` hoặc `MIGRATION_DATABASE_URL`. Không đưa URL có mật khẩu vào Git/log.

## Các revision

- `0001_baseline`: SQL schema 19 bảng ngày 18/10 được đóng băng trong `apps/backend/migrations/sql`; bổ sung trigger provenance. Database trống được tạo bằng SQL này. Database đã có bảng được so sánh với manifest trước khi ghi version; không tự stamp schema không rõ nguồn gốc. Hỗ trợ thiếu cột provenance ở bản trước ngày 18/10 và đúng các index legacy đã được kiểm tra tại local. Khác biệt khác làm dừng transaction.
- `0002_normalize`: preflight dữ liệu, CHECK, FK giữ lịch sử, index, default, nullability và average precision. Không tự chọn model active hoặc sửa dữ liệu sai miền. Các UNIQUE đã có ở SQL cũ nay cũng được khai báo đúng trong ORM.

Revision không import model/schema contract hiện tại. Khi thay đổi tiếp theo, tạo revision mới; không sửa hai revision đã áp dụng. Metadata/check/default/index dùng chung nằm trong `models/schema_contract.py`; cập nhật ORM và revision rồi sinh lại SQL/tài liệu bằng `scripts/prepare_schema_contract.py`.

## Kiểm tra và nâng cấp

```powershell
.venv/Scripts/python.exe -m pip install -r apps/backend/requirements-dev.txt
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe scripts/verify_migrations.py
# Local Docker: tạo pg_dump, khôi phục sang DB _test và thử migration, chưa sửa DB nguồn.
.venv/Scripts/python.exe scripts/migrate_database.py --container kltn13_postgres
# Áp dụng sau khi kiểm tra bản khôi phục; script lặp lại backup/restore và khóa bảng trong transaction.
.venv/Scripts/python.exe scripts/migrate_database.py --container kltn13_postgres --apply
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe -m alembic check
.venv/Scripts/python.exe scripts/run_backend_tests.py -q
```

Helper backup chỉ hỗ trợ PostgreSQL Docker local và xác minh system identifier của container trùng server được cấu hình. Backup nằm ở `.cache/database-backups/` (Git ignore), chứa dữ liệu cá nhân/mật khẩu đã hash nên phải giữ ở nơi được bảo vệ. JSON bằng chứng chỉ lưu đường dẫn, SHA-256 và kết quả, không lưu nội dung bảng hoặc mật khẩu.

Với môi trường khác: tạo `pg_dump -Fc`, khôi phục thử bằng `pg_restore --exit-on-error --no-owner --no-privileges` vào database riêng, so sánh schema và dữ liệu rồi chạy `python -m alembic upgrade head` trên URL đích trong thời gian bảo trì. Role cần quyền ALTER/CREATE trên schema; CREATE EXTENSION/CREATE DATABASE chỉ cần cho khởi tạo và runner kiểm thử. Backend không tự chạy migration khi startup.

Docker volume mới chạy SQL canonical, seed, trigger và marker version qua `01`–`04`. Không chạy riêng `04_schema_version.sql` trên database cũ. Database trống nâng cấp bằng Alembic chỉ có schema/trigger, không tự thêm tài khoản demo; nếu cần dữ liệu minh họa, nạp `02_seed_data.sql` sau khi schema đã ở head. Seed không kích hoạt thêm một model khi đã có model active.

## Dữ liệu cũ không hợp lệ

Preflight báo tên bảng/cột và số bản ghi sai, bao gồm số âm, tỷ lệ ngoài miền, trạng thái sai, academic_rank NULL và nhiều model active. Toàn bộ thay đổi/schema/version rollback khi lỗi. Kiểm tra trên bản khôi phục, xác nhận giá trị với chủ dữ liệu, sửa có audit rồi thử lại; không clamp số, tự điền nhãn hay xóa dữ liệu để vượt ràng buộc. Không dùng `alembic stamp head` để bỏ qua preflight.

Giá trị seed ROC-AUC 0.8968 chỉ được sửa khi khớp đúng UUID, version và giá trị seed cũ: chuyển sang AP 0.8967566497124569, ROC-AUC NULL, lưu dấu nguồn/correction trong metadata. Các model khác không được suy đoán metric. Các tham chiếu này thuộc validation, không phải đánh giá test mới.

## Khôi phục

DDL và correction chạy trong một transaction có advisory lock và lock timeout 10 giây. Lỗi trước commit tự rollback. Helper `--apply` còn khóa 19 bảng, kiểm tra backup vẫn khớp và xác minh dữ liệu sau thay đổi trước commit; dùng thời gian bảo trì vì khóa sẽ chặn ghi/đọc tạm thời.

`alembic downgrade 0001_baseline` được kiểm thử để quay lại schema cũ và correction seed. Downgrade bỏ cột AP, bỏ các CHECK mới, khôi phục CASCADE và có thể mất metric mới thêm sau nâng cấp; chỉ dùng trên bản thử hoặc sau khi đã backup và đánh giá dữ liệu phát sinh. Các index legacy ngoài SQL gốc được chuẩn hóa, downgrade không tái tạo riêng từng biến thể index local. Downgrade xuống `base` bị chặn để không xóa dữ liệu.

Khi cần khôi phục đầy đủ: dừng ghi, giữ database lỗi để điều tra, khôi phục file dump đã xác minh vào **database mới**, kiểm tra checksum/schema/số dòng và cấu hình ứng dụng sang database đã phục hồi. Không tự động DROP/reset database ứng dụng. Sao lưu artifact archive cùng database để lịch sử dự báo còn replay được.

## Bằng chứng

- `reports/test-results/task1-migrations.json`: database trống, SQL canonical, clone dữ liệu, upgrade/downgrade/re-upgrade, schema drift, dữ liệu lỗi, active UNIQUE, miền metric và bảo vệ lịch sử.
- `reports/test-results/task1-migration-apply.json`: backup/restore, hash dump và revision áp dụng local.
- `reports/test-results/task1-backend.xml`: hồi quy backend và test truy vấn/phân trang; fixture rollback, runner kiểm tra hash nội dung 19 bảng cùng bảng version.

Các database thử có tên riêng và hậu tố `_test` được giữ để kiểm tra lại. Chưa có thử tải quy mô lớn; kết quả kiểm tra số query không đồng nghĩa cam kết thời gian đáp ứng production.
