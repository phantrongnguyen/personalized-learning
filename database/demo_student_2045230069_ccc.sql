-- Synthetic demonstration data; not collected from a live LMS.
-- Keeps an existing snapshot intact. Repeat execution does not create duplicates.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM student_enrollments e
        JOIN student_profiles sp ON sp.id=e.student_id
        JOIN course_presentations cp ON cp.id=e.presentation_id
        JOIN courses c ON c.id=cp.course_id
        WHERE sp.student_code='2045230069' AND c.code_module='CCC'
          AND cp.code_presentation='2013J'
    ) THEN
        RAISE EXCEPTION 'Missing CCC enrollment for student 2045230069';
    END IF;
END $$;
INSERT INTO student_feature_snapshots (
    enrollment_id, cutoff_stage, total_clicks_to_t, clicks_resource_to_t,
    clicks_url_to_t, active_days_to_t, active_day_ratio, days_since_last_activity,
    clicks_recent_7, clicks_recent_30, assessments_submitted_to_t,
    late_submissions_to_t, submission_rate, raw_features_json
)
SELECT e.id, 'CUTOFF_75', 280, 180, 50, 32, 32.0 / 201, 2,
       25, 100, 8, 1, 0.8,
       '{"data_source":"synthetic_demo","assessment_score":7.5,
         "assessments_due":10,"cutoff_day":201,
         "note":"Demonstration only; score is not a model feature"}'::jsonb
FROM student_enrollments e
JOIN student_profiles sp ON sp.id=e.student_id
JOIN course_presentations cp ON cp.id=e.presentation_id
JOIN courses c ON c.id=cp.course_id
WHERE sp.student_code='2045230069' AND c.code_module='CCC'
  AND cp.code_presentation='2013J'
  AND NOT EXISTS (SELECT 1 FROM student_feature_snapshots s WHERE s.enrollment_id=e.id);
SELECT s.id AS snapshot_id, e.id AS enrollment_id, s.cutoff_stage,
       s.active_day_ratio, s.raw_features_json
FROM student_feature_snapshots s
JOIN student_enrollments e ON e.id=s.enrollment_id
JOIN student_profiles sp ON sp.id=e.student_id
JOIN course_presentations cp ON cp.id=e.presentation_id
JOIN courses c ON c.id=cp.course_id
WHERE sp.student_code='2045230069' AND c.code_module='CCC'
ORDER BY s.created_at DESC LIMIT 1;
COMMIT;
