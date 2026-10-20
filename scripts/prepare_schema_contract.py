"""Generate canonical DDL and an ERD/data dictionary from reviewed metadata."""
from pathlib import Path
import sys
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from models import Base
from database_dictionary import TABLES, meaning
from database_design_sections import detailed_document


def single_unique(column):
    return any(isinstance(c, UniqueConstraint) and len(c.columns) == 1 and
               column.name in c.columns for c in column.table.constraints)


def column_keys(column, diagram=False):
    keys = []
    if column.primary_key:
        keys.append('PK' if diagram or len(column.table.primary_key.columns) == 1 else 'PK (ghép)')
    if column.foreign_keys:
        if diagram:
            keys.append('FK')
        else:
            for fk in column.foreign_keys:
                keys.append(f'FK → `{fk.target_fullname}` ({fk.ondelete})')
    if single_unique(column) and not column.primary_key:
        keys.append('UK' if diagram else 'UNIQUE')
    return (','.join(keys) if diagram else '; '.join(keys)) or ('' if diagram else '—')


def erd_relationship(fk):
    # Left: parents per child. Right: children per parent, including zero.
    left = '|o' if fk.parent.nullable else '||'
    right = 'o|' if single_unique(fk.parent) else 'o{'
    return f'    {fk.column.table.name} {left}--{right} {fk.parent.table.name} : "{fk.parent.name}"'


def erd_type(column, dialect):
    value = column.type.compile(dialect=dialect)
    return {'TIMESTAMP WITH TIME ZONE': 'TIMESTAMPTZ', 'DOUBLE PRECISION': 'FLOAT8'}.get(value, value.replace(' ', '_'))

if __name__ == '__main__':
    dialect = postgresql.dialect()
    tables = [Base.metadata.tables[name] for name in TABLES]
    if set(TABLES) != set(Base.metadata.tables):
        raise ValueError('Table dictionary and ORM table list differ')
    for table in tables:
        for column in table.columns:
            meaning(table.name, column.name)  # Fail before writing if a definition is missing.
    parts = ['-- Canonical schema; migrations are required for existing databases.',
             'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
             'CREATE EXTENSION IF NOT EXISTS "pgcrypto";']
    for table in Base.metadata.sorted_tables:
        # Metadata stores constraints in a set; fix ordering for reproducible DDL.
        table.constraints = sorted(table.constraints, key=lambda c: (
            type(c).__name__, str(c.name), ','.join(column.name for column in c.columns)))
        ddl = str(CreateTable(table, if_not_exists=True).compile(dialect=dialect))
        parts.append('\n'.join(line.rstrip() for line in ddl.splitlines()).strip() + ';')
    for table in Base.metadata.sorted_tables:
        for index in sorted(table.indexes, key=lambda i: i.name):
            parts.append(str(CreateIndex(index, if_not_exists=True).compile(dialect=dialect)) + ';')
    (ROOT / 'docker/postgres/init-scripts/01_init_schema.sql').write_text('\n\n'.join(parts) + '\n', encoding='utf-8')
    lines = ['# THIẾT KẾ CƠ SỞ DỮ LIỆU HỆ THỐNG', '',
        '**Cập nhật:** 19/10/2026 — PostgreSQL 15, SQLAlchemy async/asyncpg, Alembic `0002_normalize`.', '',
        '## 1. Phạm vi và nguồn chuẩn', '',
        'Hệ thống gồm **19 bảng nghiệp vụ** và bảng hạ tầng `alembic_version`. SQL khởi tạo và ORM đã được đối chiếu trên PostgreSQL, gồm kiểu/độ dài, nullability, default, PK, UNIQUE, CHECK, FK và index. Không có khác biệt được Alembic autogenerate phát hiện tại thời điểm xác minh.', '',
        '- [SQL khởi tạo](../docker/postgres/init-scripts/01_init_schema.sql) được sinh từ metadata ORM đã rà soát bằng `scripts/prepare_schema_contract.py`.',
        '- [ORM và ràng buộc dùng chung](../apps/backend/models/schema_contract.py) khai báo cả Python default và server default.',
        '- [Migration bất biến](../apps/backend/migrations/versions/) giữ SQL baseline ngày 18/10 và revision nâng cấp độc lập với model hiện tại.',
        '- [Hướng dẫn migration/khôi phục](../docs/database_migrations.md) mô tả baseline, backup, dữ liệu lỗi và vận hành.',
        '- [Bằng chứng migration](../reports/test-results/task1-migrations.json) và [áp dụng local](../reports/test-results/task1-migration-apply.json).', '',
        'UUID có server default `gen_random_uuid()`; các mốc tạo/sửa/phân công mặc định `now()`. `updated_at` được ORM cập nhật khi thay đổi, chưa có trigger cập nhật timestamp cho mọi câu SQL trực tiếp. Trigger provenance là thành phần bổ sung ngoài ORM: không dùng `Base.metadata.create_all()` thay cho Alembic.', '',
        '### 1.1. Quy ước đọc tài liệu', '',
        '- **PK:** khóa chính; **FK:** khóa ngoại; **UK/UNIQUE:** không trùng giá trị. PK ghép và UNIQUE ghép chỉ duy nhất theo cả tổ hợp, không có nghĩa từng cột riêng lẻ là duy nhất.',
        '- **NULL = Có:** được phép thiếu giá trị; dấu **—** ở mặc định nghĩa là không có server default, không phải giá trị NULL được tự tạo cho cột bắt buộc.',
        '- **UUID:** định danh; **VARCHAR(n):** chuỗi tối đa n ký tự; **TEXT:** văn bản; **INTEGER/SMALLINT:** số nguyên; **FLOAT:** số thực dấu phẩy động, PostgreSQL ánh xạ FLOAT không khai báo độ chính xác thành DOUBLE PRECISION; **BOOLEAN:** true/false.',
        '- **DATE:** ngày lịch; **TIMESTAMP WITH TIME ZONE / TIMESTAMPTZ:** thời điểm có xử lý múi giờ; **JSONB:** dữ liệu JSON có cấu trúc, không tự tạo FK cho các ID bên trong.',
        '- Mô tả ý nghĩa thuộc tính giải thích đơn vị, phạm vi và cách sử dụng; các CHECK bên dưới từng bảng mới là ràng buộc miền thực sự được database thực thi.', '',
        '### 1.2. Danh mục bảng và chức năng', '',
        '| Bảng | Tên nghiệp vụ | Chức năng |', '| --- | --- | --- |']
    for table in tables:
        title, purpose = TABLES[table.name]
        lines.append(f'| [`{table.name}`](#table-{table.name}) | {title} | {purpose} |')
    lines += ['| [`alembic_version`](#table-alembic_version) | Phiên bản schema | Bảng hạ tầng theo dõi revision Alembic, không chứa dữ liệu học tập. |', '',
        '## 2. Sơ đồ quan hệ và chính sách giữ lịch sử', '',
        '### 2.1. Sơ đồ thực thể–quan hệ (ERD)', '',
        'Sơ đồ thể hiện đủ thuộc tính của 19 bảng nghiệp vụ và bảng phiên bản schema. Kiểu có độ dài/miền và ý nghĩa chi tiết được trình bày tại mục 3. Nhãn trên cạnh là cột FK của bảng con.', '',
        'Ký hiệu: `||` = đúng một; `o|` hoặc `|o` = không hoặc một; `o{` = không hoặc nhiều. Mọi bảng cha có thể chưa có bản ghi con. Riêng hồ sơ có UNIQUE(user_id) nên một tài khoản có tối đa một hồ sơ của từng loại.', '', '```mermaid', 'erDiagram']
    for table in tables:
        lines.append(f'    {table.name} {{')
        for column in table.columns:
            keys = column_keys(column, diagram=True)
            lines.append(f'        {erd_type(column, dialect)} {column.name}' + (f' {keys}' if keys else ''))
        lines.append('    }')
    lines += ['    alembic_version {', '        VARCHAR(32) version_num PK', '    }', '']
    for table in tables:
        for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
            lines.append(erd_relationship(fk))
    lines += ['```', '',
        '### 2.2. Ma trận 25 khóa ngoại và lực lượng quan hệ', '',
        'Cột “Con/cha” ghi số bản ghi con có thể thuộc một cha; cột “Cha/con” ghi số cha được tham chiếu bởi một bản ghi con. Tính tùy chọn của FK và UNIQUE được lấy từ schema, không suy ra từ giả định nghiệp vụ.', '',
        '| Bảng cha | Bảng con.FK | Con/cha | Cha/con | ON DELETE | Ý nghĩa liên kết |',
        '| --- | --- | --- | --- | --- | --- |']
    for table in tables:
        for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
            children = '0..1' if single_unique(fk.parent) else '0..N'
            parents = '0..1' if fk.parent.nullable else '1'
            lines.append(f'| `{fk.column.table.name}` | `{table.name}.{fk.parent.name}` → `{fk.column.name}` | {children} | {parents} | `{fk.ondelete}` | {meaning(table.name, fk.parent.name)} |')
    lines += ['',
        '**Quan hệ nhiều–nhiều:** users ↔ roles qua user_roles; lecturers ↔ presentations qua course_lecturers; advisors ↔ students qua advisor_students; students ↔ presentations qua student_enrollments. Các tên rút gọn trong câu này tương ứng lecturer_profiles, course_presentations, advisor_profiles và student_profiles.', '',
        'UNIQUE(user_id) ở ba bảng hồ sơ không buộc tài khoản phải có hồ sơ, không tự gán vai trò và không cấm một tài khoản có nhiều loại hồ sơ. UNIQUE(advisor_id, student_id) không bảo đảm mỗi sinh viên chỉ có một cố vấn hoặc lưu được nhiều năm cho cùng một cặp.', '',
        '### 2.3. Chính sách xóa và bảo toàn lịch sử', '']
    lines += ['', 'Các quan hệ tài khoản → hồ sơ → đăng ký → snapshot → dự báo → kế hoạch → nhiệm vụ và ghi chú/yêu cầu hỗ trợ dùng RESTRICT để chặn xóa dây chuyền. Khóa tài khoản bằng `users.is_active=false`; hoàn tất/hủy kế hoạch bằng trạng thái. Không có chức năng purge lịch sử tự động. CASCADE chỉ còn ở liên kết vai trò/phân công; SET NULL giữ bản ghi audit và người thao tác/người nhận tùy chọn.', '',
        'Trigger `protect_prediction_snapshot` chặn sửa snapshot đã được dự báo; `protect_prediction_context` chặn sửa đầu vào, danh tính model và kết quả dự báo. DELETE được bảo vệ bằng FK RESTRICT khi có bản ghi con; bản ghi lá không có phụ thuộc vẫn có thể xóa bằng SQL nếu tài khoản DB đủ quyền. Artifact archive phải được sao lưu cùng database.', '',
        '## 3. Đặc tả toàn bộ bảng', '']
    for number, table in enumerate(tables, 1):
        title, purpose = TABLES[table.name]
        lines += [f'<a id="table-{table.name}"></a>', '', f'### 3.{number}. `{table.name}` — {title}', '',
                  purpose, '', '| Thuộc tính | Kiểu PostgreSQL | Khóa / tham chiếu | NULL | Server default | Ý nghĩa thuộc tính |',
                  '| --- | --- | --- | --- | --- | --- |']
        for column in table.columns:
            default = str(column.server_default.arg) if column.server_default is not None else ('sequence SMALLSERIAL' if table.name == 'roles' and column.name == 'id' else '—')
            lines.append(f'| `{column.name}` | `{column.type.compile(dialect=dialect)}` | {column_keys(column)} | {"Có" if column.nullable else "Không"} | `{default}` | {meaning(table.name, column.name)} |')
        lines += ['', '**Khóa chính:** ' + ', '.join(f'`{c.name}`' for c in table.primary_key.columns) + '.', '']
        for constraint in sorted(table.constraints, key=lambda c: str(c.name)):
            if isinstance(constraint, UniqueConstraint):
                lines.append('- UNIQUE: ' + ', '.join(f'`{c.name}`' for c in constraint.columns) + '.')
            if isinstance(constraint, CheckConstraint):
                lines.append(f'- CHECK `{constraint.name}`: `{constraint.sqltext}`.')
        for index in sorted(table.indexes, key=lambda i: i.name):
            lines.append(f'- Index: `{str(CreateIndex(index).compile(dialect=dialect))}`.')
        lines.append('')
    lines += ['<a id="table-alembic_version"></a>', '', '### 3.20. `alembic_version` — Phiên bản schema (hạ tầng)', '',
        'Bảng do Alembic quản lý, không được ánh xạ thành model nghiệp vụ và không có FK với 19 bảng trên.', '',
        '| Thuộc tính | Kiểu PostgreSQL | Khóa / tham chiếu | NULL | Server default | Ý nghĩa thuộc tính |',
        '| --- | --- | --- | --- | --- | --- |',
        '| `version_num` | `VARCHAR(32)` | PK | Không | `—` | ID revision schema đã áp dụng; hiện là 0002_normalize. Alembic quản lý dòng version khi nâng/hạ cấp. |', '',
        '### 3.21. Nội dung JSON và quan hệ không được bảo đảm bằng FK', '',
        '| Cột JSONB / tham chiếu | Nội dung có ý nghĩa | Cách diễn giải |', '| --- | --- | --- |',
        '| student_feature_snapshots.raw_features_json.snapshot_metadata | source, previous_snapshot_id, observed_at, updated_by_user_id | Nguồn/thời điểm quan sát, snapshot trước và người cập nhật. ID trong JSON không được kiểm tra bởi FK. |',
        '| prediction_runs.inference_context | features (17 đặc trưng), model_id, model_version, threshold, model_sha256, cutoff_fraction, positive_label | Đầu vào/danh tính của lần suy luận đã lưu; trường tùy chọn phụ thuộc phiên bản context. NULL là lịch sử cũ chưa đủ provenance. |',
        '| ml_models.metadata_json | Thông tin thuật toán, nguồn metric, hợp đồng/runtime, dấu hiệu chỉnh metric | Cấu trúc mở do ứng dụng xác minh; có thể thay đổi theo phiên bản registry. |',
        '| audit_logs.target_type + target_id | Loại đối tượng và UUID được thao tác | Tham chiếu đa hình, không có đường FK trên ERD và không tự CASCADE theo đối tượng đích. |', '',
        '### 3.22. Nguồn ghép 17 đặc trưng mô hình', '',
        '| Nguồn | Thuộc tính | Số lượng |', '| --- | --- | --- |',
        '| courses | code_module | 1 |',
        '| student_profiles | gender, highest_education, age_band | 3 |',
        '| student_enrollments | studied_credits, date_registration | 2 |',
        '| student_feature_snapshots | total_clicks_to_t, clicks_resource_to_t, clicks_url_to_t, active_days_to_t, active_day_ratio, days_since_last_activity, clicks_recent_7, clicks_recent_30, assessments_submitted_to_t, late_submissions_to_t, submission_rate | 11 |', '',
        'Tổng cộng 17 đầu vào được dựng tại `services/prediction_service.py::database_features`. final_result, imd_band, region, disability và num_of_prev_attempts không thuộc bộ đầu vào hiện tại. Các tỷ lệ phải có định nghĩa ETL/nguồn dữ liệu; schema chỉ lưu và kiểm tra miền giá trị, không có bảng raw LMS/assessment để tự tính toàn bộ chỉ số.', '']
    lines += ['## 4. Miền giá trị và mô hình active', '',
        'Số đếm không âm; tín chỉ/thời lượng dương; tỷ lệ, xác suất, threshold và metric trong [0,1], cutoff fraction trong (0,1]. Các CHECK float cũng từ chối NaN và vô cực. `date_registration` và `date_unregistration` là số ngày tương đối có thể âm, không áp CHECK không âm.', '',
        'Trạng thái kế hoạch: ACTIVE/COMPLETED/CANCELLED; yêu cầu trợ giúp: PENDING/IN_PROGRESS/RESOLVED; priority: HIGH/MEDIUM/LOW. Kết quả cuối kỳ chấp nhận chữ hoa từ API và dạng nhãn gốc OULAD để giữ dữ liệu nhập hiện có. Không tự chuyển đổi dữ liệu cũ không hợp lệ.', '',
        'Partial UNIQUE `uq_ml_models_one_active` bảo đảm tối đa một model active. Registry yêu cầu đúng một model active khi startup/suy luận; database vẫn cho phép không có model active để bảo trì. Activate tắt model cũ rồi bật model mới trong cùng transaction có advisory lock.', '',
        '`ml_models.average_precision` độc lập `roc_auc`. Seed AP 0.8967566497124569 là tham chiếu validation trong metadata artifact; ROC-AUC để NULL vì nguồn này không cung cấp ROC-AUC. Không coi các chỉ số đó là một lần đánh giá test mới.', '',
        '## 5. Truy vấn danh sách và chỉ mục', '',
        'Danh sách cố vấn gom toàn bộ enrollment và chọn snapshot/prediction mới nhất bằng `row_number()` theo created_at DESC, id DESC. Số kế hoạch ACTIVE/nhiệm vụ chưa hoàn thành được GROUP BY sinh viên. Bảng học phần lấy kết quả hiện hành trong một truy vấn; sĩ số các học phần được gom nhóm. Snapshot mới chưa dự báo không dùng lại kết quả snapshot cũ.', '',
        'Ba API danh sách `/advisor/students`, `/lecturer/courses/{id}/students`, `/lecturer/courses/{id}/risk-board` dùng limit mặc định 100, tối đa 500, offset không âm và sắp xếp ổn định. Frontend tải lần lượt các trang cho danh sách đang hiển thị, giữ bộ lọc và hủy kết quả nếu đổi tài khoản. Export/thống kê nội bộ vẫn lấy đủ dữ liệu trong phạm vi quyền.', '',
        'Index ghép phục vụ enrollment, snapshot/prediction mới nhất, kế hoạch/nhiệm vụ, phân công và người nhận hỗ trợ. Không giữ index đơn student_code trùng UNIQUE. Kiểm thử xác nhận số SELECT không tăng theo số sinh viên trong trang; chưa khẳng định mức tăng tốc trên dữ liệu lớn hoặc tải nhiều máy.', '',
        '## 6. Quy tắc còn thuộc tầng nghiệp vụ', '',
        'Phân quyền theo phân công; student_id của kế hoạch tương ứng enrollment của prediction; người nhận hỗ trợ đúng vai trò/trạng thái; lịch sử phân công theo năm học; danh mục môn và khả năng ánh xạ OULAD/HUIT vẫn được kiểm tra tại service/API hoặc cần quy định bổ sung. Database không có Row Level Security. UNIQUE advisor_students vẫn là (advisor_id, student_id), không tự thay thành lịch sử nhiều năm.', '',
        '## 7. Khởi tạo và nâng cấp', '',
        'Docker chỉ chạy 01 schema → 02 seed → 03 trigger → 04 version khi data directory còn trống. Volume đã có dữ liệu phải dùng Alembic; restart container hoặc CREATE TABLE IF NOT EXISTS không nâng cấp schema. Migration không chạy tự động trong startup backend. Xem hướng dẫn vận hành và bằng chứng ở mục 1.', '']
    lines = detailed_document(lines, tables, dialect)
    (ROOT / 'database/database_design_plan.md').write_text('\n'.join(lines), encoding='utf-8')
