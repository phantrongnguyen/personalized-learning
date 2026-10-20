"""Normalize the 19-table schema and preserve prediction/intervention history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_normalize'
down_revision = '0001_baseline'
branch_labels = depends_on = None


def preflight():
    problems = []
    checks = {'student_profiles': {'gender': "gender IN ('M', 'F')",
                          'age_band': "age_band IN ('0-35', '35-55', '55<=')",
                          'disability': "disability IN ('N', 'Y')"},
     'courses': {'credits_default': 'credits_default > 0'},
     'course_presentations': {'module_presentation_length': 'module_presentation_length > 0'},
     'student_enrollments': {'studied_credits': 'studied_credits > 0',
                             'num_of_prev_attempts': 'num_of_prev_attempts >= 0',
                             'final_result': "final_result IN ('PASS', 'FAIL', 'WITHDRAWN', "
                                             "'DISTINCTION', 'Pass', 'Fail', 'Withdrawn', "
                                             "'Distinction')"},
     'student_feature_snapshots': {'total_clicks_to_t': 'total_clicks_to_t >= 0',
                                   'clicks_resource_to_t': 'clicks_resource_to_t >= 0',
                                   'clicks_url_to_t': 'clicks_url_to_t >= 0',
                                   'active_days_to_t': 'active_days_to_t >= 0',
                                   'days_since_last_activity': 'days_since_last_activity >= 0',
                                   'clicks_recent_7': 'clicks_recent_7 >= 0',
                                   'clicks_recent_30': 'clicks_recent_30 >= 0',
                                   'assessments_submitted_to_t': 'assessments_submitted_to_t >= 0',
                                   'late_submissions_to_t': 'late_submissions_to_t >= 0',
                                   'active_day_ratio': 'active_day_ratio >= 0 AND active_day_ratio <= '
                                                       '1',
                                   'submission_rate': 'submission_rate >= 0 AND submission_rate <= 1'},
     'ml_models': {'threshold': 'threshold >= 0 AND threshold <= 1',
                   'accuracy': 'accuracy >= 0 AND accuracy <= 1',
                   'roc_auc': 'roc_auc >= 0 AND roc_auc <= 1',
                   'cutoff_fraction': 'cutoff_fraction > 0 AND cutoff_fraction <= 1'},
     'prediction_runs': {'prediction_label': 'prediction_label IN (0, 1)',
                         'risk_probability': 'risk_probability >= 0 AND risk_probability <= 1',
                         'execution_time_ms': 'execution_time_ms >= 0'},
     'intervention_plans': {'status': "status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')"},
     'intervention_tasks': {'priority': "priority IN ('HIGH', 'MEDIUM', 'LOW')"},
     'student_help_requests': {'target_role': "target_role IN ('ADVISOR', 'LECTURER')",
                               'status': "status IN ('PENDING', 'IN_PROGRESS', 'RESOLVED')"}}
    connection = op.get_bind()
    for table, expressions in checks.items():
        for name, expression in expressions.items():
            count = connection.execute(sa.text(f'SELECT count(*) FROM "{table}" WHERE NOT ({expression})')).scalar_one()
            if count:
                problems.append(f'{table}.{name}: {count} invalid rows')
    if connection.execute(sa.text('SELECT count(*) FROM lecturer_profiles WHERE academic_rank IS NULL')).scalar_one():
        problems.append('lecturer_profiles.academic_rank: NULL rows require an explicit value')
    if connection.execute(sa.text('SELECT count(*) FROM ml_models WHERE is_active')).scalar_one() > 1:
        problems.append('ml_models: multiple active models; select the valid model explicitly')
    if problems:
        raise RuntimeError('Migration preflight failed; no changes applied. Restore backup to a test database, '
                           'review/correct data with its owner, then retry: ' + '; '.join(problems))

def upgrade():
    preflight()
    # Known deployed indexes are replaced by the canonical query indexes below.
    for name in ('idx_course_lecturers_lecturer', 'idx_course_lecturers_presentation',
                 'idx_advisor_students_advisor', 'idx_advisor_students_student',
                 'idx_audit_logs_action', 'idx_audit_logs_created_at', 'idx_help_requests_student'):
        op.execute(sa.text(f'DROP INDEX IF EXISTS "{name}"'))
    # Reviewed DDL changes; all changes run in one transaction.
    op.alter_column('advising_notes', 'meeting_type',
               existing_type=sa.VARCHAR(length=50),
               server_default=sa.text("'ONLINE'"),
               existing_nullable=False)
    op.create_index('idx_notes_advisor', 'advising_notes', ['advisor_id'], unique=False)
    op.create_index('idx_notes_enrollment', 'advising_notes', ['enrollment_id'], unique=False)
    op.drop_constraint(op.f('advising_notes_advisor_id_fkey'), 'advising_notes', type_='foreignkey')
    op.drop_constraint(op.f('advising_notes_enrollment_id_fkey'), 'advising_notes', type_='foreignkey')
    op.create_foreign_key('advising_notes_advisor_id_fkey', 'advising_notes', 'advisor_profiles', ['advisor_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('advising_notes_enrollment_id_fkey', 'advising_notes', 'student_enrollments', ['enrollment_id'], ['id'], ondelete='RESTRICT')
    op.drop_constraint(op.f('advisor_profiles_user_id_fkey'), 'advisor_profiles', type_='foreignkey')
    op.create_foreign_key('advisor_profiles_user_id_fkey', 'advisor_profiles', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
    op.create_index('idx_advisor_class', 'advisor_students', ['advisor_id', 'class_name', 'academic_year'], unique=False)
    op.create_index('idx_advisor_students_student', 'advisor_students', ['student_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index('idx_course_lecturers_presentation', 'course_lecturers', ['presentation_id'], unique=False)
    op.create_index(op.f('ix_course_presentations_code_presentation'), 'course_presentations', ['code_presentation'], unique=False)
    op.drop_constraint(op.f('course_presentations_course_id_fkey'), 'course_presentations', type_='foreignkey')
    op.create_foreign_key('course_presentations_course_id_fkey', 'course_presentations', 'courses', ['course_id'], ['id'], ondelete='RESTRICT')
    op.create_index('idx_plans_prediction', 'intervention_plans', ['prediction_run_id'], unique=False)
    op.drop_constraint(op.f('intervention_plans_student_id_fkey'), 'intervention_plans', type_='foreignkey')
    op.drop_constraint(op.f('intervention_plans_prediction_run_id_fkey'), 'intervention_plans', type_='foreignkey')
    op.create_foreign_key('intervention_plans_student_id_fkey', 'intervention_plans', 'student_profiles', ['student_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('intervention_plans_prediction_run_id_fkey', 'intervention_plans', 'prediction_runs', ['prediction_run_id'], ['id'], ondelete='RESTRICT')
    op.alter_column('intervention_tasks', 'priority',
               existing_type=sa.VARCHAR(length=20),
               server_default=sa.text("'MEDIUM'"),
               existing_nullable=False)
    op.drop_constraint(op.f('intervention_tasks_plan_id_fkey'), 'intervention_tasks', type_='foreignkey')
    op.create_foreign_key('intervention_tasks_plan_id_fkey', 'intervention_tasks', 'intervention_plans', ['plan_id'], ['id'], ondelete='RESTRICT')
    op.alter_column('lecturer_profiles', 'academic_rank',
               existing_type=sa.VARCHAR(length=50),
               nullable=False,
               existing_server_default=sa.text("'Giáº£ng viÃªn'::character varying"))
    op.drop_constraint(op.f('lecturer_profiles_user_id_fkey'), 'lecturer_profiles', type_='foreignkey')
    op.create_foreign_key('lecturer_profiles_user_id_fkey', 'lecturer_profiles', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
    op.add_column('ml_models', sa.Column('average_precision', sa.Float(), nullable=True))
    op.alter_column('ml_models', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('false'),
               existing_nullable=False)
    op.create_index('uq_ml_models_one_active', 'ml_models', ['is_active'], unique=True, postgresql_where=sa.text('is_active'))
    op.drop_index(op.f('idx_predictions_created_at_desc'), table_name='prediction_runs')
    op.drop_index(op.f('idx_predictions_snapshot'), table_name='prediction_runs')
    op.create_index('idx_predictions_latest', 'prediction_runs', ['snapshot_id', 'created_at', 'id'], unique=False)
    op.create_index('idx_predictions_model', 'prediction_runs', ['model_id'], unique=False)
    op.drop_constraint(op.f('prediction_runs_snapshot_id_fkey'), 'prediction_runs', type_='foreignkey')
    op.create_foreign_key('prediction_runs_snapshot_id_fkey', 'prediction_runs', 'student_feature_snapshots', ['snapshot_id'], ['id'], ondelete='RESTRICT')
    op.drop_constraint(op.f('student_enrollments_student_id_fkey'), 'student_enrollments', type_='foreignkey')
    op.drop_constraint(op.f('student_enrollments_presentation_id_fkey'), 'student_enrollments', type_='foreignkey')
    op.create_foreign_key('student_enrollments_student_id_fkey', 'student_enrollments', 'student_profiles', ['student_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('student_enrollments_presentation_id_fkey', 'student_enrollments', 'course_presentations', ['presentation_id'], ['id'], ondelete='RESTRICT')
    op.drop_index(op.f('idx_feature_snapshots_enrollment'), table_name='student_feature_snapshots')
    op.create_index('idx_snapshots_latest', 'student_feature_snapshots', ['enrollment_id', 'created_at', 'id'], unique=False)
    op.drop_constraint(op.f('student_feature_snapshots_enrollment_id_fkey'), 'student_feature_snapshots', type_='foreignkey')
    op.create_foreign_key('student_feature_snapshots_enrollment_id_fkey', 'student_feature_snapshots', 'student_enrollments', ['enrollment_id'], ['id'], ondelete='RESTRICT')
    op.create_index('idx_help_student', 'student_help_requests', ['student_id'], unique=False)
    op.create_index('idx_help_target_status', 'student_help_requests', ['target_user_id', 'status'], unique=False)
    op.drop_constraint(op.f('student_help_requests_student_id_fkey'), 'student_help_requests', type_='foreignkey')
    op.create_foreign_key('student_help_requests_student_id_fkey', 'student_help_requests', 'student_profiles', ['student_id'], ['id'], ondelete='RESTRICT')
    op.drop_index(op.f('idx_student_profiles_code'), table_name='student_profiles')
    op.drop_constraint(op.f('student_profiles_user_id_fkey'), 'student_profiles', type_='foreignkey')
    op.create_foreign_key('student_profiles_user_id_fkey', 'student_profiles', 'users', ['user_id'], ['id'], ondelete='RESTRICT')
    # ### end Alembic commands ###
    op.create_check_constraint('student_profiles_disability_check', 'student_profiles', "disability IN ('N', 'Y')")
    op.create_check_constraint('courses_credits_default_check', 'courses', 'credits_default > 0')
    op.create_check_constraint('course_presentations_module_presentation_length_check', 'course_presentations', 'module_presentation_length > 0')
    op.create_check_constraint('student_enrollments_studied_credits_check', 'student_enrollments', 'studied_credits > 0')
    op.create_check_constraint('student_enrollments_num_of_prev_attempts_check', 'student_enrollments', 'num_of_prev_attempts >= 0')
    op.create_check_constraint('student_enrollments_final_result_check', 'student_enrollments', "final_result IN ('PASS', 'FAIL', 'WITHDRAWN', 'DISTINCTION', 'Pass', 'Fail', 'Withdrawn', 'Distinction')")
    op.create_check_constraint('student_feature_snapshots_total_clicks_to_t_check', 'student_feature_snapshots', 'total_clicks_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_clicks_resource_to_t_check', 'student_feature_snapshots', 'clicks_resource_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_clicks_url_to_t_check', 'student_feature_snapshots', 'clicks_url_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_active_days_to_t_check', 'student_feature_snapshots', 'active_days_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_days_since_last_activity_check', 'student_feature_snapshots', 'days_since_last_activity >= 0')
    op.create_check_constraint('student_feature_snapshots_clicks_recent_7_check', 'student_feature_snapshots', 'clicks_recent_7 >= 0')
    op.create_check_constraint('student_feature_snapshots_clicks_recent_30_check', 'student_feature_snapshots', 'clicks_recent_30 >= 0')
    op.create_check_constraint('student_feature_snapshots_assessments_submitted_to_t_check', 'student_feature_snapshots', 'assessments_submitted_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_late_submissions_to_t_check', 'student_feature_snapshots', 'late_submissions_to_t >= 0')
    op.create_check_constraint('student_feature_snapshots_active_day_ratio_check', 'student_feature_snapshots', 'active_day_ratio >= 0 AND active_day_ratio <= 1')
    op.create_check_constraint('student_feature_snapshots_submission_rate_check', 'student_feature_snapshots', 'submission_rate >= 0 AND submission_rate <= 1')
    op.create_check_constraint('ml_models_threshold_check', 'ml_models', 'threshold >= 0 AND threshold <= 1')
    op.create_check_constraint('ml_models_accuracy_check', 'ml_models', 'accuracy >= 0 AND accuracy <= 1')
    op.create_check_constraint('ml_models_roc_auc_check', 'ml_models', 'roc_auc >= 0 AND roc_auc <= 1')
    op.create_check_constraint('ml_models_average_precision_check', 'ml_models', 'average_precision >= 0 AND average_precision <= 1')
    op.create_check_constraint('ml_models_cutoff_fraction_check', 'ml_models', 'cutoff_fraction > 0 AND cutoff_fraction <= 1')
    op.create_check_constraint('prediction_runs_risk_probability_check', 'prediction_runs', 'risk_probability >= 0 AND risk_probability <= 1')
    op.create_check_constraint('prediction_runs_execution_time_ms_check', 'prediction_runs', 'execution_time_ms >= 0')
    op.create_check_constraint('intervention_plans_status_check', 'intervention_plans', "status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')")
    op.get_bind().exec_driver_sql("""UPDATE ml_models SET average_precision = 0.8967566497124569,
        roc_auc = NULL, metadata_json = COALESCE(metadata_json, '{}'::jsonb) ||
        '{"metric_correction_0002":{"previous_roc_auc":0.8968,"scope":"validation_reference_train_only","source":"THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"}}'::jsonb
        WHERE id = 'a0000000-0000-0000-0000-000000000001'
          AND version = 'v1.0.0-cutoff75' AND roc_auc = 0.8968""")

def downgrade():
    op.get_bind().exec_driver_sql("""UPDATE ml_models SET roc_auc = 0.8968,
        metadata_json = metadata_json - 'metric_correction_0002'
        WHERE metadata_json->'metric_correction_0002'->>'previous_roc_auc' = '0.8968'
          AND roc_auc IS NULL""")
    op.drop_constraint('intervention_plans_status_check', 'intervention_plans', type_="check")
    op.drop_constraint('prediction_runs_execution_time_ms_check', 'prediction_runs', type_="check")
    op.drop_constraint('prediction_runs_risk_probability_check', 'prediction_runs', type_="check")
    op.drop_constraint('ml_models_cutoff_fraction_check', 'ml_models', type_="check")
    op.drop_constraint('ml_models_average_precision_check', 'ml_models', type_="check")
    op.drop_constraint('ml_models_roc_auc_check', 'ml_models', type_="check")
    op.drop_constraint('ml_models_accuracy_check', 'ml_models', type_="check")
    op.drop_constraint('ml_models_threshold_check', 'ml_models', type_="check")
    op.drop_constraint('student_feature_snapshots_submission_rate_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_active_day_ratio_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_late_submissions_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_assessments_submitted_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_clicks_recent_30_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_clicks_recent_7_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_days_since_last_activity_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_active_days_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_clicks_url_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_clicks_resource_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_feature_snapshots_total_clicks_to_t_check', 'student_feature_snapshots', type_="check")
    op.drop_constraint('student_enrollments_final_result_check', 'student_enrollments', type_="check")
    op.drop_constraint('student_enrollments_num_of_prev_attempts_check', 'student_enrollments', type_="check")
    op.drop_constraint('student_enrollments_studied_credits_check', 'student_enrollments', type_="check")
    op.drop_constraint('course_presentations_module_presentation_length_check', 'course_presentations', type_="check")
    op.drop_constraint('courses_credits_default_check', 'courses', type_="check")
    op.drop_constraint('student_profiles_disability_check', 'student_profiles', type_="check")
    # Reviewed DDL changes; all changes run in one transaction.
    op.drop_constraint('student_profiles_user_id_fkey', 'student_profiles', type_='foreignkey')
    op.create_foreign_key(op.f('student_profiles_user_id_fkey'), 'student_profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('idx_student_profiles_code'), 'student_profiles', ['student_code'], unique=False)
    op.drop_constraint('student_help_requests_student_id_fkey', 'student_help_requests', type_='foreignkey')
    op.create_foreign_key(op.f('student_help_requests_student_id_fkey'), 'student_help_requests', 'student_profiles', ['student_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_help_target_status', table_name='student_help_requests')
    op.drop_index('idx_help_student', table_name='student_help_requests')
    op.drop_constraint('student_feature_snapshots_enrollment_id_fkey', 'student_feature_snapshots', type_='foreignkey')
    op.create_foreign_key(op.f('student_feature_snapshots_enrollment_id_fkey'), 'student_feature_snapshots', 'student_enrollments', ['enrollment_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_snapshots_latest', table_name='student_feature_snapshots')
    op.create_index(op.f('idx_feature_snapshots_enrollment'), 'student_feature_snapshots', ['enrollment_id', 'cutoff_stage'], unique=False)
    op.drop_constraint('student_enrollments_presentation_id_fkey', 'student_enrollments', type_='foreignkey')
    op.drop_constraint('student_enrollments_student_id_fkey', 'student_enrollments', type_='foreignkey')
    op.create_foreign_key(op.f('student_enrollments_presentation_id_fkey'), 'student_enrollments', 'course_presentations', ['presentation_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('student_enrollments_student_id_fkey'), 'student_enrollments', 'student_profiles', ['student_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('prediction_runs_snapshot_id_fkey', 'prediction_runs', type_='foreignkey')
    op.create_foreign_key(op.f('prediction_runs_snapshot_id_fkey'), 'prediction_runs', 'student_feature_snapshots', ['snapshot_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_predictions_model', table_name='prediction_runs')
    op.drop_index('idx_predictions_latest', table_name='prediction_runs')
    op.create_index(op.f('idx_predictions_snapshot'), 'prediction_runs', ['snapshot_id'], unique=False)
    op.create_index(op.f('idx_predictions_created_at_desc'), 'prediction_runs', [sa.literal_column('created_at DESC')], unique=False)
    op.drop_index('uq_ml_models_one_active', table_name='ml_models', postgresql_where=sa.text('is_active'))
    op.alter_column('ml_models', 'is_active',
               existing_type=sa.BOOLEAN(),
               server_default=sa.text('true'),
               existing_nullable=False)
    op.drop_column('ml_models', 'average_precision')
    op.drop_constraint('lecturer_profiles_user_id_fkey', 'lecturer_profiles', type_='foreignkey')
    op.create_foreign_key(op.f('lecturer_profiles_user_id_fkey'), 'lecturer_profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.alter_column('lecturer_profiles', 'academic_rank',
               existing_type=sa.VARCHAR(length=50),
               nullable=True,
               existing_server_default=sa.text("'Giáº£ng viÃªn'::character varying"))
    op.drop_constraint('intervention_tasks_plan_id_fkey', 'intervention_tasks', type_='foreignkey')
    op.create_foreign_key(op.f('intervention_tasks_plan_id_fkey'), 'intervention_tasks', 'intervention_plans', ['plan_id'], ['id'], ondelete='CASCADE')
    op.alter_column('intervention_tasks', 'priority',
               existing_type=sa.VARCHAR(length=20),
               server_default=None,
               existing_nullable=False)
    op.drop_constraint('intervention_plans_prediction_run_id_fkey', 'intervention_plans', type_='foreignkey')
    op.drop_constraint('intervention_plans_student_id_fkey', 'intervention_plans', type_='foreignkey')
    op.create_foreign_key(op.f('intervention_plans_prediction_run_id_fkey'), 'intervention_plans', 'prediction_runs', ['prediction_run_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('intervention_plans_student_id_fkey'), 'intervention_plans', 'student_profiles', ['student_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_plans_prediction', table_name='intervention_plans')
    op.drop_constraint('course_presentations_course_id_fkey', 'course_presentations', type_='foreignkey')
    op.create_foreign_key(op.f('course_presentations_course_id_fkey'), 'course_presentations', 'courses', ['course_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_course_presentations_code_presentation'), table_name='course_presentations')
    op.drop_index('idx_course_lecturers_presentation', table_name='course_lecturers')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index('idx_advisor_students_student', table_name='advisor_students')
    op.drop_index('idx_advisor_class', table_name='advisor_students')
    op.drop_constraint('advisor_profiles_user_id_fkey', 'advisor_profiles', type_='foreignkey')
    op.create_foreign_key(op.f('advisor_profiles_user_id_fkey'), 'advisor_profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('advising_notes_enrollment_id_fkey', 'advising_notes', type_='foreignkey')
    op.drop_constraint('advising_notes_advisor_id_fkey', 'advising_notes', type_='foreignkey')
    op.create_foreign_key(op.f('advising_notes_enrollment_id_fkey'), 'advising_notes', 'student_enrollments', ['enrollment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('advising_notes_advisor_id_fkey'), 'advising_notes', 'advisor_profiles', ['advisor_id'], ['id'], ondelete='CASCADE')
    op.drop_index('idx_notes_enrollment', table_name='advising_notes')
    op.drop_index('idx_notes_advisor', table_name='advising_notes')
    op.alter_column('advising_notes', 'meeting_type',
               existing_type=sa.VARCHAR(length=50),
               server_default=sa.text("'IN_PERSON'::character varying"),
               existing_nullable=False)
    # ### end Alembic commands ###
