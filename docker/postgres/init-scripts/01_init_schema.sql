-- Canonical schema; migrations are required for existing databases.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS courses (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	code_module VARCHAR(20) NOT NULL,
	name VARCHAR(255) NOT NULL,
	credits_default INTEGER DEFAULT 30 NOT NULL,
	description TEXT,
	PRIMARY KEY (id),
	CONSTRAINT courses_code_module_key UNIQUE (code_module),
	CONSTRAINT courses_credits_default_check CHECK (credits_default > 0)
);

CREATE TABLE IF NOT EXISTS ml_models (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	model_name VARCHAR(150) NOT NULL,
	version VARCHAR(30) NOT NULL,
	model_file_path VARCHAR(500) NOT NULL,
	threshold FLOAT DEFAULT 0.5 NOT NULL,
	cutoff_fraction FLOAT DEFAULT 0.75 NOT NULL,
	accuracy FLOAT,
	average_precision FLOAT,
	roc_auc FLOAT,
	is_active BOOLEAN DEFAULT false NOT NULL,
	metadata_json JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ml_models_threshold_check CHECK (threshold >= 0 AND threshold <= 1),
	CONSTRAINT ml_models_accuracy_check CHECK (accuracy >= 0 AND accuracy <= 1),
	CONSTRAINT ml_models_roc_auc_check CHECK (roc_auc >= 0 AND roc_auc <= 1),
	CONSTRAINT ml_models_average_precision_check CHECK (average_precision >= 0 AND average_precision <= 1),
	CONSTRAINT ml_models_cutoff_fraction_check CHECK (cutoff_fraction > 0 AND cutoff_fraction <= 1),
	CONSTRAINT ml_models_version_key UNIQUE (version)
);

CREATE TABLE IF NOT EXISTS roles (
	id SMALLSERIAL NOT NULL,
	code VARCHAR(50) NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	PRIMARY KEY (id),
	CONSTRAINT roles_code_key UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS users (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	email VARCHAR(255) NOT NULL,
	hashed_password VARCHAR(255) NOT NULL,
	full_name VARCHAR(150) NOT NULL,
	avatar_url VARCHAR(500),
	phone_number VARCHAR(20),
	is_active BOOLEAN DEFAULT true NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT users_email_key UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS advisor_profiles (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	user_id UUID NOT NULL,
	department VARCHAR(150) NOT NULL,
	office_location VARCHAR(255),
	lms_api_key VARCHAR(255),
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS audit_logs (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	user_id UUID,
	action VARCHAR(100) NOT NULL,
	target_type VARCHAR(50),
	target_id UUID,
	detail TEXT,
	ip_address VARCHAR(50),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS course_presentations (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	course_id UUID NOT NULL,
	code_presentation VARCHAR(20) NOT NULL,
	start_date DATE,
	module_presentation_length INTEGER DEFAULT 260 NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE RESTRICT,
	CONSTRAINT course_presentations_module_presentation_length_check CHECK (module_presentation_length > 0),
	CONSTRAINT uq_course_presentation UNIQUE (course_id, code_presentation)
);

CREATE TABLE IF NOT EXISTS lecturer_profiles (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	user_id UUID NOT NULL,
	lecturer_code VARCHAR(50) NOT NULL,
	department VARCHAR(150) NOT NULL,
	academic_rank VARCHAR(50) DEFAULT 'Giảng viên' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
	CONSTRAINT lecturer_profiles_lecturer_code_key UNIQUE (lecturer_code)
);

CREATE TABLE IF NOT EXISTS student_profiles (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	user_id UUID NOT NULL,
	student_code VARCHAR(50) NOT NULL,
	gender VARCHAR(10) NOT NULL,
	highest_education VARCHAR(100) NOT NULL,
	age_band VARCHAR(20) NOT NULL,
	imd_band VARCHAR(50),
	region VARCHAR(100),
	disability VARCHAR(10) DEFAULT 'N' NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT,
	CONSTRAINT student_profiles_student_code_key UNIQUE (student_code),
	CONSTRAINT student_profiles_gender_check CHECK (gender IN ('M', 'F')),
	CONSTRAINT student_profiles_age_band_check CHECK (age_band IN ('0-35', '35-55', '55<=')),
	CONSTRAINT student_profiles_disability_check CHECK (disability IN ('N', 'Y'))
);

CREATE TABLE IF NOT EXISTS user_roles (
	user_id UUID NOT NULL,
	role_id SMALLINT NOT NULL,
	PRIMARY KEY (user_id, role_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS advisor_students (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	advisor_id UUID NOT NULL,
	student_id UUID NOT NULL,
	academic_year VARCHAR(20) NOT NULL,
	class_name VARCHAR(100) NOT NULL,
	assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_advisor_student UNIQUE (advisor_id, student_id),
	FOREIGN KEY(advisor_id) REFERENCES advisor_profiles (id) ON DELETE CASCADE,
	FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS course_lecturers (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	lecturer_id UUID NOT NULL,
	presentation_id UUID NOT NULL,
	role_in_course VARCHAR(50) DEFAULT 'GIANG_VIEN_CHINH' NOT NULL,
	assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_lecturer_presentation UNIQUE (lecturer_id, presentation_id),
	FOREIGN KEY(lecturer_id) REFERENCES lecturer_profiles (id) ON DELETE CASCADE,
	FOREIGN KEY(presentation_id) REFERENCES course_presentations (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS student_enrollments (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	student_id UUID NOT NULL,
	presentation_id UUID NOT NULL,
	date_registration INTEGER DEFAULT -10 NOT NULL,
	date_unregistration INTEGER,
	studied_credits INTEGER DEFAULT 60 NOT NULL,
	num_of_prev_attempts INTEGER DEFAULT 0 NOT NULL,
	final_result VARCHAR(20),
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE RESTRICT,
	FOREIGN KEY(presentation_id) REFERENCES course_presentations (id) ON DELETE RESTRICT,
	CONSTRAINT student_enrollments_studied_credits_check CHECK (studied_credits > 0),
	CONSTRAINT student_enrollments_num_of_prev_attempts_check CHECK (num_of_prev_attempts >= 0),
	CONSTRAINT student_enrollments_final_result_check CHECK (final_result IN ('PASS', 'FAIL', 'WITHDRAWN', 'DISTINCTION', 'Pass', 'Fail', 'Withdrawn', 'Distinction')),
	CONSTRAINT uq_student_presentation UNIQUE (student_id, presentation_id)
);

CREATE TABLE IF NOT EXISTS student_help_requests (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	student_id UUID NOT NULL,
	target_role VARCHAR(20) NOT NULL,
	target_user_id UUID,
	presentation_id UUID,
	subject VARCHAR(255) NOT NULL,
	content TEXT NOT NULL,
	status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
	response_note TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE RESTRICT,
	FOREIGN KEY(target_user_id) REFERENCES users (id) ON DELETE SET NULL,
	FOREIGN KEY(presentation_id) REFERENCES course_presentations (id) ON DELETE SET NULL,
	CONSTRAINT student_help_requests_target_role_check CHECK (target_role IN ('ADVISOR', 'LECTURER')),
	CONSTRAINT student_help_requests_status_check CHECK (status IN ('PENDING', 'IN_PROGRESS', 'RESOLVED'))
);

CREATE TABLE IF NOT EXISTS advising_notes (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	enrollment_id UUID NOT NULL,
	advisor_id UUID NOT NULL,
	meeting_date DATE DEFAULT CURRENT_DATE NOT NULL,
	meeting_type VARCHAR(50) DEFAULT 'ONLINE' NOT NULL,
	content TEXT NOT NULL,
	agreed_actions TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(enrollment_id) REFERENCES student_enrollments (id) ON DELETE RESTRICT,
	FOREIGN KEY(advisor_id) REFERENCES advisor_profiles (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS student_feature_snapshots (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	enrollment_id UUID NOT NULL,
	cutoff_stage VARCHAR(30) DEFAULT 'CUTOFF_75' NOT NULL,
	total_clicks_to_t INTEGER DEFAULT 0 NOT NULL,
	clicks_resource_to_t INTEGER DEFAULT 0 NOT NULL,
	clicks_url_to_t INTEGER DEFAULT 0 NOT NULL,
	active_days_to_t INTEGER DEFAULT 0 NOT NULL,
	active_day_ratio FLOAT DEFAULT 0.0 NOT NULL,
	days_since_last_activity INTEGER DEFAULT 0 NOT NULL,
	clicks_recent_7 INTEGER DEFAULT 0 NOT NULL,
	clicks_recent_30 INTEGER DEFAULT 0 NOT NULL,
	assessments_submitted_to_t INTEGER DEFAULT 0 NOT NULL,
	late_submissions_to_t INTEGER DEFAULT 0 NOT NULL,
	submission_rate FLOAT DEFAULT 0.0 NOT NULL,
	raw_features_json JSONB,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(enrollment_id) REFERENCES student_enrollments (id) ON DELETE RESTRICT,
	CONSTRAINT student_feature_snapshots_total_clicks_to_t_check CHECK (total_clicks_to_t >= 0),
	CONSTRAINT student_feature_snapshots_clicks_resource_to_t_check CHECK (clicks_resource_to_t >= 0),
	CONSTRAINT student_feature_snapshots_clicks_url_to_t_check CHECK (clicks_url_to_t >= 0),
	CONSTRAINT student_feature_snapshots_active_days_to_t_check CHECK (active_days_to_t >= 0),
	CONSTRAINT student_feature_snapshots_days_since_last_activity_check CHECK (days_since_last_activity >= 0),
	CONSTRAINT student_feature_snapshots_clicks_recent_7_check CHECK (clicks_recent_7 >= 0),
	CONSTRAINT student_feature_snapshots_clicks_recent_30_check CHECK (clicks_recent_30 >= 0),
	CONSTRAINT student_feature_snapshots_assessments_submitted_to_t_check CHECK (assessments_submitted_to_t >= 0),
	CONSTRAINT student_feature_snapshots_late_submissions_to_t_check CHECK (late_submissions_to_t >= 0),
	CONSTRAINT student_feature_snapshots_active_day_ratio_check CHECK (active_day_ratio >= 0 AND active_day_ratio <= 1),
	CONSTRAINT student_feature_snapshots_submission_rate_check CHECK (submission_rate >= 0 AND submission_rate <= 1)
);

CREATE TABLE IF NOT EXISTS prediction_runs (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	snapshot_id UUID NOT NULL,
	model_id UUID NOT NULL,
	prediction_label SMALLINT NOT NULL,
	risk_probability FLOAT NOT NULL,
	inference_context JSONB,
	execution_time_ms INTEGER,
	triggered_by_user_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(snapshot_id) REFERENCES student_feature_snapshots (id) ON DELETE RESTRICT,
	FOREIGN KEY(model_id) REFERENCES ml_models (id) ON DELETE RESTRICT,
	FOREIGN KEY(triggered_by_user_id) REFERENCES users (id) ON DELETE SET NULL,
	CONSTRAINT prediction_runs_prediction_label_check CHECK (prediction_label IN (0, 1)),
	CONSTRAINT prediction_runs_risk_probability_check CHECK (risk_probability >= 0 AND risk_probability <= 1),
	CONSTRAINT prediction_runs_execution_time_ms_check CHECK (execution_time_ms >= 0)
);

CREATE TABLE IF NOT EXISTS intervention_plans (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	prediction_run_id UUID NOT NULL,
	student_id UUID NOT NULL,
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL,
	target_completion_date DATE,
	advisor_note_summary TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(prediction_run_id) REFERENCES prediction_runs (id) ON DELETE RESTRICT,
	FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE RESTRICT,
	CONSTRAINT intervention_plans_status_check CHECK (status IN ('ACTIVE', 'COMPLETED', 'CANCELLED'))
);

CREATE TABLE IF NOT EXISTS intervention_tasks (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	plan_id UUID NOT NULL,
	category VARCHAR(50) NOT NULL,
	priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
	title VARCHAR(255) NOT NULL,
	description TEXT NOT NULL,
	target_metric VARCHAR(255) NOT NULL,
	is_completed BOOLEAN DEFAULT false NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE,
	student_feedback TEXT,
	PRIMARY KEY (id),
	FOREIGN KEY(plan_id) REFERENCES intervention_plans (id) ON DELETE RESTRICT,
	CONSTRAINT intervention_tasks_priority_check CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ml_models_one_active ON ml_models (is_active) WHERE is_active;

CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);

CREATE INDEX IF NOT EXISTS ix_course_presentations_code_presentation ON course_presentations (code_presentation);

CREATE INDEX IF NOT EXISTS idx_advisor_class ON advisor_students (advisor_id, class_name, academic_year);

CREATE INDEX IF NOT EXISTS idx_advisor_students_student ON advisor_students (student_id);

CREATE INDEX IF NOT EXISTS idx_course_lecturers_presentation ON course_lecturers (presentation_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_presentation ON student_enrollments (presentation_id);

CREATE INDEX IF NOT EXISTS idx_enrollments_student ON student_enrollments (student_id);

CREATE INDEX IF NOT EXISTS idx_help_student ON student_help_requests (student_id);

CREATE INDEX IF NOT EXISTS idx_help_target_status ON student_help_requests (target_user_id, status);

CREATE INDEX IF NOT EXISTS idx_notes_advisor ON advising_notes (advisor_id);

CREATE INDEX IF NOT EXISTS idx_notes_enrollment ON advising_notes (enrollment_id);

CREATE INDEX IF NOT EXISTS idx_snapshots_latest ON student_feature_snapshots (enrollment_id, created_at, id);

CREATE INDEX IF NOT EXISTS idx_predictions_latest ON prediction_runs (snapshot_id, created_at, id);

CREATE INDEX IF NOT EXISTS idx_predictions_model ON prediction_runs (model_id);

CREATE INDEX IF NOT EXISTS idx_intervention_plans_student ON intervention_plans (student_id, status);

CREATE INDEX IF NOT EXISTS idx_plans_prediction ON intervention_plans (prediction_run_id);

CREATE INDEX IF NOT EXISTS idx_intervention_tasks_plan_status ON intervention_tasks (plan_id, is_completed);
