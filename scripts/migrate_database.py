"""Back up local PostgreSQL, prove restoration/upgrading on a copy, then migrate.

Usage: python scripts/migrate_database.py --container kltn13_postgres [--apply]
Without --apply only the backup/restored test database are written.
Backups contain private data: .cache is ignored by Git. Keep them securely.
"""
import argparse
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.config import Config
from alembic import command
from verify_migrations import ROOT, Base, settings, make_url, dsn, fingerprints, signature, normalized_signature, alembic


async def main(args):
    source = make_url(settings.database_url)
    if source.host not in ('localhost', '127.0.0.1', '::1'):
        raise SystemExit('This backup helper supports local Docker PostgreSQL only; use a reviewed pg_dump workflow for remote hosts.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    restored = source.set(database=f'migration_restore_{stamp}_test')
    backup_dir = ROOT / '.cache' / 'database-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    # Pass secrets through environment; never print or store the URL in evidence.
    env = dict(os.environ, PGPASSWORD=source.password or '')
    docker = ['docker', 'exec', '--env', 'PGPASSWORD', args.container]
    common = ['--host', '127.0.0.1', '--username', source.username or 'postgres']
    connection = await asyncpg.connect(dsn(source))
    try:
        identity = str(await connection.fetchval('SELECT system_identifier FROM pg_control_system()'))
        container_identity = subprocess.check_output(docker + ['psql', *common, '--dbname', source.database,
            '-Atc', 'SELECT system_identifier FROM pg_control_system()'], env=env, text=True).strip()
        if identity != container_identity:
            raise RuntimeError('Container is not the PostgreSQL instance configured by DATABASE_URL')
        original_signature = await signature(source)
        original = await fingerprints(connection)
        backup = backup_dir / f'{source.database}-{stamp}.dump'
        with backup.open('xb') as output:
            subprocess.run(docker + ['pg_dump', *common, '--dbname', source.database, '--format=custom',
                                     '--no-owner', '--no-privileges'], env=env, stdout=output, check=True)
        admin = await asyncpg.connect(dsn(source.set(database='postgres')))
        try:
            await admin.execute(f'CREATE DATABASE "{restored.database}"')
        finally:
            await admin.close()
        with backup.open('rb') as input_file:
            subprocess.run(['docker', 'exec', '-i', '--env', 'PGPASSWORD', args.container,
                'pg_restore', *common, '--dbname', restored.database, '--exit-on-error', '--no-owner', '--no-privileges'],
                env=env, stdin=input_file, check=True)
        copy = await asyncpg.connect(dsn(restored))
        try:
            assert original == await fingerprints(copy), 'Restored row hashes differ'
        finally:
            await copy.close()
        assert original_signature == await signature(restored), 'Restored schema differs'
        await alembic(restored)
        expected_signature = await signature(restored)
        assert original == await fingerprints(connection), 'Source changed during backup verification; retry during a quiet window'
        evidence = {'utc': datetime.now(timezone.utc).isoformat(), 'backup': str(backup.relative_to(ROOT)),
                    'sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
                    'restored_test_database': restored.database, 'restore_schema_and_rows_verified': True,
                    'restored_upgrade_verified': True, 'applied': False}
        print('PASS: backup restored with identical schema and all 19 table hashes; restored copy upgrades to head', flush=True)
        if args.apply:
            engine = create_async_engine(source.set(drivername='postgresql+asyncpg'))
            try:
                async with engine.begin() as migration_connection:
                    def upgrade(sync):
                        sync.exec_driver_sql("SET LOCAL lock_timeout = '10s'")
                        sync.exec_driver_sql('SELECT pg_advisory_xact_lock(1910202601)')
                        tables = ','.join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
                        sync.exec_driver_sql(f'LOCK TABLE {tables} IN ACCESS EXCLUSIVE MODE')
                        # Under the lock, verify that backup still matches every row.
                        for table in Base.metadata.sorted_tables:
                            current = sync.exec_driver_sql(f'''SELECT count(*)::text || ':' || md5(COALESCE(
                                string_agg(to_jsonb(t)::text, '' ORDER BY to_jsonb(t)::text), '')) FROM "{table.name}" t''').scalar_one()
                            assert current == original[table.name], 'Rows changed since backup: ' + table.name
                        before_models = [dict(r) for r in sync.exec_driver_sql('SELECT * FROM ml_models').mappings()]
                        config = Config(str(ROOT / 'alembic.ini'))
                        config.attributes['connection'] = sync
                        command.upgrade(config, 'head')
                        differences = compare_metadata(MigrationContext.configure(sync,
                            opts={'compare_type': True, 'compare_server_default': True}), Base.metadata)
                        assert not differences, differences
                        assert normalized_signature(sync) == expected_signature, 'Full schema differs from the verified restored copy'
                        for table in Base.metadata.sorted_tables:
                            if table.name == 'ml_models':
                                continue
                            after = sync.exec_driver_sql(f'''SELECT count(*)::text || ':' || md5(COALESCE(
                                string_agg(to_jsonb(t)::text, '' ORDER BY to_jsonb(t)::text), '')) FROM "{table.name}" t''').scalar_one()
                            assert after == original[table.name], 'Unexpected row changes: ' + table.name
                        for row in before_models:
                            row.setdefault('average_precision', None)
                            if str(row['id']) == 'a0000000-0000-0000-0000-000000000001' and row['version'] == 'v1.0.0-cutoff75' and row['roc_auc'] == 0.8968:
                                row['roc_auc'] = None
                                row['average_precision'] = 0.8967566497124569
                                row['metadata_json'] = {**(row['metadata_json'] or {}), 'metric_correction_0002': {
                                    'previous_roc_auc': 0.8968, 'scope': 'validation_reference_train_only',
                                    'source': 'THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json'}}
                            actual = dict(sync.exec_driver_sql('SELECT * FROM ml_models WHERE id=$1', (row['id'],)).mappings().one())
                            assert row == actual, 'Unexpected model data changes'
                    await migration_connection.run_sync(upgrade)
            finally:
                await engine.dispose()
            assert await signature(source) == expected_signature
            evidence['applied'] = True
            evidence['revision'] = '0002_normalize'
            evidence['unchanged_tables'] = 18
            evidence['model_changes'] = 'Only nullable average_precision and the verified seed metric correction'
            print('PASS: application database migrated atomically; 18 table hashes unchanged, model rows match expected correction', flush=True)
        output = ROOT / 'reports/test-results/task1-migration-apply.json'
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    finally:
        await connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container', required=True)
    parser.add_argument('--apply', action='store_true')
    asyncio.run(main(parser.parse_args()))
