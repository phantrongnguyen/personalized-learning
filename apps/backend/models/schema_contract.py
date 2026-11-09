"""Shared database constraints/defaults, attached after all 19 tables are declared.

Keep scalar Python defaults in each model for ORM inserts; server defaults below
also protect SQL imports. Alembic revisions are frozen and never import this file.
"""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text


CHECKS = {
    'student_profiles': {
        'gender': "gender IN ('M', 'F')",
        'age_band': "age_band IN ('0-35', '35-55', '55<=')",
        'disability': "disability IN ('N', 'Y')",
    },
    'courses': {'credits_default': 'credits_default > 0'},
    'course_presentations': {'module_presentation_length': 'module_presentation_length > 0'},
    'student_enrollments': {
        'studied_credits': 'studied_credits > 0',
        'num_of_prev_attempts': 'num_of_prev_attempts >= 0',
        'final_result': "final_result IN ('PASS', 'FAIL', 'WITHDRAWN', 'DISTINCTION', 'Pass', 'Fail', 'Withdrawn', 'Distinction')",
    },
    'student_feature_snapshots': {
        **{name: f'{name} >= 0' for name in (
            'total_clicks_to_t', 'clicks_resource_to_t', 'clicks_url_to_t',
            'active_days_to_t', 'days_since_last_activity', 'clicks_recent_7',
            'clicks_recent_30', 'assessments_submitted_to_t', 'late_submissions_to_t')},
        'active_day_ratio': 'active_day_ratio >= 0 AND active_day_ratio <= 1',
        'submission_rate': 'submission_rate >= 0 AND submission_rate <= 1',
    },
    'ml_models': {
        **{name: f'{name} >= 0 AND {name} <= 1' for name in
           ('threshold', 'accuracy', 'roc_auc', 'average_precision')},
        'cutoff_fraction': 'cutoff_fraction > 0 AND cutoff_fraction <= 1',
    },
    'prediction_runs': {
        'prediction_label': 'prediction_label IN (0, 1)',
        'risk_probability': 'risk_probability >= 0 AND risk_probability <= 1',
        'execution_time_ms': 'execution_time_ms >= 0',
    },
    'intervention_plans': {'status': "status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')"},
    'intervention_tasks': {'priority': "priority IN ('HIGH', 'MEDIUM', 'LOW')"},
    'student_help_requests': {
        'target_role': "target_role IN ('ADVISOR', 'LECTURER')",
        'status': "status IN ('PENDING', 'IN_PROGRESS', 'RESOLVED')",
    },
}

DEFAULTS = {
    'users': {'is_active': 'true'},
    'student_profiles': {'disability': "'N'"},
    'courses': {'credits_default': '30'},
    'course_presentations': {'module_presentation_length': '260'},
    'student_enrollments': {'date_registration': '-10', 'studied_credits': '60', 'num_of_prev_attempts': '0'},
    'student_feature_snapshots': {
        'cutoff_stage': "'CUTOFF_75'",
        **{name: '0' for name in CHECKS['student_feature_snapshots']},
        'active_day_ratio': '0.0',
        'submission_rate': '0.0',
    },
    'ml_models': {'threshold': '0.5', 'cutoff_fraction': '0.75', 'is_active': 'false'},
    'intervention_plans': {'status': "'ACTIVE'"},
    'intervention_tasks': {'priority': "'MEDIUM'", 'is_completed': 'false'},
    'advising_notes': {'meeting_date': 'CURRENT_DATE', 'meeting_type': "'ONLINE'"},
    'lecturer_profiles': {'academic_rank': "'Giảng viên'"},
    'course_lecturers': {'role_in_course': "'GIANG_VIEN_CHINH'"},
    'student_help_requests': {'status': "'PENDING'"},
}

INDEXES = {
    'student_enrollments': [('idx_enrollments_student', 'student_id'), ('idx_enrollments_presentation', 'presentation_id')],
    'student_feature_snapshots': [('idx_snapshots_latest', 'enrollment_id', 'created_at', 'id')],
    'prediction_runs': [('idx_predictions_latest', 'snapshot_id', 'created_at', 'id'),
                        ('idx_predictions_model', 'model_id')],
    'intervention_plans': [('idx_intervention_plans_student', 'student_id', 'status'),
                           ('idx_plans_prediction', 'prediction_run_id')],
    'intervention_tasks': [('idx_intervention_tasks_plan_status', 'plan_id', 'is_completed')],
    'advisor_students': [('idx_advisor_class', 'advisor_id', 'class_name', 'academic_year'),
                         ('idx_advisor_students_student', 'student_id')],
    'course_lecturers': [('idx_course_lecturers_presentation', 'presentation_id')],
    'advising_notes': [('idx_notes_enrollment', 'enrollment_id'), ('idx_notes_advisor', 'advisor_id')],
    'student_help_requests': [('idx_help_student', 'student_id'), ('idx_help_target_status', 'target_user_id', 'status')],
}


def configure_schema(metadata):
    from sqlalchemy import DefaultClause
    for table in metadata.tables.values():
        # unique=True,index=True produces a unique index instead of SQL UNIQUE.
        # Use one explicit UNIQUE constraint and avoid redundant single-column indexes.
        for index in list(table.indexes):
            if index.unique:
                names = [c.name for c in index.columns]
                table.indexes.remove(index)
                table.append_constraint(UniqueConstraint(*names, name=f'{table.name}_{"_".join(names)}_key'))
        for column in table.columns:
            default = DEFAULTS.get(table.name, {}).get(column.name)
            if column.name == 'id' and str(column.type) == 'UUID':
                default = 'gen_random_uuid()'
            elif column.name in ('created_at', 'updated_at', 'assigned_at'):
                default = 'now()'
            if default is not None:
                column.server_default = DefaultClause(text(default))
        for key, expression in CHECKS.get(table.name, {}).items():
            table.append_constraint(CheckConstraint(expression, name=f'{table.name}_{key}_check'))
        for name, *columns in INDEXES.get(table.name, []):
            Index(name, *[table.c[c] for c in columns])
    Index('uq_ml_models_one_active', metadata.tables['ml_models'].c.is_active,
          unique=True, postgresql_where=text('is_active'))
    for table_name, columns, name in (
        ('course_presentations', ['course_id', 'code_presentation'], 'uq_course_presentation'),
        ('student_enrollments', ['student_id', 'presentation_id'], 'uq_student_presentation'),
        ('ml_models', ['version'], 'ml_models_version_key'),
    ):
        metadata.tables[table_name].append_constraint(UniqueConstraint(*columns, name=name))
