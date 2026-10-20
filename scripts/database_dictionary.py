"""Vietnamese business definitions for the physical database design document."""

TABLES = {
    'users': ('Tài khoản người dùng', 'Lưu thông tin đăng nhập và liên hệ dùng chung cho mọi vai trò. Một tài khoản có thể mang nhiều vai trò và có các hồ sơ chuyên biệt tương ứng.'),
    'roles': ('Danh mục vai trò', 'Danh mục quyền nghiệp vụ ADMIN, ADVISOR, LECTURER và STUDENT; gán cho tài khoản qua user_roles.'),
    'user_roles': ('Gán vai trò cho tài khoản', 'Bảng nối nhiều–nhiều giữa users và roles. Khóa chính ghép ngăn một tài khoản được gán cùng vai trò hai lần.'),
    'student_profiles': ('Hồ sơ sinh viên', 'Thông tin định danh sinh viên và đặc trưng nhân khẩu học theo dữ liệu OULAD. Các mã danh mục cần được ánh xạ rõ khi sử dụng trong bối cảnh HUIT.'),
    'advisor_profiles': ('Hồ sơ cố vấn học tập', 'Thông tin đơn vị và liên hệ công tác của cố vấn; phạm vi sinh viên phụ trách nằm trong advisor_students.'),
    'lecturer_profiles': ('Hồ sơ giảng viên', 'Thông tin giảng viên bộ môn; phạm vi học phần giảng dạy nằm trong course_lecturers.'),
    'courses': ('Danh mục môn học', 'Định nghĩa môn học dùng chung. Một môn có thể được mở nhiều đợt trong course_presentations; mã môn còn được dùng làm đặc trưng đầu vào mô hình.'),
    'course_presentations': ('Đợt mở môn / lớp học phần', 'Một lần tổ chức giảng dạy của môn học, có mã đợt, ngày bắt đầu và thời lượng. Enrollment, phân công giảng viên và hỗ trợ theo môn tham chiếu bản ghi này.'),
    'student_enrollments': ('Đăng ký học phần', 'Liên kết sinh viên với một đợt mở môn; là gốc truy vết snapshot, dự báo và nhiệm vụ theo từng học phần.'),
    'course_lecturers': ('Phân công giảng dạy', 'Bảng nối giảng viên với đợt mở môn, xác định phạm vi truy cập dữ liệu học phần. Một đợt có thể có nhiều giảng viên.'),
    'advisor_students': ('Phân công cố vấn–sinh viên', 'Bảng nối cố vấn với sinh viên, kèm lớp sinh hoạt và năm học. Schema cho phép nhiều cố vấn được phân công một sinh viên; không có UNIQUE chỉ trên student_id.'),
    'student_feature_snapshots': ('Ảnh chụp đặc trưng học tập', 'Lưu 11 chỉ số hành vi tại một mốc quan sát của enrollment. Một đăng ký có nhiều snapshot; snapshot đã dùng trong dự báo không được cập nhật trực tiếp.'),
    'ml_models': ('Đăng ký phiên bản mô hình', 'Lưu vị trí artifact, phiên bản, cấu hình ngưỡng và chỉ số đánh giá. Partial UNIQUE bảo đảm tối đa một model active; registry kiểm tra yêu cầu có đúng một model khi suy luận.'),
    'prediction_runs': ('Lịch sử dự báo nguy cơ', 'Mỗi bản ghi là một lần suy luận của một model trên một snapshot. Một snapshot có thể được dự báo nhiều lần; context lưu đầu vào và danh tính model thực sự đã sử dụng.'),
    'intervention_plans': ('Kế hoạch can thiệp', 'Kế hoạch hỗ trợ sinh viên dựa trên một lần dự báo. Schema cho phép nhiều kế hoạch cùng ACTIVE và nhiều kế hoạch tham chiếu cùng dự báo.'),
    'intervention_tasks': ('Nhiệm vụ can thiệp', 'Các việc cụ thể sinh viên cần hoàn thành trong kế hoạch. Phạm vi môn học được truy ra qua plan → prediction → snapshot → enrollment, không có cột môn học trực tiếp.'),
    'advising_notes': ('Biên bản / ghi chú tư vấn', 'Ghi nhận buổi trao đổi giữa cố vấn và sinh viên trong phạm vi một enrollment, kèm nội dung và hành động đã thống nhất.'),
    'student_help_requests': ('Yêu cầu trợ giúp', 'Yêu cầu do sinh viên gửi đến cố vấn hoặc giảng viên. Người nhận có thể chưa được gán; presentation_id cho biết phạm vi học phần nếu có.'),
    'audit_logs': ('Nhật ký thao tác hệ thống', 'Ghi nhận người thực hiện, loại thao tác và đối tượng liên quan. target_type/target_id là tham chiếu nghiệp vụ đa hình, không phải khóa ngoại đến một bảng cố định.'),
}

COMMON = {
    'created_at': 'Thời điểm tạo bản ghi, lưu kèm múi giờ; mặc định theo đồng hồ PostgreSQL.',
    'updated_at': 'Thời điểm cập nhật gần nhất. ORM tự cập nhật khi sửa; SQL trực tiếp phải tự gán nếu cần, vì chưa có trigger cập nhật chung.',
    'assigned_at': 'Thời điểm tạo phân công, lưu kèm múi giờ.',
}

FIELDS = {
    'users': {
        'email': 'Địa chỉ email đăng nhập và liên hệ; duy nhất trong hệ thống.',
        'hashed_password': 'Chuỗi băm mật khẩu, không phải mật khẩu dạng rõ; dùng xác minh khi đăng nhập.',
        'full_name': 'Họ tên hiển thị của người dùng.',
        'avatar_url': 'Đường dẫn hoặc URL ảnh đại diện; NULL khi chưa khai báo.',
        'phone_number': 'Số điện thoại liên hệ; lưu chuỗi để giữ số 0 đầu và mã quốc gia.',
        'is_active': 'Trạng thái tài khoản: true cho phép hoạt động, false bị khóa; dịch vụ xác thực kiểm tra khi sử dụng token.',
    },
    'roles': {
        'id': 'Mã số vai trò tự tăng bằng sequence SMALLSERIAL; là khóa chính kiểu SMALLINT.',
        'code': 'Mã vai trò duy nhất, hiện sử dụng ADMIN, ADVISOR, LECTURER, STUDENT. Đây là danh mục seed, không phải CHECK giới hạn bốn giá trị.',
        'name': 'Tên vai trò hiển thị bằng ngôn ngữ nghiệp vụ.',
        'description': 'Mô tả phạm vi và trách nhiệm của vai trò.',
    },
    'user_roles': {
        'user_id': 'Tài khoản được gán vai trò; thành phần thứ nhất của khóa chính ghép.',
        'role_id': 'Vai trò được gán; thành phần thứ hai của khóa chính ghép.',
    },
    'student_profiles': {
        'user_id': 'Tài khoản sở hữu hồ sơ sinh viên; UNIQUE bảo đảm tối đa một hồ sơ sinh viên cho mỗi tài khoản.',
        'student_code': 'Mã số sinh viên duy nhất; có thể dùng làm định danh đăng nhập thay email theo API hiện tại.',
        'gender': 'Mã giới tính theo OULAD: M hoặc F; không tự diễn giải các nhóm ngoài danh mục mô hình.',
        'highest_education': 'Nhóm trình độ học vấn cao nhất trước khóa học theo danh mục OULAD; là một đầu vào mô hình.',
        'age_band': 'Nhóm tuổi OULAD: 0-35, 35-55, 55<=; giữ nguyên chuỗi mã của dữ liệu nguồn.',
        'imd_band': 'Nhóm chỉ số thiếu hụt kinh tế–xã hội IMD của dữ liệu OULAD; không phải thu nhập cá nhân. Không nằm trong 17 đầu vào hiện tại.',
        'region': 'Khu vực địa lý của sinh viên theo dữ liệu nguồn; không nằm trong 17 đầu vào hiện tại.',
        'disability': 'Cờ khai báo khuyết tật theo dữ liệu nguồn: N hoặc Y; không nằm trong 17 đầu vào hiện tại.',
    },
    'advisor_profiles': {
        'user_id': 'Tài khoản sở hữu hồ sơ cố vấn; UNIQUE bảo đảm tối đa một hồ sơ cố vấn cho mỗi tài khoản.',
        'department': 'Khoa, bộ môn hoặc đơn vị công tác của cố vấn.',
        'office_location': 'Phòng hoặc địa điểm làm việc để liên hệ tư vấn.',
        'lms_api_key': 'Khóa tích hợp LMS nếu được cấu hình. Cột tồn tại không đồng nghĩa hệ thống đã triển khai đồng bộ LMS; không đưa giá trị thật vào báo cáo.',
    },
    'lecturer_profiles': {
        'user_id': 'Tài khoản sở hữu hồ sơ giảng viên; UNIQUE bảo đảm tối đa một hồ sơ giảng viên cho mỗi tài khoản.',
        'lecturer_code': 'Mã giảng viên duy nhất trong hệ thống.',
        'department': 'Khoa, bộ môn hoặc đơn vị công tác của giảng viên.',
        'academic_rank': 'Chức danh/học hàm mô tả của giảng viên; mặc định Giảng viên, không phải danh mục ENUM tại database.',
    },
    'courses': {
        'code_module': 'Mã môn học duy nhất; với artifact hiện tại cần thuộc danh mục OULAD được schema suy luận hỗ trợ.',
        'name': 'Tên đầy đủ của môn học.',
        'credits_default': 'Số tín chỉ mặc định của môn, phải dương. Đơn vị nguồn OULAD cần được quy đổi rõ nếu áp dụng cho tín chỉ HUIT.',
        'description': 'Mô tả nội dung hoặc thông tin bổ sung về môn học.',
    },
    'course_presentations': {
        'course_id': 'Môn học được tổ chức trong đợt này.',
        'code_presentation': 'Mã đợt mở môn, ví dụ 2013J; duy nhất trong cùng môn theo UNIQUE ghép, không duy nhất toàn hệ thống.',
        'start_date': 'Ngày bắt đầu đợt học; có thể chưa xác định. Là mốc diễn giải các ngày tương đối trong dữ liệu học tập.',
        'module_presentation_length': 'Thời lượng đợt học tính bằng ngày, phải lớn hơn 0; phục vụ diễn giải mốc cutoff.',
    },
    'student_enrollments': {
        'student_id': 'Sinh viên đăng ký học; không thể trùng cặp với presentation_id.',
        'presentation_id': 'Đợt mở môn mà sinh viên theo học; không phải ID danh mục môn courses.',
        'date_registration': 'Ngày đăng ký tương đối so với ngày bắt đầu đợt học; số âm là đăng ký trước ngày bắt đầu, mặc định -10. Là đầu vào mô hình.',
        'date_unregistration': 'Ngày rút/hủy đăng ký tương đối so với đầu đợt học; NULL khi chưa có thông tin rút học, không tự coi là đã hoàn thành.',
        'studied_credits': 'Tổng tải tín chỉ đang học theo định nghĩa đặc trưng OULAD, phải dương; không mặc định đồng nhất với credits_default của riêng môn. Là đầu vào mô hình.',
        'num_of_prev_attempts': 'Số lần đã học/thử môn trước lần đăng ký này, số nguyên không âm; không nằm trong 17 đầu vào hiện tại.',
        'final_result': 'Kết quả cuối kỳ: PASS/FAIL/WITHDRAWN/DISTINCTION hoặc dạng nhãn gốc Pass/Fail/Withdrawn/Distinction. NULL khi chưa biết; không dùng làm đầu vào dự báo.',
    },
    'course_lecturers': {
        'lecturer_id': 'Giảng viên được phân công giảng dạy.',
        'presentation_id': 'Đợt mở môn thuộc phạm vi giảng dạy của giảng viên.',
        'role_in_course': 'Vai trò trong học phần, mặc định GIANG_VIEN_CHINH; database chưa CHECK danh mục vai trò này.',
    },
    'advisor_students': {
        'advisor_id': 'Cố vấn được giao theo dõi sinh viên.',
        'student_id': 'Sinh viên thuộc phạm vi phụ trách của cố vấn.',
        'academic_year': 'Nhãn năm học của phân công, ví dụ 2026-2027; không phải kiểu DATE và không thuộc UNIQUE ghép hiện tại.',
        'class_name': 'Tên/mã lớp sinh hoạt của sinh viên trong phân công; dùng lọc danh sách và tổng hợp thống kê lớp.',
    },
    'student_feature_snapshots': {
        'enrollment_id': 'Đăng ký học phần mà các chỉ số trong snapshot mô tả.',
        'cutoff_stage': 'Mã mốc quan sát, mặc định CUTOFF_75. Dịch vụ batch hiện chỉ chấp nhận mốc này; database chưa CHECK chỉ cho phép một mã.',
        'total_clicks_to_t': 'Tổng lượt click/tương tác VLE ghi nhận từ đầu đợt học đến mốc quan sát t; đơn vị lượt, không âm.',
        'clicks_resource_to_t': 'Lượt click vào loại tài nguyên resource đến t; đơn vị lượt, không âm.',
        'clicks_url_to_t': 'Lượt click vào loại tài nguyên URL/liên kết đến t; đơn vị lượt, không âm.',
        'active_days_to_t': 'Số ngày khác nhau có hoạt động học tập đến t; đơn vị ngày, không âm.',
        'active_day_ratio': 'Tỷ lệ ngày hoạt động trong khoảng quan sát theo quy trình trích xuất; lưu từ 0 đến 1, không lưu phần trăm 0–100. Database không tự tính tỷ lệ.',
        'days_since_last_activity': 'Số ngày từ lần hoạt động gần nhất tới mốc quan sát t; đơn vị ngày, không âm.',
        'clicks_recent_7': 'Lượt click trong cửa sổ 7 ngày gần mốc quan sát t theo dữ liệu nguồn; không phải 7 ngày trước thời điểm đọc API.',
        'clicks_recent_30': 'Lượt click trong cửa sổ 30 ngày gần mốc quan sát t theo dữ liệu nguồn; đơn vị lượt, không âm.',
        'assessments_submitted_to_t': 'Số bài đánh giá đã nộp tính đến t theo dữ liệu nguồn; đơn vị bài, không âm.',
        'late_submissions_to_t': 'Số bài nộp trễ hạn tính đến t theo dữ liệu nguồn; đơn vị bài, không âm.',
        'submission_rate': 'Tỷ lệ nộp/hoàn thành bài đánh giá theo quy trình trích xuất tại t; lưu 0–1. Mẫu số/phạm vi bài phải được nguồn ETL định nghĩa, database không tự suy ra.',
        'raw_features_json': 'Dữ liệu/metadata mở rộng của snapshot. Cập nhật từ giảng viên ghi snapshot_metadata gồm source, previous_snapshot_id, observed_at và updated_by_user_id; các ID trong JSON không phải FK.',
        'created_at': 'Thời điểm ghi snapshot vào database; không tự đồng nghĩa thời điểm quan sát nghiệp vụ. Kết quả hiện hành chọn created_at DESC rồi id DESC.',
    },
    'ml_models': {
        'model_name': 'Tên hiển thị/nhóm thuật toán của mô hình.',
        'version': 'Chuỗi phiên bản mô hình duy nhất trong registry, ví dụ v1.0.0-cutoff75.',
        'model_file_path': 'Đường dẫn artifact mô hình mà backend có thể nạp; không chứa byte artifact trong database.',
        'threshold': 'Ngưỡng quyết định nhãn nguy cơ theo hợp đồng suy luận, trong [0,1]; provenance của từng lần chạy giữ ngưỡng thực tế đã dùng.',
        'cutoff_fraction': 'Tỷ phần thời lượng quan sát của mô hình, trong (0,1]; 0.75 biểu diễn mốc 75%.',
        'accuracy': 'Tỷ lệ phân loại đúng trên tập đánh giá được ghi trong nguồn/metadata; NULL khi chưa có số liệu. Không tự suy ra đây là kết quả test độc lập.',
        'average_precision': 'Average precision (AP) của lớp nguy cơ; độc lập ROC-AUC và không mặc định bằng diện tích PR tính theo mọi cách tích phân. NULL khi chưa có số liệu.',
        'roc_auc': 'Diện tích dưới đường ROC trên tập đánh giá đã xác định; NULL khi nguồn không cung cấp. Không điền AP thay thế.',
        'is_active': 'true khi phiên bản đang được chọn cho suy luận; partial UNIQUE chỉ cho tối đa một dòng true, mặc định false khi thêm model.',
        'metadata_json': 'Metadata mở rộng như thuật toán, nguồn metric, hợp đồng đặc trưng và thông tin runtime đã xác minh; không thay thế provenance bất biến trong từng prediction_run.',
    },
    'prediction_runs': {
        'snapshot_id': 'Snapshot đầu vào của lần suy luận; RESTRICT giữ snapshot khi có dự báo tham chiếu.',
        'model_id': 'Phiên bản registry đã thực hiện suy luận; RESTRICT không cho xóa model đang có lịch sử.',
        'prediction_label': 'Nhãn đã lưu: 1 là nguy cơ, 0 là an toàn theo mô hình/ngưỡng của lần chạy. Giao diện dùng nhãn này, không phân loại lại bằng ngưỡng cố định 0.5.',
        'risk_probability': 'Xác suất thuộc lớp nguy cơ (positive label 1), trong [0,1]; không phải xác suất của nhãn bất kỳ được chọn.',
        'inference_context': 'Provenance JSONB: đủ 17 đầu vào thực tế, model_version, threshold, model_sha256 và các thông tin danh tính đi kèm. NULL đánh dấu lịch sử cũ chưa đủ dữ liệu xác minh; không backfill bằng hồ sơ hiện tại.',
        'execution_time_ms': 'Thời gian thực hiện suy luận tính bằng mili giây, không âm; NULL khi lần chạy không ghi thời gian.',
        'triggered_by_user_id': 'Tài khoản kích hoạt suy luận nếu có; NULL khi không xác định hoặc tài khoản bị xóa theo SET NULL.',
        'created_at': 'Thời điểm lưu lần dự báo; dùng created_at DESC, id DESC để chọn lần chạy mới nhất của snapshot hiện hành.',
    },
    'intervention_plans': {
        'prediction_run_id': 'Lần dự báo làm căn cứ lập kế hoạch; truy ra học phần qua snapshot và enrollment.',
        'student_id': 'Sinh viên nhận can thiệp. API/service phải xác minh trùng sinh viên trong enrollment của dự báo; hai FK độc lập chưa bảo đảm điều này tại DB.',
        'status': 'Trạng thái kế hoạch: ACTIVE đang thực hiện, COMPLETED hoàn tất, CANCELLED đã hủy; mặc định ACTIVE.',
        'target_completion_date': 'Ngày dự kiến hoàn thành kế hoạch; NULL khi chưa đặt hạn.',
        'advisor_note_summary': 'Tóm tắt nhận định hoặc định hướng can thiệp của người lập kế hoạch.',
    },
    'intervention_tasks': {
        'plan_id': 'Kế hoạch chứa nhiệm vụ; mỗi nhiệm vụ thuộc đúng một kế hoạch.',
        'category': 'Nhóm nhiệm vụ, ví dụ CHUYEN_CAN, HOC_THUAT, TIEN_DO, TAM_LY; database chưa CHECK danh mục này.',
        'priority': 'Mức ưu tiên HIGH/MEDIUM/LOW; mặc định MEDIUM.',
        'title': 'Tiêu đề ngắn gọn của nhiệm vụ.',
        'description': 'Hướng dẫn chi tiết về việc sinh viên cần thực hiện.',
        'target_metric': 'Mục tiêu/chỉ tiêu hoàn thành dạng văn bản; không phải giá trị số tự đo hoặc công thức do DB tính.',
        'is_completed': 'Cờ hoàn thành nhiệm vụ; false khi chưa hoàn thành, true khi đã hoàn thành.',
        'completed_at': 'Thời điểm hoàn thành nếu có. Database chưa có CHECK ràng buộc tương đương giữa trường này và is_completed.',
        'student_feedback': 'Phản hồi của sinh viên về việc thực hiện nhiệm vụ.',
    },
    'advising_notes': {
        'enrollment_id': 'Đăng ký học phần được trao đổi trong buổi tư vấn; từ đó xác định sinh viên và đợt học.',
        'advisor_id': 'Cố vấn ghi biên bản; API kiểm tra sinh viên thuộc phạm vi được phân công.',
        'meeting_date': 'Ngày diễn ra buổi trao đổi; mặc định ngày hiện tại của database nếu INSERT không truyền giá trị.',
        'meeting_type': 'Hình thức trao đổi như ONLINE/IN_PERSON/EMAIL; mặc định ONLINE, database chưa CHECK danh mục.',
        'content': 'Nội dung nhận xét và trao đổi của buổi tư vấn.',
        'agreed_actions': 'Các hành động đã thống nhất sau tư vấn; là văn bản, không tự sinh nhiệm vụ can thiệp.',
    },
    'student_help_requests': {
        'student_id': 'Sinh viên tạo yêu cầu trợ giúp.',
        'target_role': 'Nhóm người nhận mong muốn: ADVISOR hoặc LECTURER.',
        'target_user_id': 'Tài khoản nhận xử lý cụ thể; NULL khi chưa phân công hoặc người nhận bị xóa. Service xác minh vai trò, trạng thái và phân công.',
        'presentation_id': 'Đợt mở môn liên quan; NULL biểu diễn yêu cầu không gắn môn hoặc học phần bị xóa theo SET NULL. Yêu cầu tới giảng viên được service yêu cầu gắn học phần hợp lệ.',
        'subject': 'Tiêu đề yêu cầu hỗ trợ.',
        'content': 'Nội dung khó khăn/vấn đề cần trợ giúp.',
        'status': 'PENDING chờ xử lý, IN_PROGRESS đang xử lý, RESOLVED đã giải quyết; mặc định PENDING.',
        'response_note': 'Nội dung phản hồi hoặc kết quả xử lý của người phụ trách.',
    },
    'audit_logs': {
        'user_id': 'Tài khoản thực hiện thao tác nếu xác định được; SET NULL giữ log khi tài khoản bị xóa.',
        'action': 'Mã thao tác nghiệp vụ được ứng dụng ghi, dùng tra cứu/lọc nhật ký; không có CHECK danh mục mã.',
        'target_type': 'Tên loại đối tượng được tác động, diễn giải cùng target_id; không phải tên bảng được DB kiểm chứng.',
        'target_id': 'UUID đối tượng nghiệp vụ được tác động; không có FK vì có thể trỏ tới nhiều loại đối tượng.',
        'detail': 'Mô tả bổ sung về thao tác/kết quả; lưu TEXT, không bắt buộc JSON hợp lệ.',
        'ip_address': 'Địa chỉ IP dưới dạng chuỗi do ứng dụng cung cấp; không phải kiểu PostgreSQL INET.',
    },
}


def meaning(table, column):
    if column in FIELDS.get(table, {}):
        return FIELDS[table][column]
    if column == 'id':
        return f'Định danh UUID duy nhất của bản ghi {TABLES[table][0].lower()}; sinh tự động khi không được cung cấp.'
    if column in COMMON:
        return COMMON[column]
    raise ValueError(f'Missing business definition: {table}.{column}')
