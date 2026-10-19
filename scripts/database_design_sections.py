"""Detailed narrative following the original database design's nine sections.

The old document is a reference; physical facts are generated from current ORM.
No external file or instruction in that file is needed to regenerate this report.
"""
from sqlalchemy.schema import CreateIndex


TABLE_NOTES = {
    'users': 'Luồng sử dụng: quản trị tạo/cập nhật tài khoản; đăng nhập tra email hoặc mã sinh viên qua student_profiles. Khóa tài khoản bằng is_active thay cho xóa khi đã có hồ sơ/lịch sử. Lưu hash mật khẩu không có nghĩa đổi mật khẩu đã thu hồi mọi JWT cũ; schema hiện chưa có token_version/bảng revocation.',
    'roles': 'Gán hoặc gỡ vai trò thay đổi các dòng user_roles; việc gán vai trò không tự bảo đảm đã có hồ sơ tương ứng. Kiểm tra vai trò và kiểm tra phạm vi dữ liệu là hai bước riêng tại backend.',
    'user_roles': 'Mỗi dòng biểu diễn một lần gán vai trò, không có cột id riêng. Cùng user_id có thể xuất hiện nhiều lần với role_id khác nhau; cùng role_id có thể được gán cho nhiều người. CASCADE chỉ xóa liên kết khi cha bị xóa, không xóa tài khoản từ phía vai trò.',
    'student_profiles': 'Hồ sơ nhân khẩu học có thể được cập nhật, vì vậy không dùng giá trị hiện tại để tái dựng đầu vào của dự báo cũ. Snapshot chỉ cố định hành vi; bộ 17 đặc trưng của lần suy luận phải lấy từ prediction_runs.inference_context.',
    'advisor_profiles': 'Một cố vấn có thể theo dõi nhiều sinh viên thông qua advisor_students. Khi tạo ghi chú/kế hoạch hoặc xem tổng quan, API phải xác minh hồ sơ cố vấn và phân công của chính người gọi. Có profile không tự động cấp vai trò ADVISOR.',
    'lecturer_profiles': 'Một giảng viên có thể được phân công nhiều đợt mở môn; chỉ các course_presentations được nối qua course_lecturers mới thuộc phạm vi xử lý. Có vai trò LECTURER nhưng thiếu hồ sơ không được suy ra hồ sơ của người khác.',
    'courses': 'Phân biệt môn học với lần mở môn: tên và mã dùng chung ở courses; lịch mở môn nằm trong course_presentations. Mã tùy ý được lưu trong DB không đồng nghĩa artifact OULAD hiện tại có thể suy luận mã đó; schema đầu vào ML kiểm tra danh mục riêng.',
    'course_presentations': 'Cặp (course_id, code_presentation) xác định duy nhất một đợt mở môn. Hai môn khác nhau có thể dùng cùng code_presentation. Xóa đợt có enrollment bị RESTRICT; các phân công vẫn là quan hệ phụ và dùng CASCADE khi việc xóa cha được phép.',
    'student_enrollments': 'Đây là đơn vị phân tách học tập theo môn: một sinh viên học nhiều đợt tạo nhiều enrollment. Không ghép trực tiếp một prediction với student_id mà bỏ qua enrollment, vì sẽ trộn nguy cơ và nhiệm vụ giữa các môn. Cập nhật final_result đơn thuần không tự tạo snapshot mới.',
    'course_lecturers': 'UNIQUE(lecturer_id, presentation_id) ngăn phân công lặp cùng cặp, nhưng không cấm một học phần có nhiều giảng viên. Vai trò trong học phần là nhãn nghiệp vụ, không thay cho việc kiểm tra roles.code của tài khoản.',
    'advisor_students': 'Cặp (advisor_id, student_id) duy nhất trên mọi năm học trong schema hiện tại. Đổi academic_year không tạo lịch sử nhiều năm cho cùng cặp; muốn quản lý lịch sử phân công theo năm cần thay đổi mô hình và migration riêng. Không có ràng buộc mỗi sinh viên chỉ thuộc một cố vấn.',
    'student_feature_snapshots': 'Khi giảng viên sửa chỉ số, repository sao chép các chỉ số nền, áp dụng phần thay đổi và tạo dòng mới kèm snapshot_metadata. Thiếu snapshot nền trả lỗi thay vì tự dựng toàn bộ bằng 0. Trigger từ chối UPDATE snapshot đã có prediction; số 0 mặc định khi INSERT không tự chứng minh dữ liệu đã được quan sát đầy đủ.',
    'ml_models': 'Registry dùng database để chọn model active cho dashboard, batch và CLI. Kích hoạt kiểm tra artifact/metadata/schema/checksum và suy luận thử trước khi commit cùng audit; cache phân biệt theo danh tính/hash. Artifact gốc và archive theo SHA-256 nằm ngoài DB, phải được lưu và sao lưu để replay.',
    'prediction_runs': 'Chạy batch lại tạo dòng lịch sử mới, không ghi đè kết quả trước. Trigger bảo vệ snapshot_id, model_id, prediction_label, risk_probability, created_at và inference_context. Dự báo mới có context để replay; bản cũ thiếu context được giữ và trả trạng thái truy vết LEGACY_UNVERIFIED thay vì suy đoán dữ liệu.',
    'intervention_plans': 'Lập kế hoạch phải dùng dự báo của snapshot hiện hành trong đúng enrollment. Snapshot mới chưa dự báo khiến API từ chối dùng dự báo cũ để lập kế hoạch mới; các kế hoạch đã có vẫn được giữ. Hoàn thành mọi nhiệm vụ không tự đổi status của kế hoạch bằng trigger.',
    'intervention_tasks': 'Khi sinh viên hoàn thành nhiệm vụ, service ghi is_completed, completed_at và phản hồi nếu có. Thống kê việc còn lại tổng hợp nhiệm vụ chưa hoàn thành của các kế hoạch ACTIVE. Việc gán môn được truy qua chuỗi FK, không suy từ title, category hoặc target_metric.',
    'advising_notes': 'Từ enrollment_id, API xác định sinh viên rồi kiểm tra cố vấn được phân công trước khi ghi. Biên bản là dữ liệu tư vấn độc lập; agreed_actions không tự đồng bộ thành intervention_tasks. RESTRICT giữ ghi chú khi cố xóa enrollment hoặc hồ sơ cố vấn được tham chiếu.',
    'student_help_requests': 'Service chỉ chọn người nhận đang hoạt động, có vai trò phù hợp và được phân công. Nếu chỉ định người nhận không hợp lệ thì từ chối; nếu không chỉ định và chưa có phân công hợp lệ thì giữ yêu cầu chưa gán. Một yêu cầu có presentation_id NULL không được coi là yêu cầu của mọi môn.',
    'audit_logs': 'Ứng dụng chủ động gọi write_audit_log cho các đường thao tác đã triển khai; không có trigger audit toàn bộ SQL. Một số đường commit nghiệp vụ và audit riêng, nên không mặc định mọi thao tác đều có log nguyên tử. Log dùng truy vết sự kiện, không thay thế lịch sử đầu vào dự báo.',
}

SUBSYSTEMS = '''## 2. Các phân hệ dữ liệu

| Phân hệ | Bảng | Vai trò trong hệ thống |
| --- | --- | --- |
| Danh tính và quyền (6) | users, roles, user_roles, student_profiles, advisor_profiles, lecturer_profiles | Đăng nhập, nhiều vai trò và hồ sơ chuyên biệt; phân biệt tài khoản với danh tính sinh viên/cố vấn/giảng viên. |
| Đào tạo (3) | courses, course_presentations, student_enrollments | Tổ chức môn học, đợt mở môn và đăng ký; làm gốc phân tách dữ liệu theo học phần. |
| Phân công (2) | course_lecturers, advisor_students | Xác định phạm vi giảng viên và cố vấn được đọc/ghi; liên kết nhiều–nhiều có UNIQUE ghép. |
| Đặc trưng (1) | student_feature_snapshots | Lưu 11 chỉ số hành vi tại mốc quan sát; tạo lịch sử snapshot thay cho sửa dữ liệu đã dùng dự báo. |
| ML và dự báo (2) | ml_models, prediction_runs | Chọn phiên bản mô hình, lưu xác suất/nhãn và provenance để truy vết lần suy luận. |
| Can thiệp và tư vấn (3) | intervention_plans, intervention_tasks, advising_notes | Chuyển kết quả dự báo thành kế hoạch, việc cần làm và ghi chú tư vấn trong phạm vi học phần. |
| Hỗ trợ và kiểm toán (2) | student_help_requests, audit_logs | Tiếp nhận khó khăn của sinh viên, phân công xử lý và ghi các sự kiện hệ thống. |
| Hạ tầng migration (1) | alembic_version | Ghi revision schema; không tính vào 19 bảng nghiệp vụ. |

Các phân hệ là nhóm nghiệp vụ trong schema PostgreSQL `public`, không phải các schema vật lý riêng. Phân quyền hiện được backend kiểm tra bằng JWT, trạng thái tài khoản, vai trò, hồ sơ và phân công; database chưa có Row Level Security.

### 2.1. Luồng liên kết dữ liệu chính

```mermaid
flowchart LR
    A["Tài khoản và hồ sơ"] --> B["Đăng ký học phần"]
    C["Môn và đợt mở môn"] --> B
    B --> D["Snapshot hành vi"]
    D --> E["Lần dự báo và provenance"]
    M["Model active và artifact"] --> E
    E --> F["Kế hoạch can thiệp"]
    F --> G["Nhiệm vụ và phản hồi"]
    B --> H["Ghi chú tư vấn"]
    P["Phân công cố vấn/giảng viên"] -. "phạm vi quyền" .-> B
    A --> Q["Yêu cầu trợ giúp"]
```

Sơ đồ trên mô tả liên kết nghiệp vụ; không hàm ý hệ thống tự động tạo kế hoạch/nhiệm vụ ngay sau dự báo. Đường FK vật lý và tính bắt buộc/tùy chọn được thể hiện riêng ở mục 3.
'''

FLOW = '''### 5.2. Luồng thực thi theo nghiệp vụ

1. **Tài khoản và hồ sơ:** tạo users, gán user_roles, tạo hồ sơ tương ứng. Đăng nhập bằng email hoặc mã sinh viên; backend kiểm tra trạng thái tài khoản và vai trò hiện hành. Chưa có hồ sơ thì không mượn hồ sơ tài khoản khác.
2. **Đào tạo và phân công:** tạo courses, course_presentations, student_enrollments. Gán giảng viên qua course_lecturers và cố vấn qua advisor_students trước khi cho xử lý dữ liệu thuộc phạm vi đó.
3. **Thu nhận chỉ số:** tạo student_feature_snapshots từ nguồn nhập/đồng bộ đã xác định. Schema hiện không có bảng VLE log thô hoặc bảng assessment để tự tính toàn bộ 11 chỉ số. Nhãn demo/nguồn dữ liệu phải được giữ rõ trong metadata nếu có.
4. **Cập nhật tiến độ:** khi sửa chỉ số, tạo snapshot mới và ghi nguồn, người cập nhật, observed_at, previous_snapshot_id. Chỉ sửa final_result thì không tạo snapshot. Snapshot mới chưa có dự báo không dùng lại kết quả của snapshot cũ.
5. **Suy luận trực tiếp:** POST /api/v1/predictions/ yêu cầu tài khoản hoạt động và token hợp lệ; lấy model active qua registry, suy luận trên 17 giá trị payload và trả provenance. Endpoint này không tự tạo enrollment, snapshot, prediction_run hoặc kế hoạch; lịch sử trình duyệt được lưu riêng theo tài khoản/API server.
6. **Suy luận từ database:** batch hoặc CLI chọn snapshot mới nhất của enrollment, ghép đủ 17 đầu vào, kiểm tra CUTOFF_75 và hợp đồng model. Tất cả suy luận phải thành công trước khi thêm các prediction_runs. Endpoint batch lưu kết quả cùng audit BATCH_PREDICT trong một transaction; lỗi không sinh kết quả fallback hoặc lưu lô dở dang.
7. **Lập kế hoạch:** cố vấn chọn sinh viên và enrollment thuộc phân công; API lấy dự báo hiện hành của đúng enrollment. Tạo intervention_plans và các intervention_tasks nếu được yêu cầu. Giảng viên giao nhiệm vụ vào plan ACTIVE của đúng sinh viên/học phần được phân công.
8. **Thực hiện và theo dõi:** sinh viên xem nhiệm vụ theo enrollment và đánh dấu hoàn thành. Thống kê/nhắc nhở tổng hợp theo kế hoạch ACTIVE và nhiệm vụ chưa hoàn thành; không coi việc hoàn thành task tự động chứng minh hiệu quả học tập.
9. **Tư vấn/hỗ trợ:** lưu advising_notes theo enrollment; student_help_requests có vai trò đích, người nhận hợp lệ nếu có, phạm vi học phần, trạng thái và phản hồi.
10. **Kiểm toán:** các đường xử lý có gọi write_audit_log ghi action, actor và đối tượng. Không có cơ chế tự động ghi audit cho mọi UPDATE/DELETE SQL trực tiếp.

### 5.3. Quy tắc chọn dữ liệu hiện hành và tổng hợp nguy cơ

| Tình huống | Cách hệ thống diễn giải |
| --- | --- |
| Nhiều snapshot của một enrollment | Chọn created_at DESC, id DESC; không dùng cutoff_stage làm định danh duy nhất. |
| Nhiều dự báo của snapshot hiện hành | Chọn prediction_runs.created_at DESC, id DESC. |
| Thiếu snapshot hoặc snapshot mới chưa dự báo | Xác suất NULL, trạng thái API NOT_PREDICTED; không tự ghi thêm nhãn này vào prediction_label SMALLINT. |
| Có ít nhất một môn nhãn 1 | Sinh viên có nguy cơ; chọn xác suất lớn nhất trong các môn có nhãn 1 làm giá trị đại diện. |
| Mọi môn đã được dự báo và đều nhãn 0 | SAFE; xác suất đại diện là giá trị lớn nhất trong các môn đã dự báo. |
| Không có môn nguy cơ nhưng còn môn chưa dự báo | NOT_PREDICTED, không kết luận an toàn khi chưa đủ dữ liệu. |

Nhãn lấy từ prediction_label đã lưu theo threshold của lần chạy, không phân loại lại toàn bộ lịch sử bằng 0.5. API kèm total_courses, predicted_courses, unpredicted_courses, high_risk_courses; các trường tổng hợp này được tính từ dữ liệu, không phải cột vật lý trong student_profiles.

### 5.4. Giao dịch, thời gian và truy vết

`core/database.py` cung cấp AsyncSession: rollback khi có ngoại lệ và đóng session ở finally; commit do endpoint/repository quyết định. Engine dùng pool_pre_ping=True, pool_size=10, max_overflow=20; session expire_on_commit=False, autoflush=False. Các thông số này là cấu hình runtime hiện tại, không phải ràng buộc dữ liệu.

`write_audit_log()` flush để caller quyết định commit. Batch và activate/reload model đã có transaction gắn với audit; một số luồng quản trị khác vẫn commit nghiệp vụ và log riêng. Không suy ra tính nguyên tử của toàn hệ thống chỉ từ việc có bảng audit_logs.

Các thời điểm dùng TIMESTAMPTZ; ORM tạo thời gian UTC, PostgreSQL hiển thị theo timezone session. Kiểu này lưu một thời điểm và không giữ nguyên tên múi giờ nhập vào. DATE dùng cho ngày tư vấn, ngày bắt đầu và hạn hoàn thành. Ngày đăng ký/rút học là INTEGER tương đối, có thể âm, không phải DATE. updated_at mặc định NOW() nhưng không có trigger chung tự thay đổi khi UPDATE bằng SQL trực tiếp.

Replay dùng inference_context và đúng artifact trong archive theo SHA-256. Thay hồ sơ sinh viên, tín chỉ hoặc model registry sau đó không được thay đầu vào lịch sử. Bản ghi cũ không đủ context phải được giữ là chưa xác minh, không backfill bằng dữ liệu hiện tại.
'''

RULES = '''### 6.2. Ràng buộc miền giá trị và tính duy nhất

| Nhóm | Ràng buộc vật lý hiện có | Ý nghĩa và giới hạn |
| --- | --- | --- |
| Nhận diện | PK UUID; roles.id SMALLSERIAL; user_roles PK ghép | Không trùng định danh. Sequence có thể tăng dù transaction rollback; không dùng ID để đòi hỏi chuỗi số liên tiếp. |
| Tài khoản/hồ sơ | UNIQUE email, mã sinh viên, mã giảng viên; UNIQUE user_id từng bảng hồ sơ | Một tài khoản có tối đa một hồ sơ mỗi loại, có thể có nhiều loại hồ sơ. |
| Đào tạo/phân công | UNIQUE(course_id,code_presentation), UNIQUE(student_id,presentation_id), UNIQUE(lecturer_id,presentation_id), UNIQUE(advisor_id,student_id) | Ngăn trùng cặp, không áp duy nhất riêng từng thành phần. |
| Số lượng | Các count hành vi và num_of_prev_attempts ≥ 0; tín chỉ/thời lượng > 0 | Không áp ràng buộc không âm cho ngày tương đối. Không tự tính hoặc sửa số liệu. |
| Tỷ lệ/xác suất/metric | active_day_ratio, submission_rate, risk_probability, threshold, accuracy, average_precision, roc_auc trong [0,1] | CHECK float từ chối NaN/vô cực; metric nullable để biểu diễn chưa có số liệu. |
| Cutoff | cutoff_fraction trong (0,1] | Dịch vụ batch hiện kiểm tra cutoff_stage=CUTOFF_75; database chưa khóa danh mục cutoff_stage. |
| Nhãn và trạng thái | prediction_label 0/1; plan ACTIVE/COMPLETED/CANCELLED; help PENDING/IN_PROGRESS/RESOLVED; priority HIGH/MEDIUM/LOW | NOT_PREDICTED là trạng thái API khi không có dự báo hiện hành, không phải giá trị lưu trong prediction_label. |
| Nhân khẩu học/kết quả | CHECK gender, age_band, disability và final_result | highest_education và mã môn còn được schema suy luận kiểm tra riêng theo artifact. |
| Model active | Partial UNIQUE trên is_active WHERE is_active | Tối đa một active ở DB; điều kiện phải có đúng một active được registry kiểm tra. |

### 6.3. Bảo vệ lịch sử và model active

RESTRICT chặn xóa cha đang có dữ liệu phụ thuộc trong chuỗi hồ sơ → enrollment → snapshot → prediction → plan → task và các ghi chú/hỗ trợ liên quan. CASCADE chỉ còn ở liên kết vai trò/phân công; SET NULL giữ dữ liệu audit/người thao tác/người nhận tùy chọn. Bản ghi lá không có phụ thuộc vẫn có thể bị xóa bởi tài khoản SQL đủ quyền; đây không phải cơ chế cấm mọi DELETE.

Trigger `protect_prediction_snapshot` chặn thay đổi snapshot đã được dùng dự báo. Trigger `protect_prediction_context` chặn sửa đầu vào, model, kết quả, thời điểm tạo và context của prediction. Không có trigger tự hoàn tất kế hoạch hoặc tự tạo nhiệm vụ từ nhãn nguy cơ.

Registry kiểm tra artifact, metadata, danh sách/thứ tự 17 đặc trưng, threshold, positive label, cutoff và checksum. Khi activate, tắt model active cũ rồi bật phiên bản mới trong transaction có advisory lock; worker đọc model active ở request tiếp theo, cache theo danh tính/hash. Không dùng partial UNIQUE để suy luận rằng luôn tồn tại một active.

### 6.4. Quy tắc còn thuộc API/service

- Kiểm tra người gọi có vai trò, hồ sơ và phân công tương ứng trước khi đọc/ghi; ADMIN không tự được bỏ qua mọi phạm vi trong portal chuyên biệt.
- Xác minh student_id trong plan trùng sinh viên của enrollment được dự báo; các FK độc lập chưa tạo ràng buộc chéo này.
- Kiểm tra người nhận hỗ trợ đang hoạt động, đúng vai trò/phân công và môn sinh viên theo học; FK target_user_id chỉ bảo đảm tài khoản tồn tại.
- Quy định lịch sử phân công theo năm học, danh mục category/meeting_type/role_in_course và tính nhất quán is_completed/completed_at chưa có CHECK đầy đủ tại DB.
- Cơ chế thu hồi mọi JWT sau đổi/đặt lại mật khẩu, Row Level Security và audit tự động mọi câu SQL chưa được triển khai chỉ bằng schema này.

### 6.5. Truy vấn danh sách và phân trang

Danh sách cố vấn gom enrollment và dùng row_number() để chọn snapshot/prediction hiện hành; GROUP BY đếm kế hoạch ACTIVE và nhiệm vụ chưa hoàn thành. Bảng nguy cơ/danh sách học phần lấy snapshot/dự báo theo lô; sĩ số các học phần được tổng hợp trong truy vấn gom nhóm.

Ba API `/advisor/students`, `/lecturer/courses/{id}/students`, `/lecturer/courses/{id}/risk-board` nhận limit mặc định 100, tối đa 500, offset không âm và sắp xếp ổn định. Frontend đọc lần lượt đủ trang, giữ bộ lọc và không ghép kết quả của hai tài khoản; export/thống kê nội bộ vẫn cần đủ dữ liệu thuộc phạm vi quyền.

Bằng chứng đã ghi nhận 8 SELECT cho trang 1 sinh viên và 8 SELECT cho trang 4 sinh viên. EXPLAIN trên bảng local nhỏ vẫn có thể chọn Seq Scan + Sort; đây là kiểm tra số truy vấn và cấu trúc index, chưa phải cam kết tăng tốc trên dữ liệu lớn hoặc kiểm thử tải nhiều máy.
'''

OPERATIONS = '''## 7. Khởi tạo, dữ liệu mẫu, migration và kiểm tra

### 7.1. Kết nối và môi trường

| Thành phần | Host/cổng mặc định theo Compose | Ghi chú |
| --- | --- | --- |
| PostgreSQL từ host | localhost:5433 | Cổng cấu hình bằng POSTGRES_HOST_PORT; giá trị thực lấy từ môi trường. |
| PostgreSQL từ container backend | postgres:5432 | Sử dụng mạng Compose, không dùng localhost của container. |
| pgAdmin từ host | localhost:5050 | Cấu hình PGADMIN_PORT; đây là giao diện quản trị, không phải cổng PostgreSQL. |

Database mặc định personalized_learning_db, schema public; tài khoản/mật khẩu và SECRET_KEY lấy từ cấu hình môi trường. Không đưa URL chứa mật khẩu hoặc dữ liệu backup vào tài liệu/Git. PostgreSQL 15 và asyncpg là nền tảng hiện đã kiểm thử; backend dùng SQLAlchemy asyncio theo requirements được khóa phiên bản.

### 7.2. Database mới và seed

Docker mount docker/postgres/init-scripts vào /docker-entrypoint-initdb.d và chỉ chạy khi data directory còn trống:

1. `01_init_schema.sql`: 19 bảng, PK/UNIQUE/CHECK/FK/index và extensions uuid-ossp, pgcrypto; UUID mặc định gen_random_uuid().
2. `02_seed_data.sql`: bốn vai trò, tài khoản/dữ liệu minh họa, danh mục học phần và model seed.
3. `03_prediction_integrity.sql`: cột provenance tương thích và hai trigger bảo vệ UPDATE lịch sử.
4. `04_schema_version.sql`: marker Alembic cho schema canonical vừa được tạo; không chạy riêng để stamp database cũ.

Volume postgres_data giữ dữ liệu bền vững; restart container hoặc CREATE TABLE IF NOT EXISTS không cập nhật định nghĩa bảng đã tồn tại. Backend không gọi Base.metadata.create_all() để nâng schema và không tự chạy migration trong startup.

Seed model v1.0.0-cutoff75 có threshold 0.5, cutoff_fraction 0.75. AP 0.8967566497124569 là tham chiếu validation từ metadata artifact, ROC-AUC để NULL vì nguồn đó không cung cấp; không trình bày AP thành ROC-AUC hay kết quả test mới. Seed không bật thêm model nếu đã có model active. Dữ liệu seed/demo không chứng minh đã có ETL hoặc dữ liệu LMS thực tế.

### 7.3. Nâng cấp database đã có dữ liệu

Alembic `0001_baseline` tạo schema trên DB trống hoặc kiểm tra schema cũ trước khi nhận baseline. `0002_normalize` kiểm tra dữ liệu, bổ sung ràng buộc/default/index, đổi chính sách giữ lịch sử và thêm average_precision. SQL baseline/revision được đóng băng; các thay đổi tiếp theo phải có revision mới.

Baseline chỉ chấp nhận cấu trúc đã xác định và đúng các biến thể index legacy đã kiểm tra; schema lệch làm dừng. Preflight báo số dòng sai miền, academic_rank NULL hoặc active trùng; không tự clamp, chọn model hoặc xóa dữ liệu để vượt ràng buộc. DDL/correction chạy trong transaction có advisory lock và lock timeout.

Tạo backup, khôi phục vào database riêng rồi thử nâng cấp trước khi áp dụng nguồn. Helper local còn khóa bảng, kiểm tra backup vẫn khớp và xác minh dữ liệu trước commit. Chi tiết xử lý lỗi/downgrade/khôi phục tại [database_migrations.md](../docs/database_migrations.md).

```powershell
# Chạy từ gốc repository sau khi cấu hình môi trường.
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe scripts/verify_migrations.py
# Backup và thử khôi phục, chưa sửa nguồn:
.venv/Scripts/python.exe scripts/migrate_database.py --container kltn13_postgres
# Áp dụng có backup/restore lại trước khi ghi nguồn:
.venv/Scripts/python.exe scripts/migrate_database.py --container kltn13_postgres --apply
.venv/Scripts/python.exe -m alembic check
.venv/Scripts/python.exe scripts/run_backend_tests.py -q
```

Các lệnh trên là hướng dẫn tái lập, không phải yêu cầu chạy lại trong lần viết tài liệu này. Runner/test dùng database riêng hậu tố _test, fixture rollback và kiểm tra hash dữ liệu. Database trống nâng bằng Alembic chỉ có schema/trigger, không tự nạp tài khoản demo; nếu cần seed, nạp sau khi schema ở head.

### 7.4. Câu SQL chỉ đọc để kiểm tra

```sql
-- 19 bảng nghiệp vụ và bảng hạ tầng Alembic.
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

SELECT version_num FROM alembic_version;

SELECT tablename, indexname, indexdef FROM pg_indexes
WHERE schemaname = 'public' ORDER BY tablename, indexname;

SELECT conrelid::regclass AS table_name, conname,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint WHERE connamespace = 'public'::regnamespace
ORDER BY conrelid::regclass::text, conname;

SELECT version, is_active, threshold, cutoff_fraction,
       accuracy, average_precision, roc_auc
FROM ml_models ORDER BY created_at;
```

### 7.5. Bằng chứng và giới hạn xác nhận

Kết quả ngày 19/10 được lưu trong [báo cáo daily](../reports/dailys/19-10-2026.md): 121 test backend và 48 subtest đạt; 10 test frontend đạt, build thành công; schema SQL mới và schema nâng cấp khớp 19 bảng. Có bảng alembic_version nên fingerprint suite kiểm tra 20 bảng.

[task1-migrations.json](../reports/test-results/task1-migrations.json) ghi kiểm tra upgrade/downgrade/re-upgrade, clone dữ liệu, drift và ràng buộc; [task1-migration-apply.json](../reports/test-results/task1-migration-apply.json) ghi backup/restore và áp dụng local. Khi áp dụng, 18 bảng giữ nguyên hash; model chỉ thêm AP nullable và hiệu chỉnh đúng seed đã xác minh. Backup chứa dữ liệu cá nhân nằm trong .cache/database-backups được Git ignore, phải sao lưu an toàn cùng artifact archive.

Đây là bằng chứng đã thực thi ở phiên triển khai được dẫn nguồn; lần biên soạn lại tài liệu chỉ đối chiếu mã/DDL/báo cáo. Không suy ra schema của mọi môi trường từ kết quả local và không xem kiểm thử phần mềm là bằng chứng hiệu quả can thiệp học tập.
'''

COMPARISON = '''## 8. Đối chiếu thiết kế cũ và schema đã cập nhật

Tài liệu tham khảo ngày 18/10 ghi trạng thái trước chuẩn hóa. Bảng dưới giải thích thay đổi đã triển khai, thay cho việc giữ các khác biệt SQL/ORM cũ như công việc còn tồn tại.

| Nội dung | Bản thiết kế cũ / trạng thái trước chuẩn hóa | Hiện trạng cập nhật |
| --- | --- | --- |
| Quản lý schema | Chưa có Alembic | Có alembic.ini, env asyncpg, baseline 0001, revision 0002 và alembic_version. |
| UUID/timestamp/default | Chủ yếu default PostgreSQL trong SQL; Python default khác nhau | ORM có server default tương ứng SQL; Python default vẫn dùng khi phù hợp. updated_at chưa có trigger UPDATE chung. |
| office_location | SQL VARCHAR(255), ORM String(100) | Cùng VARCHAR(255). |
| academic_rank | SQL cho NULL, ORM bắt buộc | Cùng NOT NULL DEFAULT Giảng viên; dữ liệu cũ NULL phải được xử lý rõ trước nâng cấp. |
| Thời lượng / ngày đăng ký | ORM thiếu default 260; date_registration ORM 0 so với SQL -10 | ORM/SQL thống nhất server default; ngày tương đối vẫn được phép âm. |
| UNIQUE đợt mở môn/đăng ký | SQL có UNIQUE ghép, ORM thiếu | ORM và SQL đều có đủ UNIQUE ghép tương ứng; hai bảng phân công giữ UNIQUE cặp. |
| cutoff_stage | SQL VARCHAR(30), ORM String(50) | Cùng VARCHAR(30). |
| model_name / version / model_file_path | Độ dài SQL/ORM khác nhau; ORM thiếu UNIQUE version | Thống nhất 150 / 30 / 500; version duy nhất. |
| is_active của model | Default SQL TRUE khác ORM FALSE; không có unique active | Default FALSE, partial UNIQUE tối đa một active; registry yêu cầu đúng một khi sử dụng. |
| model_id FK | SQL RESTRICT, ORM CASCADE | Cùng RESTRICT; model có prediction không thể bị xóa. |
| Lịch sử dự báo/can thiệp | CASCADE từ nhiều cha có thể xóa snapshot/prediction/plan/task | Chuỗi quan hệ lịch sử chuyển RESTRICT; ORM không delete-orphan để xóa con trước FK. |
| Miền số/trạng thái | Chỉ có một phần CHECK | CHECK số đếm, tín chỉ, tỷ lệ, xác suất, metric, trạng thái và kết quả; giữ giới hạn tầng nghiệp vụ ở mục 6.4. |
| priority / target_metric | SQL không default priority; độ dài target_metric khác ORM | Cùng default MEDIUM và VARCHAR(255); priority chỉ HIGH/MEDIUM/LOW. |
| Ngày/hình thức tư vấn | ORM thiếu default ngày, meeting_type khác SQL | Server default CURRENT_DATE và ONLINE; API vẫn có hợp đồng request riêng. |
| Chỉ số model | Seed dùng AP khoảng 0.8968 ở roc_auc | Thêm average_precision; ROC-AUC chưa xác định để NULL, có correction nguồn seed. |
| Chỉ mục/truy vấn | 8 index SQL gốc, một số index local ngoài script; truy vấn lặp theo sinh viên | Index canonical ở mục 6.1; gom nhóm/window function và phân trang. Index trùng UNIQUE student_code được bỏ. |
| Provenance/bất biến | Đã có inference_context/trigger từ nâng cấp trước | Tiếp tục giữ trigger, bổ sung bảo vệ DELETE bằng FK và quản lý nâng cấp qua Alembic. |

Schema mới và ORM đã được kiểm tra không có thay đổi autogenerate tại mốc triển khai. Điều đó không có nghĩa mọi quy tắc nghiệp vụ đều trở thành CHECK/FK; các giới hạn như RLS, lịch sử phân công theo năm và token revocation vẫn được ghi rõ.
'''

SCOPE = '''## 9. Phạm vi học phần của can thiệp, tư vấn và trợ giúp

### 9.1. Chuỗi truy vết nhiệm vụ

```mermaid
flowchart LR
    T["intervention_tasks"] -->|"plan_id → id"| P["intervention_plans"]
    P -->|"prediction_run_id → id"| R["prediction_runs"]
    R -->|"snapshot_id → id"| S["student_feature_snapshots"]
    S -->|"enrollment_id → id"| E["student_enrollments"]
    E -->|"student_id → id"| ST["student_profiles"]
    E -->|"presentation_id → id"| CP["course_presentations"]
    CP -->|"course_id → id"| C["courses"]
```

Task không có presentation_id trực tiếp. API truy ngược chuỗi này, xác minh student_id của enrollment và quyền của người gọi; plan.student_id còn là FK riêng nên service phải bảo đảm nhất quán với chuỗi dự báo. Một plan thuộc một dự báo của một enrollment, không mặc định bao phủ mọi môn của sinh viên.

### 9.2. Quy tắc đọc và ghi theo vai trò

| Vai trò/luồng | Cách xác định phạm vi | Hành vi cần giữ |
| --- | --- | --- |
| Sinh viên xem task/nhắc nhở | Tài khoản → student_profiles → enrollment đang chọn → chuỗi plan/prediction/snapshot | Chỉ dữ liệu của chính sinh viên và học phần; không trộn task giữa các enrollment. |
| Cố vấn lập kế hoạch | advisor_profiles → advisor_students → sinh viên → enrollment chọn → dự báo hiện hành | Có phân công và prediction của snapshot mới nhất; nhiều enrollment thì phải chỉ rõ học phần. |
| Giảng viên giao nhiệm vụ | lecturer_profiles → course_lecturers → presentation → enrollment của sinh viên → plan ACTIVE | Chọn plan đúng môn, không lấy một plan ACTIVE bất kỳ của sinh viên. |
| Cố vấn ghi biên bản | advising_notes.enrollment_id → student_id, đối chiếu advisor_students | Chỉ tạo khi kiểm tra quyền thành công; advisor_id là hồ sơ cố vấn, không phải users.id. |
| Sinh viên gửi yêu cầu | Xác minh enrollment sở hữu, gán presentation_id tương ứng, kiểm tra người nhận | Không chấp nhận enrollment của người khác hoặc presentation_id mâu thuẫn; giảng viên đích phải được phân công học phần. |
| Giảng viên cảnh báo cố vấn | Kiểm tra phân công môn và sinh viên thuộc môn, sau đó chọn cố vấn nhận hợp lệ | Yêu cầu gắn presentation_id, không gửi tới tài khoản bất kỳ ngoài phân công. |

### 9.3. Yêu cầu chung và dữ liệu cũ

student_help_requests.presentation_id có thể NULL, biểu diễn yêu cầu không gắn môn hoặc liên kết đã được SET NULL khi xóa cha được phép. Khi API lọc theo enrollment, yêu cầu chung không tự xuất hiện trong mọi môn. target_user_id NULL là chưa gán người nhận, không có nghĩa mọi giảng viên/cố vấn đều được đọc.

Dữ liệu cũ không có provenance hoặc học phần liên quan được giữ nguyên và diễn giải theo liên kết thực có. Không suy đoán môn từ tiêu đề nhiệm vụ, không dựng feature cũ từ hồ sơ mới, không coi thiếu prediction là SAFE. Mọi mở rộng lưu lịch sử hoặc quy tắc phân công cần migration và kiểm thử tương ứng.
'''


def detailed_document(lines, tables, dialect):
    """Keep generated schema/ERD exact, surround it with the reference structure."""
    source = '\n'.join(lines)
    intro = source[:source.index('## 2. Sơ đồ')]
    intro = intro.replace('## 1. Phạm vi và nguồn chuẩn', '## 1. Phạm vi và nguồn đối chiếu')
    intro = intro.replace('### 1.2. Danh mục bảng và chức năng', '### 2.2. Danh mục bảng và chức năng')
    catalog = intro[intro.index('### 2.2.'):]
    intro = intro[:intro.index('### 2.2.')]
    intro = intro.replace('**Cập nhật:** 19/10/2026 — PostgreSQL 15, SQLAlchemy async/asyncpg, Alembic `0002_normalize`.',
        '### Hệ thống gợi ý chiến lược học tập cá nhân hóa — KLTN 13, HUIT\n\n'
        '> **Sinh viên thực hiện:** Phan Trọng Nguyên<br>\n'
        '> **Cập nhật:** 19/10/2026<br>\n'
        '> **CSDL:** PostgreSQL 15 — personalized_learning_db, schema public<br>\n'
        '> **ORM:** SQLAlchemy Async, driver asyncpg<br>\n'
        '> **Revision schema:** 0002_normalize\n\n'
        'Bản biên soạn này kế thừa bố cục chín phần của tài liệu tham khảo ngày 18/10/2026 '
        'do người dùng cung cấp (`Y:\\database_design_plan.md`), cập nhật nội dung theo schema và mã nguồn trong dự án. '
        'Tài liệu mô tả thiết kế đang triển khai, phân biệt ràng buộc DB với kiểm tra tại API/service và các giới hạn còn lại.')
    source_rows = '''
| Nguồn đối chiếu | Nội dung sử dụng |
| --- | --- |
| [01_init_schema.sql](../docker/postgres/init-scripts/01_init_schema.sql) | Cấu trúc vật lý, default, khóa, CHECK và index canonical. |
| [02_seed_data.sql](../docker/postgres/init-scripts/02_seed_data.sql) | Danh mục, model và dữ liệu minh họa. |
| [03_prediction_integrity.sql](../docker/postgres/init-scripts/03_prediction_integrity.sql) | Trigger bất biến snapshot/context. |
| [04_schema_version.sql](../docker/postgres/init-scripts/04_schema_version.sql) | Marker revision trên database Docker mới. |
| [models](../apps/backend/models/) và [schema_contract.py](../apps/backend/models/schema_contract.py) | Mapping 19 bảng và ràng buộc dùng chung. |
| [database.py](../apps/backend/core/database.py) | Engine, session và rollback. |
| [prediction_service.py](../apps/backend/services/prediction_service.py), [risk_service.py](../apps/backend/services/risk_service.py), [model_registry.py](../apps/backend/services/model_registry.py) | Ghép đặc trưng, chọn dự báo hiện hành và chọn model active. |
| [endpoints](../apps/backend/api/v1/endpoints/) và [repositories](../apps/backend/repositories/) | Phân quyền, nghiệp vụ đọc/ghi, transaction và phạm vi học phần. |
| [migration](../apps/backend/migrations/) và [hướng dẫn vận hành](../docs/database_migrations.md) | Baseline, upgrade, backup/restore và xử lý dữ liệu cũ. |
| [Compose](../docker-compose.yml) và [requirements](../apps/backend/requirements.txt) | Kết nối, volume và dependency hiện tại. |
'''
    intro = intro.replace('### 1.1. Quy ước đọc tài liệu', source_rows + '\n### 1.1. Quy ước đọc tài liệu')
    relations = source[source.index('## 2. Sơ đồ'):source.index('## 3. Đặc tả')]
    relations = relations.replace('## 2. Sơ đồ quan hệ và chính sách giữ lịch sử', '## 3. Sơ đồ thực thể và quan hệ')
    relations = relations.replace('### 2.', '### 3.').replace('tại mục 3.', 'tại mục 4.')
    detail = source[source.index('## 3. Đặc tả'):source.index('### 3.21.')]
    detail = detail.replace('## 3. Đặc tả toàn bộ bảng', '## 4. Đặc tả chi tiết 19 bảng và bảng hạ tầng').replace('### 3.', '### 4.')
    for table in tables:
        marker = f'<a id="table-{table.name}"></a>'
        start = detail.index(marker)
        end = detail.find('<a id=', start + len(marker))
        if end == -1:
            end = len(detail)
        section = detail[start:end]
        out = []
        for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
            out.append(f'- `{table.name}.{fk.parent.name}` → [`{fk.column.table.name}.{fk.column.name}`](#table-{fk.column.table.name}); '
                       f'{"không bắt buộc" if fk.parent.nullable else "bắt buộc"}, ON DELETE {fk.ondelete}.')
        incoming = []
        for child in tables:
            for fk in sorted(child.foreign_keys, key=lambda f: f.parent.name):
                if fk.column.table.name == table.name:
                    incoming.append(f'- [`{child.name}.{fk.parent.name}`](#table-{child.name}) tham chiếu `{table.name}.{fk.column.name}`; ON DELETE {fk.ondelete}.')
        extra = '\n**Quan hệ đi ra:**\n\n' + ('\n'.join(out) if out else 'Không có khóa ngoại đi ra; đây là bảng cha/danh mục trong các quan hệ bên dưới.')
        extra += '\n\n**Được tham chiếu bởi:**\n\n' + ('\n'.join(incoming) if incoming else 'Không có bảng nghiệp vụ khác khai báo FK trực tiếp tới bảng này trong schema hiện tại.')
        extra += '\n\n**Sử dụng và lưu ý nghiệp vụ:** ' + TABLE_NOTES[table.name] + '\n\n'
        detail = detail[:end] + extra + detail[end:]
    json_part = source[source.index('### 3.21.'):source.index('### 3.22.')].replace('### 3.21.', '### 5.5.')
    feature_part = source[source.index('### 3.22.'):source.index('## 4. Miền')].replace('### 3.22.', '### 5.1.')
    feature_part += '\nPredictor chọn đúng feature_columns của artifact và lấy xác suất lớp 1. raw_features_json không được tự dùng thay cột dữ liệu đã định nghĩa. Giá trị cuối kỳ final_result không tham gia bộ đầu vào hiện tại.\n\n'
    indexes = ['## 6. Chỉ mục, ràng buộc và tối ưu truy vấn', '', '### 6.1. Index khai báo tường minh trong schema hiện tại', '',
               '| Tên index | Bảng / cột và điều kiện | Mục đích chính |', '| --- | --- | --- |']
    purposes = {
        'student_enrollments': 'Tra enrollment theo sinh viên hoặc đợt mở môn.',
        'student_feature_snapshots': 'Tra snapshot của enrollment và hỗ trợ thứ tự thời gian/UUID; B-tree có thể quét ngược.',
        'prediction_runs': 'Tra lần chạy theo snapshot/thời gian/UUID hoặc model được tham chiếu.',
        'intervention_plans': 'Lọc kế hoạch theo sinh viên/trạng thái hoặc theo dự báo nguồn.',
        'intervention_tasks': 'Đếm/lọc nhiệm vụ theo plan và cờ hoàn thành.',
        'advisor_students': 'Kiểm tra phân công/lọc lớp–năm học và tìm cố vấn theo sinh viên.',
        'course_lecturers': 'Tra giảng viên được phân công học phần.',
        'advising_notes': 'Tra ghi chú theo enrollment hoặc cố vấn.',
        'student_help_requests': 'Tra yêu cầu theo sinh viên hoặc người nhận/trạng thái.',
        'course_presentations': 'Tra mã đợt mở môn.', 'audit_logs': 'Lọc nhật ký theo mã thao tác.',
        'ml_models': 'UNIQUE có điều kiện bảo đảm tối đa một model active.',
    }
    sql = []
    for table in tables:
        for index in sorted(table.indexes, key=lambda i: i.name):
            ddl = str(CreateIndex(index).compile(dialect=dialect))
            condition = index.dialect_options['postgresql'].get('where')
            spec = f'`{table.name}({", ".join(c.name for c in index.columns)})`'
            if condition is not None:
                spec += f'; UNIQUE WHERE `{condition}`'
            indexes.append(f'| `{index.name}` | {spec} | {purposes[table.name]} |')
            sql.append(ddl + ';')
    indexes += ['', 'PK và UNIQUE còn tạo các index hỗ trợ riêng; không tính chúng như index tường minh ở bảng trên. '
                'PostgreSQL không tự tạo index cho mọi FK. Index đơn student_code trùng UNIQUE đã bỏ; các index legacy local '
                'được chuẩn hóa bởi migration, không giữ như những cấu trúc ngoài SQL canonical.', '', '```sql', *sql, '```', '']
    document = '\n\n'.join([
        intro.strip(), SUBSYSTEMS.strip(), catalog.strip(), relations.strip(), detail.strip(),
        '## 5. Đặc trưng ML và luồng dữ liệu\n\n' + feature_part.strip(), FLOW.strip(), json_part.strip(),
        '\n'.join(indexes).strip(), RULES.strip(), OPERATIONS.strip(), COMPARISON.strip(), SCOPE.strip()])
    return document.splitlines() + ['']
