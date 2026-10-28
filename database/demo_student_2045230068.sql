-- Du lieu GIA LAP de kiem tra giao dien sinh vien, khong phai ket qua ML.
-- Yeu cau tai khoan va student_profiles.student_code = '2045230068' da ton tai.
-- Khong thay doi mat khau, ho so, vai tro hay du lieu hoc phan dang co.
-- Chay lai se bo qua neu snapshot demo cua enrollment nay da ton tai.
BEGIN;

DO $$
DECLARE
    v_student UUID;
    v_course UUID;
    v_presentation UUID;
    v_enrollment UUID;
    v_snapshot UUID;
    v_model UUID;
    v_prediction UUID;
    v_plan UUID;
BEGIN
    SELECT id INTO v_student
    FROM student_profiles WHERE student_code = '2045230068';

    IF v_student IS NULL THEN
        RAISE EXCEPTION 'Chua co ho so sinh vien 2045230068. Hay cap tai khoan STUDENT kem MSSV qua admin truoc.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM student_profiles sp
        JOIN users u ON u.id = sp.user_id
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        WHERE sp.id = v_student AND u.is_active AND r.code = 'STUDENT'
    ) THEN
        RAISE EXCEPTION 'Tai khoan phai dang hoat dong va co vai tro STUDENT.';
    END IF;

    INSERT INTO courses (code_module, name, credits_default, description)
    VALUES ('AAA', 'Discovering Arts and Humanities', 30, 'Hoc phan OULAD')
    ON CONFLICT (code_module) DO NOTHING;
    SELECT id INTO v_course FROM courses WHERE code_module = 'AAA';

    INSERT INTO course_presentations
        (course_id, code_presentation, start_date, module_presentation_length)
    VALUES (v_course, 'DEMO2045230068', '2026-01-01', 268)
    ON CONFLICT (course_id, code_presentation) DO NOTHING;
    SELECT id INTO v_presentation FROM course_presentations
    WHERE course_id = v_course AND code_presentation = 'DEMO2045230068';

    INSERT INTO student_enrollments
        (student_id, presentation_id, date_registration, studied_credits, num_of_prev_attempts)
    VALUES (v_student, v_presentation, -10, 60, 0)
    ON CONFLICT (student_id, presentation_id) DO NOTHING;
    SELECT id INTO v_enrollment FROM student_enrollments
    WHERE student_id = v_student AND presentation_id = v_presentation;

    -- Khong gan ket qua gia lap vao model LightGBM that.
    INSERT INTO ml_models
        (model_name, version, model_file_path, threshold, cutoff_fraction,
         is_active, metadata_json)
    VALUES ('DEMO UI - du lieu gia lap', 'demo-ui-2045230068',
            'demo-ui-not-an-artifact', 0.5, 0.75, FALSE,
            '{"source":"synthetic_ui_demo","is_real_prediction":false}'::jsonb)
    ON CONFLICT (version) DO NOTHING;
    SELECT id INTO v_model FROM ml_models WHERE version = 'demo-ui-2045230068';

    IF EXISTS (
        SELECT 1 FROM student_feature_snapshots
        WHERE enrollment_id = v_enrollment
          AND raw_features_json ->> 'source' = 'demo-ui-2045230068'
    ) THEN
        RAISE NOTICE 'Du lieu demo da ton tai; khong chen lap.';
        RETURN;
    END IF;

    INSERT INTO student_feature_snapshots
        (enrollment_id, cutoff_stage, total_clicks_to_t, clicks_resource_to_t,
         clicks_url_to_t, active_days_to_t, active_day_ratio,
         days_since_last_activity, clicks_recent_7, clicks_recent_30,
         assessments_submitted_to_t, late_submissions_to_t, submission_rate,
         raw_features_json)
    VALUES
        (v_enrollment, 'CUTOFF_75', 180, 80, 30, 15, 0.15, 10, 8, 45,
         3, 2, 0.5, '{"source":"demo-ui-2045230068","synthetic":true}'::jsonb)
    RETURNING id INTO v_snapshot;

    INSERT INTO prediction_runs
        (snapshot_id, model_id, prediction_label, risk_probability)
    VALUES (v_snapshot, v_model, 1, 0.82)
    RETURNING id INTO v_prediction;

    INSERT INTO intervention_plans
        (prediction_run_id, student_id, status, target_completion_date,
         advisor_note_summary)
    VALUES (v_prediction, v_student, 'ACTIVE', CURRENT_DATE + 14,
            '[DEMO] Ke hoach gia lap de kiem tra giao dien')
    RETURNING id INTO v_plan;

    INSERT INTO intervention_tasks
        (plan_id, category, priority, title, description, target_metric)
    VALUES
        (v_plan, 'CHUYEN_CAN', 'HIGH', '[DEMO] Duy tri lich hoc',
         'Du lieu thu giao dien: hoc it nhat 3 ngay moi tuan.', '3 ngay/tuan'),
        (v_plan, 'HOC_THUAT', 'MEDIUM', '[DEMO] Hoan thanh bai tap',
         'Du lieu thu giao dien: on tap va nop bai dung han.', 'Ty le nop bai >= 80%');
END $$;

COMMIT;

SELECT sp.student_code, c.code_module, cp.code_presentation,
       se.id AS enrollment_id, pr.risk_probability,
       pr.prediction_label, m.version AS prediction_source
FROM student_profiles sp
JOIN student_enrollments se ON se.student_id = sp.id
JOIN course_presentations cp ON cp.id = se.presentation_id
JOIN courses c ON c.id = cp.course_id
JOIN student_feature_snapshots sf ON sf.enrollment_id = se.id
JOIN prediction_runs pr ON pr.snapshot_id = sf.id
JOIN ml_models m ON m.id = pr.model_id
WHERE sp.student_code = '2045230068'
  AND cp.code_presentation = 'DEMO2045230068'
ORDER BY pr.created_at DESC;
