"""Read-only aggregate inventory; no student identifiers or credentials in output."""
import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/backend'))
import asyncpg
from sqlalchemy.engine import make_url
from core.config import settings
from services.support_evidence import inspection
from services.support_suggestions import evaluate_suggestions


async def inventory():
    url = make_url(settings.database_url).set(drivername='postgresql')
    connection = await asyncpg.connect(url.render_as_string(hide_password=False))
    counts, issues, sources, keys = Counter(), Counter(), Counter(), Counter()
    try:
        async with connection.transaction(isolation='repeatable_read', readonly=True):
            rows = await connection.fetch('''SELECT s.*, p.id AS presentation_id,
                p.start_date, p.module_presentation_length FROM student_feature_snapshots s
                JOIN student_enrollments e ON e.id=s.enrollment_id
                JOIN course_presentations p ON p.id=e.presentation_id''')
            for row in rows:
                values = dict(row)
                raw = json.loads(values['raw_features_json']) if values['raw_features_json'] else {}
                values['raw_features_json'] = raw
                snapshot = SimpleNamespace(**values)
                presentation = SimpleNamespace(id=row['presentation_id'], start_date=row['start_date'],
                    module_presentation_length=row['module_presentation_length'])
                status, _, _, _ = evaluate_suggestions(snapshot, presentation)
                counts[status] += 1
                preview = inspection(snapshot, presentation)
                issues.update(preview['issues'])
                source = raw.get('data_source') if isinstance(raw, dict) else None
                sources[source if source in ('synthetic_demo', None) else 'other_declared_source'] += 1
                if isinstance(raw, dict): keys.update(raw.keys())
                if isinstance(raw, dict) and raw.get('support_evidence'): counts['with_support_evidence'] += 1
            tables = await connection.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    finally:
        await connection.close()
    return {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'read_only': True,
        'snapshots': len(rows), 'with_support_evidence': counts.pop('with_support_evidence', 0), 'statuses': dict(counts),
        'sources': {key or 'unknown': value for key, value in sources.items()},
        'metadata_keys': dict(keys), 'inspection_issues': dict(issues),
        'public_tables': [row['tablename'] for row in tables],
        'limitation': 'Aggregate consistency does not establish completeness of source logs or assessments.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(asyncio.run(inventory()), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + '\n', encoding='utf-8', newline='\n')
        print('Read-only inventory saved; no student identifiers exported.')
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(result)
