"""Verify migrations only in uniquely named PostgreSQL databases ending in _test.

Reads application rows into an isolated legacy clone; never writes the source.
Keeps test databases and a JSON evidence file for inspection/reproduction.
"""
import asyncio
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import asyncpg
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from core.config import settings
from models import Base

SQL_DIR = ROOT / 'apps/backend/migrations/sql'
spec = importlib.util.spec_from_file_location('baseline', ROOT / 'apps/backend/migrations/versions/0001_baseline.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def dsn(url):
    return url.set(drivername='postgresql').render_as_string(hide_password=False)


def normalized_signature(connection):
    result = baseline.signature(connection)
    for table in result.values():
        table['columns'].sort(key=lambda c: c[0])
    return result


async def alembic(url, action='upgrade', revision='head'):
    engine = create_async_engine(url.set(drivername='postgresql+asyncpg'))
    try:
        async with engine.begin() as connection:
            def run(sync):
                config = Config(str(ROOT / 'alembic.ini'))
                config.attributes['connection'] = sync
                getattr(command, action)(config, revision)
            await connection.run_sync(run)
    finally:
        await engine.dispose()


async def signature(url):
    engine = create_async_engine(url.set(drivername='postgresql+asyncpg'))
    try:
        async with engine.connect() as connection:
            return await connection.run_sync(normalized_signature)
    finally:
        await engine.dispose()


async def fingerprints(connection):
    result = {}
    for table in Base.metadata.sorted_tables:
        result[table.name] = await connection.fetchval(f'''SELECT count(*)::text || ':' ||
            md5(COALESCE(string_agg(to_jsonb(t)::text, '' ORDER BY to_jsonb(t)::text), ''))
            FROM "{table.name}" t''')
    return result


async def expect_rejected(connection, statement, state):
    tx = connection.transaction()
    await tx.start()
    try:
        await connection.execute(statement)
    except asyncpg.PostgresError as error:
        assert error.sqlstate == state, (statement, error.sqlstate)
    else:
        raise AssertionError('Database accepted invalid operation: ' + statement)
    finally:
        await tx.rollback()


async def latest_snapshot_plan(connection):
    enrollment = await connection.fetchval('SELECT enrollment_id FROM student_feature_snapshots LIMIT 1')
    plan = json.loads(await connection.fetchval('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '
        'SELECT id FROM student_feature_snapshots WHERE enrollment_id=$1 ORDER BY created_at DESC,id DESC LIMIT 1', enrollment))[0]
    nodes = []
    def walk(node):
        nodes.append({'node': node['Node Type'], 'index': node.get('Index Name'), 'rows': node['Actual Rows']})
        for child in node.get('Plans', []):
            walk(child)
    walk(plan['Plan'])
    return {'execution_ms': plan['Execution Time'], 'nodes': nodes,
            'scope': 'Local sample only; small tables, not a load benchmark'}


async def main():
    source = make_url(settings.database_url)
    prefix = 'migration_' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    targets = {name: source.set(database=f'{prefix}_{name}_test') for name in ('empty', 'sql', 'clone', 'invalid', 'drift')}
    admin = await asyncpg.connect(dsn(source.set(database='postgres')))
    try:
        for target in targets.values():
            assert target.database.endswith('_test') and target.database != source.database
            await admin.execute(f'CREATE DATABASE "{target.database}"')
    finally:
        await admin.close()
    evidence = {'utc': datetime.now(timezone.utc).isoformat(), 'databases': {k: v.database for k, v in targets.items()}, 'checks': []}
    def passed(message):
        evidence['checks'].append(message)
        print('PASS:', message, flush=True)

    await alembic(targets['empty'])
    passed('Empty database upgrades through baseline to head')
    fresh = await asyncpg.connect(dsn(targets['sql']))
    try:
        for filename in ('01_init_schema.sql', '02_seed_data.sql', '03_prediction_integrity.sql', '04_schema_version.sql'):
            await fresh.execute((ROOT / 'docker/postgres/init-scripts' / filename).read_text(encoding='utf-8'))
    finally:
        await fresh.close()
    expected = await signature(targets['sql'])
    actual = await signature(targets['empty'])
    assert expected == actual, {table: {'sql': expected.get(table), 'alembic': actual.get(table)}
                               for table in expected.keys() | actual.keys() if expected.get(table) != actual.get(table)}
    passed('All 19 tables: canonical SQL and Alembic schema signatures match (columns/defaults/nullability/PK/UNIQUE/CHECK/FK/indexes)')
    engine = create_async_engine(targets['empty'].set(drivername='postgresql+asyncpg'))
    async with engine.connect() as connection:
        differences = await connection.run_sync(lambda sync: compare_metadata(
            MigrationContext.configure(sync, opts={'compare_type': True, 'compare_server_default': True}), Base.metadata))
        assert not differences, differences
    await engine.dispose()
    passed('Alembic autogenerate finds zero SQL/ORM differences')
    source_signature = await signature(source)
    baseline_expected = json.loads((SQL_DIR / '0001_signature.json').read_text(encoding='utf-8'))
    source_at_head = source_signature == expected
    assert source_at_head or baseline.without_legacy_indexes(source_signature) == baseline_expected, 'Application schema must match baseline or head before clone verification'
    passed('Read-only application schema inspection matches a supported 19-table baseline/head')

    src = await asyncpg.connect(dsn(source))
    clone = await asyncpg.connect(dsn(targets['clone']))
    try:
        async with src.transaction(isolation='repeatable_read', readonly=True):
            before = await fingerprints(src)
            schema_file = ROOT / 'docker/postgres/init-scripts/01_init_schema.sql' if source_at_head else SQL_DIR / '0001_schema.sql'
            await clone.execute(schema_file.read_text(encoding='utf-8'))
            await clone.execute((SQL_DIR / '0001_integrity.sql').read_text(encoding='utf-8'))
            if source_at_head:
                await clone.execute((ROOT / 'docker/postgres/init-scripts/04_schema_version.sql').read_text(encoding='utf-8'))
            for table, indexes in ({} if source_at_head else baseline.LEGACY_INDEXES).items():
                for name, columns, unique in indexes:
                    if [name, columns, unique] in source_signature[table]['indexes']:
                        definition = await src.fetchval('SELECT indexdef FROM pg_indexes WHERE schemaname=$1 AND indexname=$2', 'public', name)
                        await clone.execute(definition)
            async with clone.transaction():
                for table in Base.metadata.sorted_tables:
                    columns = [r['column_name'] for r in await src.fetch(
                        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=$1 ORDER BY ordinal_position", table.name)]
                    quoted = ','.join(f'"{name}"' for name in columns)
                    # Bounded batches keep the snapshot consistent without buffering an entire table.
                    batch = []
                    async for row in src.cursor(f'SELECT {quoted} FROM "{table.name}"'):
                        batch.append(tuple(row))
                        if len(batch) == 1000:
                            await clone.copy_records_to_table(table.name, records=batch, columns=columns)
                            batch = []
                    if batch:
                        await clone.copy_records_to_table(table.name, records=batch, columns=columns)
            assert before == await fingerprints(clone)
            assert before == await fingerprints(src)
        passed('Read-only consistent copy: all 19 application tables copied with equal counts/content hashes')
        if source_at_head:
            await alembic(targets['clone'], 'downgrade', '0001_baseline')
        baseline_rows = await fingerprints(clone)
        evidence['latest_snapshot_query_plan'] = {'baseline': await latest_snapshot_plan(clone)}
        await alembic(targets['clone'])
        evidence['latest_snapshot_query_plan']['head'] = await latest_snapshot_plan(clone)
        assert expected == await signature(targets['clone'])
        for table in Base.metadata.sorted_tables:
            assert int(before[table.name].split(':')[0]) == await clone.fetchval(f'SELECT count(*) FROM "{table.name}"')
        passed('Existing-data clone upgrades without losing rows; upgraded schema matches fresh database')
        seed = await clone.fetchrow("SELECT roc_auc,average_precision FROM ml_models WHERE version='v1.0.0-cutoff75'")
        assert seed and seed['roc_auc'] is None and abs(seed['average_precision'] - 0.8967566497124569) < 1e-12
        passed('Known seed metric corrected to average precision; unknown ROC-AUC remains NULL')
        await alembic(targets['clone'], 'downgrade', '0001_baseline')
        assert baseline_rows == await fingerprints(clone)
        passed('Downgrade to baseline restores all original application row hashes including seed metadata')
        await alembic(targets['clone'])
        passed('Re-upgrade after downgrade succeeds')
    finally:
        await src.close()
        await clone.close()

    for name in ('invalid', 'drift'):
        connection = await asyncpg.connect(dsn(targets[name]))
        try:
            await connection.execute((SQL_DIR / '0001_schema.sql').read_text(encoding='utf-8'))
            if name == 'invalid':
                await connection.execute("INSERT INTO courses(code_module,name,credits_default) VALUES ('BAD','Invalid',-1)")
            else:
                await connection.execute('ALTER TABLE courses ALTER COLUMN name TYPE varchar(256)')
            original = await signature(targets[name])
            try:
                await alembic(targets[name])
            except RuntimeError as error:
                assert ('preflight' if name == 'invalid' else 'drift') in str(error).lower(), str(error)
            else:
                raise AssertionError('Migration accepted ' + name)
            assert original == await signature(targets[name])
            assert not await connection.fetchval("SELECT to_regclass('public.alembic_version') IS NOT NULL")
            passed(f'{name}: rejected with transaction rollback and no schema/version changes')
        finally:
            await connection.close()

    connection = await asyncpg.connect(dsn(targets['sql']))
    try:
        await expect_rejected(connection, "INSERT INTO ml_models(model_name,version,model_file_path,is_active) VALUES ('Second','second','x',true)", '23505')
        for column in ('threshold', 'cutoff_fraction', 'accuracy', 'roc_auc', 'average_precision'):
            for value in ('-0.1', '1.1', "'NaN'::float8", "'Infinity'::float8"):
                await expect_rejected(connection, f'UPDATE ml_models SET {column}={value}', '23514')
        passed('Partial UNIQUE rejects a second active model; all metric/threshold bounds reject out-of-range/NaN/infinity')
        # Tests below use a complete history chain created with SQL defaults.
        async with connection.transaction():
            uid = await connection.fetchval("INSERT INTO users(email,hashed_password,full_name) VALUES ('history@test','test','History') RETURNING id")
            student = await connection.fetchval("INSERT INTO student_profiles(user_id,student_code,gender,highest_education,age_band) VALUES ($1,'HISTORY','M','A Level or Equivalent','0-35') RETURNING id", uid)
            enrollment = await connection.fetchval("INSERT INTO student_enrollments(student_id,presentation_id) SELECT $1,id FROM course_presentations LIMIT 1 RETURNING id", student)
            snapshot = await connection.fetchval('INSERT INTO student_feature_snapshots(enrollment_id) VALUES ($1) RETURNING id', enrollment)
            prediction = await connection.fetchval('INSERT INTO prediction_runs(snapshot_id,model_id,prediction_label,risk_probability) SELECT $1,id,1,0.8 FROM ml_models WHERE is_active RETURNING id', snapshot)
            plan = await connection.fetchval('INSERT INTO intervention_plans(prediction_run_id,student_id) VALUES ($1,$2) RETURNING id', prediction, student)
            await connection.execute("INSERT INTO intervention_tasks(plan_id,category,title,description,target_metric) VALUES ($1,'HOC_THUAT','Task','Test','Test')", plan)
            for table, identifier in [('users',uid), ('student_profiles',student), ('student_enrollments',enrollment), ('student_feature_snapshots',snapshot), ('prediction_runs',prediction), ('intervention_plans',plan)]:
                await expect_rejected(connection, f"DELETE FROM {table} WHERE id='{identifier}'", '23503')
            await expect_rejected(connection, f"UPDATE student_feature_snapshots SET total_clicks_to_t=1 WHERE id='{snapshot}'", '23514')
            await expect_rejected(connection, f"UPDATE prediction_runs SET risk_probability=0.3 WHERE id='{prediction}'", '23514')
        passed('History DELETE blocked along full user/student/enrollment/snapshot/prediction/plan chain; immutable UPDATE triggers preserved')
    finally:
        await connection.close()
    output = ROOT / 'reports/test-results/task1-migrations.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Evidence:', output.relative_to(ROOT))


if __name__ == '__main__':
    asyncio.run(main())
