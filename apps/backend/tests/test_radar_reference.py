import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

import pytest

from services.radar_service import calculate_radar_6d, RADAR_REFERENCE
from schemas.student import RadarDataOut

CASES = json.loads((Path(__file__).resolve().parents[3] /
    'packages/shared/constants/radar-cases.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CASES, ids=[case['name'] for case in CASES])
def test_shared_radar_contract(case):
    dimensions = calculate_radar_6d(case['features'])
    assert [d['reference_score'] for d in dimensions] == case['scores']
    assert all('percentile' not in d for d in dimensions)
    assert RADAR_REFERENCE['status'] == 'illustrative_unvalidated'


@pytest.mark.parametrize('value', [float('inf'), float('nan'), True])
def test_nonfinite_and_boolean_are_not_observations(value):
    assert calculate_radar_6d({'total_clicks_to_t': value})[0]['reference_score'] is None


@pytest.mark.anyio
async def test_radar_endpoint_exposes_reference_and_snapshot_without_percentile(monkeypatch):
    import api.v1.endpoints.student as endpoint
    profile = SimpleNamespace(id=uuid4())
    enrollment = SimpleNamespace(id=uuid4(), presentation_id=uuid4())
    snapshot = SimpleNamespace(**CASES[0]['features'], id=uuid4(), cutoff_stage='CUTOFF_75',
        created_at=datetime.now(timezone.utc), raw_features_json={'data_source': 'synthetic_demo'})

    class Result:
        def __init__(self, value): self.value = value
        def scalars(self): return self
        def first(self): return self.value

    monkeypatch.setattr(endpoint, 'get_student_profile_by_user_id', AsyncMock(return_value=profile))
    db = SimpleNamespace(execute=AsyncMock(side_effect=[Result(enrollment),
        Result((None, SimpleNamespace(code_module='BBB'))), Result(snapshot)]))
    response = await endpoint.get_my_course_radar(enrollment.id, SimpleNamespace(id=uuid4()), db)
    data = RadarDataOut.model_validate(response).model_dump(mode='json')
    assert data['snapshot_id'] == str(snapshot.id)
    assert data['reference_version'] == RADAR_REFERENCE['version']
    assert data['reference_status'] == 'illustrative_unvalidated'
    assert data['data_source'] == 'synthetic_demo'
    assert data['dimensions'][5]['reference_score'] == 50
    assert 'percentile' not in json.dumps(data)
