"""Build and run real-browser tests against a disposable local PostgreSQL database."""
import asyncio
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
import asyncpg
import httpx
from sqlalchemy.engine import make_url
from core.config import settings


async def provision(url, name):
    admin = await asyncpg.connect(url.set(database='postgres').render_as_string(hide_password=False))
    try: await admin.execute(f'CREATE DATABASE "{name}"')
    finally: await admin.close()


async def seed(url):
    connection = await asyncpg.connect(url.render_as_string(hide_password=False))
    try: await connection.execute((ROOT / 'docker/postgres/init-scripts/02_seed_data.sql').read_text(encoding='utf-8'))
    finally: await connection.close()


async def dispose(url, name):
    admin = await asyncpg.connect(url.set(database='postgres').render_as_string(hide_password=False))
    try: await admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')
    finally: await admin.close()


def main():
    source = make_url(settings.database_url).set(drivername='postgresql')
    if source.host not in ('localhost', '127.0.0.1', '::1'):
        raise SystemExit('Browser runner only supports a local PostgreSQL instance')
    name = 'e2e_' + uuid.uuid4().hex[:12] + '_test'
    target = source.set(database=name)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); port = listener.getsockname()[1]
    evidence = ROOT / 'reports/test-results/browser'
    evidence.mkdir(parents=True, exist_ok=True)
    private = ROOT / '.cache' / name
    private.mkdir(parents=True)
    base = f'http://127.0.0.1:{port}'
    env = dict(os.environ, DATABASE_URL=target.render_as_string(hide_password=False),
        SECRET_KEY=secrets.token_hex(32), AVATAR_UPLOAD_DIR=str(private / 'avatars'),
        E2E_BASE_URL=base, E2E_DATABASE_NAME=name, EDURISK_E2E_RUN='1',
        E2E_PRIVATE_DIR=str(private), E2E_PYTHON=sys.executable, PYTHONIOENCODING='utf-8')
    process = None
    created = False
    result = 1
    try:
        subprocess.run(['npm.cmd' if os.name == 'nt' else 'npm', '--prefix', 'apps/frontend', 'run', 'build'], cwd=ROOT, check=True)
        asyncio.run(provision(source, name)); created = True
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT, env=env, check=True)
        asyncio.run(seed(target))
        with (private / 'server.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(port)],
                cwd=ROOT / 'apps/backend', env=env, stdout=log, stderr=subprocess.STDOUT)
        with httpx.Client(base_url=base, timeout=10) as client:
            for _ in range(60):
                try:
                    if client.get('/api/v1/health').is_success: break
                except httpx.HTTPError: pass
                if process.poll() is not None: raise RuntimeError('Isolated backend did not start; inspect private server log')
                time.sleep(.5)
            else: raise RuntimeError('Isolated backend health timeout')
            login = client.post('/api/v1/auth/login', json={'username': 'admin@huit.edu.vn', 'password': 'admin'})
            login.raise_for_status()
            client.headers['Authorization'] = 'Bearer ' + login.json()['access_token']
            suffix = name[4:16]
            fixture = {'password': 'Browser-fixture-123!', 'student_code': f'E2E{suffix}',
                'student_email': f'student-{suffix}@example.com', 'base_url': base, 'database_name': name}
            for role in ('ADVISOR', 'LECTURER'):
                email = f'{role.lower()}-{suffix}@example.com'
                response = client.post('/api/v1/admin/users', json={'email': email, 'full_name': f'E2E {role}',
                    'password': fixture['password'], 'role_codes': [role],
                    'department': 'E2E fixture', 'lecturer_code': f'L{suffix}' if role == 'LECTURER' else None})
                response.raise_for_status(); fixture[role.lower()] = response.json()
            courses = client.get('/api/v1/admin/academic/courses').json()
            course = next(row for row in courses if row['code_module'] == 'BBB')
            from datetime import datetime, timedelta, timezone
            response = client.post('/api/v1/admin/academic/presentations', json={'course_id': course['id'],
                'code_presentation': 'E2E-' + suffix, 'module_presentation_length': 100,
                'start_date': (datetime.now(timezone.utc) - timedelta(days=100)).date().isoformat()})
            response.raise_for_status(); fixture['presentation'] = response.json()
            foreign = client.post('/api/v1/admin/academic/presentations', json={'course_id': course['id'],
                'code_presentation': 'FOREIGN-' + suffix, 'module_presentation_length': 100})
            foreign.raise_for_status(); fixture['foreign_presentation'] = foreign.json()
            response = client.post('/api/v1/admin/academic/assign-lecturer', json={
                'lecturer_id': fixture['lecturer']['lecturer_profile']['id'], 'presentation_id': fixture['presentation']['id']})
            response.raise_for_status()
            (private / 'fixture.json').write_text(json.dumps(fixture), encoding='utf-8')
        result = subprocess.call(['node', 'node_modules/@playwright/test/cli.js', 'test', '--config=playwright.config.ts'],
            cwd=ROOT / 'apps/frontend', env=env)
    finally:
        if process is not None:
            process.terminate()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
        if created: asyncio.run(dispose(source, name))
        import hashlib
        diff = subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=ROOT)
        names = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
        manifest = {}
        for filename in sorted(set(names)):
            path = ROOT / filename
            if filename.startswith(('apps/', 'packages/', 'scripts/', 'tests/', 'docker/')) and path.is_file():
                manifest[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode()
        (evidence / 'source-manifest.json').write_bytes(manifest_bytes)
        metadata = {'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'tracked_diff_sha256': hashlib.sha256(diff).hexdigest(),
            'source_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(), 'database_name': name,
            'database_disposed': created, 'base_url': base, 'exit_code': result,
            'scope': 'Built React + real FastAPI + PostgreSQL + real artifact; account/import boundaries documented separately'}
        (evidence / 'run.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    raise SystemExit(result)


if __name__ == '__main__': main()
