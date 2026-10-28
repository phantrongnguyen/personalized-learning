"""Import boundary for E2E only: production has no enrollment/snapshot creation UI."""
import asyncio
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'apps/backend'))
from core.config import settings
from core.database import AsyncSessionLocal, engine
from sqlalchemy import select
from sqlalchemy.engine import make_url
from models.profile import StudentProfile
from models.academic import StudentEnrollment
from models.feature import StudentFeatureSnapshot
import models.user, models.assignment, models.ml, models.intervention, models.help_request, models.audit


async def main():
    database = make_url(settings.database_url).database
    if os.getenv('EDURISK_E2E_RUN') != '1' or not re.fullmatch(r'e2e_[a-f0-9]{12}_test', database or ''):
        raise SystemExit('Disposable E2E database required')
    fixture_path = Path(os.environ['E2E_PRIVATE_DIR']) / 'fixture.json'
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    assert fixture['database_name'] == database
    async with AsyncSessionLocal() as db:
        student = (await db.execute(select(StudentProfile).where(StudentProfile.student_code == fixture['student_code']))).scalar_one()
        enrollment = StudentEnrollment(student_id=student.id, presentation_id=uuid.UUID(fixture['presentation']['id']), studied_credits=60)
        db.add(enrollment); await db.flush()
        snapshot = StudentFeatureSnapshot(enrollment_id=enrollment.id, total_clicks_to_t=12,
            clicks_resource_to_t=4, clicks_url_to_t=2, active_days_to_t=3, active_day_ratio=.04,
            days_since_last_activity=30, clicks_recent_7=0, clicks_recent_30=0,
            assessments_submitted_to_t=1, late_submissions_to_t=1, submission_rate=.1,
            raw_features_json={'data_source': 'synthetic_demo'})
        db.add(snapshot); await db.commit()
        fixture.update(student_id=str(student.id), enrollment_id=str(enrollment.id), snapshot_id=str(snapshot.id))
        fixture_path.write_text(json.dumps(fixture), encoding='utf-8')
    await engine.dispose()


asyncio.run(main())
