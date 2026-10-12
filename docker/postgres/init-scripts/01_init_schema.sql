-- ==============================================================================
-- KHOA LUAN TOT NGHIEP KLTN 13 - TRUONG DAI HOC CONG THUONG TP.HCM (HUIT)
-- HE THONG GOI Y CHIEN LUOC HOC TAP CA NHAN HOA
-- KICH BAN KHOI TAO SCHEMA CO SO DU LIEU: personalized_learning_db
-- ==============================================================================

-- 0. KICH HOAT EXTENSIONS CAN THIET
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. PHAN HE XAC THUC & PHAN QUYEN NGUOI DUNG (AUTH & IDENTITY)
-- ==============================================================================

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

CREATE TABLE IF NOT EXISTS roles (
    id SMALLSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

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

CREATE TABLE IF NOT EXISTS advisor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(150) NOT NULL,
    office_location VARCHAR(255),
    lms_api_key VARCHAR(255)
);

-- ==============================================================================
-- 2. PHAN HE HOC PHAN & DAO TAO (ACADEMIC & COURSES - CHUAN OULAD)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_module VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    credits_default INT NOT NULL DEFAULT 30,
    description TEXT
);

CREATE TABLE IF NOT EXISTS course_presentations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    code_presentation VARCHAR(20) NOT NULL,
    start_date DATE,
    module_presentation_length INT NOT NULL DEFAULT 260,
    CONSTRAINT uq_course_presentation UNIQUE (course_id, code_presentation)
);

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

-- ==============================================================================
-- 3. PHAN HE DAC TRUNG HANH VI HOC TAP (FEATURE SNAPSHOTS - OULAD 17 FEATURES)
-- ==============================================================================

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

-- ==============================================================================
-- 4. PHAN HE DU BAO HOC MAY & GIAM SAT MO HINH (ML MODELS & PREDICTIONS)
-- ==============================================================================

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

-- ==============================================================================
-- 5. PHAN HE KE HOACH CAN THIEP & CO VAN (INTERVENTIONS & ADVISING)
-- ==============================================================================

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

-- ==============================================================================
-- 6. BANG MO RONG PHAN HE 4 VA!! VAI TRO (LECTURER / ADVISOR / HELP REQUESTS / AUDIT)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS lecturer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lecturer_code VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(150) NOT NULL,
    academic_rank VARCHAR(50) DEFAULT 'Giảng viên',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS course_lecturers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lecturer_id UUID NOT NULL REFERENCES lecturer_profiles(id) ON DELETE CASCADE,
    presentation_id UUID NOT NULL REFERENCES course_presentations(id) ON DELETE CASCADE,
    role_in_course VARCHAR(50) NOT NULL DEFAULT 'GIANG_VIEN_CHINH',
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_lecturer_presentation UNIQUE (lecturer_id, presentation_id)
);

CREATE TABLE IF NOT EXISTS advisor_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_id UUID NOT NULL REFERENCES advisor_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
    academic_year VARCHAR(20) NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_advisor_student UNIQUE (advisor_id, student_id)
);

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

-- ==============================================================================
-- 7. THIET LAP CHI MUC & TOI UU HOA TRUY VAN (INDEXES)
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_student_profiles_code ON student_profiles(student_code);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON student_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_presentation ON student_enrollments(presentation_id);

CREATE INDEX IF NOT EXISTS idx_feature_snapshots_enrollment ON student_feature_snapshots(enrollment_id, cutoff_stage);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at_desc ON prediction_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_snapshot ON prediction_runs(snapshot_id);

CREATE INDEX IF NOT EXISTS idx_intervention_plans_student ON intervention_plans(student_id, status);
CREATE INDEX IF NOT EXISTS idx_intervention_tasks_plan_status ON intervention_tasks(plan_id, is_completed);
