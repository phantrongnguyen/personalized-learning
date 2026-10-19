"""Frozen 18 October schema; validate existing databases before adopting baseline."""
import json
from pathlib import Path
from alembic import op
from sqlalchemy import inspect, text

revision = '0001_baseline'
down_revision = None
branch_labels = depends_on = None
SQL = Path(__file__).resolve().parents[1] / 'sql'
LEGACY_INDEXES = {
    'course_lecturers': [('idx_course_lecturers_lecturer', ['lecturer_id'], False),
                         ('idx_course_lecturers_presentation', ['presentation_id'], False)],
    'advisor_students': [('idx_advisor_students_advisor', ['advisor_id', 'class_name'], False),
                         ('idx_advisor_students_student', ['student_id'], False)],
    'audit_logs': [('idx_audit_logs_action', ['action'], False), ('idx_audit_logs_created_at', ['created_at'], False)],
    'student_help_requests': [('idx_help_requests_student', ['student_id', 'status'], False)],
}


def without_legacy_indexes(signature):
    # These exact non-unique indexes were observed on the deployed local schema.
    # Other differences still stop adoption; no arbitrary drift is silently stamped.
    result = json.loads(json.dumps(signature))
    for table, indexes in LEGACY_INDEXES.items():
        if table in result:
            removable = []
            for name, columns, unique in indexes:
                definition = f'CREATE INDEX {name} ON public.{table} USING btree ({", ".join(columns)})'
                if [name, definition] in result[table]['index_definitions']:
                    removable.append(name)
            result[table]['indexes'] = [i for i in result[table]['indexes'] if i[0] not in removable]
            result[table]['index_definitions'] = [i for i in result[table]['index_definitions'] if i[0] not in removable]
    return result


def signature(connection):
    inspector = inspect(connection)
    result = {}
    for table in sorted(set(inspector.get_table_names()) - {'alembic_version'}):
        result[table] = {
            'columns': sorted([[c['name'], c['type'].compile(dialect=connection.dialect), c['nullable'], c.get('default')]
                        for c in inspector.get_columns(table)], key=lambda c: c[0]),
            'pk': inspector.get_pk_constraint(table)['constrained_columns'],
            'unique': sorted(sorted(c['column_names']) for c in inspector.get_unique_constraints(table)),
            # pg_dump/restore rewrites VARCHAR IN-lists with element casts rather
            # than an array cast. Normalize only those equivalent text casts.
            'checks': sorted(c['sqltext'].replace('::character varying', '').replace('::text[]', '').replace('::text', '')
                             for c in inspector.get_check_constraints(table)),
            'foreign_keys': sorted([f['constrained_columns'], f['referred_table'], f['referred_columns'],
                                    f['options'].get('ondelete', 'NO ACTION')]
                                   for f in inspector.get_foreign_keys(table)),
            'indexes': sorted([i['name'], i['column_names'], i['unique']]
                              for i in inspector.get_indexes(table) if not i.get('duplicates_constraint')),
            'index_definitions': [list(row) for row in connection.execute(text(
                'SELECT indexname,indexdef FROM pg_indexes WHERE schemaname=current_schema() AND tablename=:table ORDER BY indexname'),
                {'table': table})],
        }
    return result


def execute_file(name):
    sql = (SQL / name).read_text(encoding='utf-8')
    op.get_bind().connection.run_async(lambda connection: connection.execute(sql))


def upgrade():
    connection = op.get_bind()
    tables = set(inspect(connection).get_table_names()) - {'alembic_version'}
    if not tables:
        execute_file('0001_schema.sql')
    else:
        # Provenance column may be absent on installations predating task 2.
        expected = json.loads((SQL / '0001_signature.json').read_text(encoding='utf-8'))
        actual = without_legacy_indexes(signature(connection))
        if 'prediction_runs' in actual and not any(c[0] == 'inference_context' for c in actual['prediction_runs']['columns']):
            expected['prediction_runs']['columns'] = [c for c in expected['prediction_runs']['columns'] if c[0] != 'inference_context']
        if actual != expected:
            changed = sorted(t for t in actual.keys() | expected.keys() if actual.get(t) != expected.get(t))
            raise RuntimeError('Baseline schema drift in: ' + ', '.join(changed) +
                               '. Reconcile against frozen 0001 schema on a restored copy; do not stamp blindly.')
    execute_file('0001_integrity.sql')


def downgrade():
    raise RuntimeError('Baseline downgrade would delete application data. Restore a verified backup instead.')
