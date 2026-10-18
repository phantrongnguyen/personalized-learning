"""Provision a dedicated PostgreSQL database and run the backend suite safely.

Usage: .venv/Scripts/python scripts/run_backend_tests.py [pytest arguments]
TEST_DATABASE_URL can select an existing dedicated database ending in _test.
Never drops databases or touches the application database's tables.
"""
import asyncio
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/backend"))

from core.config import settings
from sqlalchemy.engine import make_url
import asyncpg


async def prepare():
    source = make_url(settings.database_url)
    target = make_url(os.environ.get("TEST_DATABASE_URL") or source.set(
        database=source.database + "_test").render_as_string(hide_password=False))
    if not target.database or not target.database.endswith("_test") or target.database == source.database:
        raise SystemExit("TEST_DATABASE_URL must name a separate database ending in _test")
    def dsn(url):
        return url.set(drivername="postgresql").render_as_string(hide_password=False)
    connection = await asyncpg.connect(dsn(target.set(database="postgres")))
    try:
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", target.database)
        if not exists:
            name = target.database.replace('"', '""')
            await connection.execute(f'CREATE DATABASE "{name}"')
    finally:
        await connection.close()
    connection = await asyncpg.connect(dsn(target))
    try:
        for filename in ("01_init_schema.sql", "02_seed_data.sql", "03_prediction_integrity.sql"):
            await connection.execute((ROOT / "docker/postgres/init-scripts" / filename).read_text(encoding="utf-8"))
    finally:
        await connection.close()
    print(f"Dedicated PostgreSQL test database: {target.database}", flush=True)
    return dsn(target)


async def database_fingerprint(url):
    connection = await asyncpg.connect(url)
    try:
        tables = await connection.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        fingerprints = {}
        for row in tables:
            name = row["tablename"]
            quoted = name.replace('"', '""')
            fingerprints[name] = await connection.fetchval(
                f'''SELECT count(*)::text || ':' || md5(COALESCE(string_agg(
                    row_to_json(t)::text, '' ORDER BY row_to_json(t)::text), ''))
                    FROM "{quoted}" t''')
        return fingerprints
    finally:
        await connection.close()


if __name__ == "__main__":
    target_url = asyncio.run(prepare())
    before = asyncio.run(database_fingerprint(target_url))
    environment = dict(os.environ, TEST_DATABASE_URL=target_url,
                       RUN_COURSE_SCOPE_DB="1", RUN_AVATAR_DB="1", RUN_INTEGRATION_DB="1")
    result = subprocess.call([sys.executable, "-m", "pytest", "apps/backend/tests",
                              *(sys.argv[1:] or ["-q"])], cwd=ROOT, env=environment)
    after = asyncio.run(database_fingerprint(target_url))
    if before != after:
        changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        print("FAIL: test rows were not fully rolled back: " + ", ".join(changed), flush=True)
        result = 1
    else:
        print(f"PASS: row counts and content unchanged across {len(before)} tables after tests", flush=True)
    raise SystemExit(result)
