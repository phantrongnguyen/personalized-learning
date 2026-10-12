-- ==============================================================================
-- KHOA LUAN TOT NGHIEP KLTN 13 - TRUONG DAI HOC CONG THUONG TP.HCM (HUIT)
-- HE THONG GOI Y CHIEN LUOC HOC TAP CA NHAN HOA
-- KICH BAN NAP DU LIEU KHOI TAO BAN DAU (SEED DATA)
-- ==============================================================================

-- 1. CHEN DANH MUC VAI TRO MAC DINH (ROLES)
INSERT INTO roles (code, name, description) VALUES
    ('ADMIN', 'Quản trị viên', 'Toàn quyền cấu hình hệ thống, quản lý người dùng và giám sát mô hình ML'),
    ('ADVISOR', 'Cố vấn học tập', 'Theo dõi nguy cơ học tập của sinh viên, xem cảnh báo sớm và kê đơn can thiệp'),
    ('LECTURER', 'Giảng viên bộ môn', 'Theo dõi tình hình tương tác học phần và ghi nhận tiến độ học tập'),
    ('STUDENT', 'Sinh viên', 'Tra cứu dự báo nguy cơ cá nhân và theo dõi nhiệm vụ can thiệp')
ON CONFLICT (code) DO NOTHING;

-- 2. CHEN TAI KHOAN QUAN TRI HE THONG MAC DINH (ADMIN DEFAULT ACCOUNT)
-- Mat khau mac dinh la: admin_password_123 (duoc hash bang thuat toan blowfish/bcrypt qua pgcrypto)
DO $$
DECLARE
    admin_user_id UUID;
    admin_role_id SMALLINT;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE code = 'ADMIN';

    IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@huit.edu.vn') THEN
        INSERT INTO users (
            id,
            email,
            hashed_password,
            full_name,
            phone_number,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            'admin@huit.edu.vn',
            crypt('admin_password_123', gen_salt('bf', 10)),
            'Quản trị viên Hệ thống KLTN 13',
            '0901234567',
            TRUE,
            NOW(),
            NOW()
        ) RETURNING id INTO admin_user_id;

        INSERT INTO user_roles (user_id, role_id)
        VALUES (admin_user_id, admin_role_id)
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- 3. CHEN MO HINH MACHINE LEARNING MAC DINH (LIGHTGBM + HCO-VNLS CUTOFF 75%)
INSERT INTO ml_models (
    id,
    model_name,
    version,
    model_file_path,
    threshold,
    cutoff_fraction,
    accuracy,
    roc_auc,
    is_active,
    metadata_json,
    created_at
) VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'HCO-VNLS + LightGBM 80 cây — cutoff 75%',
    'v1.0.0-cutoff75',
    'artifacts/model_hco_vnls_lightgbm_cutoff75.joblib',
    0.5,
    0.75,
    0.8741,
    0.8968,
    TRUE,
    '{
        "description": "Mô hình phân loại nguy cơ học tập sinh viên tại mốc Cutoff 75% thời lượng học phần OULAD",
        "algorithm": "LightGBM + Tối ưu hóa siêu tham số lai ghép HCO-VNLS",
        "positive_label": 1,
        "features_count": 17
    }'::jsonb,
    NOW()
) ON CONFLICT (version) DO NOTHING;

-- 4. CHEN DU LIEU DANH MUC HOC PHAN OULAD MAU (COURSES & PRESENTATIONS)
INSERT INTO courses (id, code_module, name, credits_default, description) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'AAA', 'Discovering Arts and Humanities', 30, 'Học phần cơ sở OULAD nhóm ngành Nhân văn'),
    ('c0000000-0000-0000-0000-000000000002', 'BBB', 'Introduction to the Social Sciences', 30, 'Học phần cơ sở OULAD nhóm ngành Khoa học Xã hội'),
    ('c0000000-0000-0000-0000-000000000003', 'DDD', 'Exploring Science and Technology', 30, 'Học phần cơ sở OULAD nhóm ngành Khoa học Tự nhiên & Công nghệ')
ON CONFLICT (code_module) DO NOTHING;

INSERT INTO course_presentations (id, course_id, code_presentation, start_date, module_presentation_length) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', '2013J', '2013-10-01', 268),
    ('b0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', '2014J', '2014-10-01', 269),
    ('b0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000002', '2013J', '2013-10-01', 268),
    ('b0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000003', '2013J', '2013-10-01', 261)
ON CONFLICT (course_id, code_presentation) DO NOTHING;
