from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from schemas.support_evidence import SnapshotReviewIn
from services.support_evidence import inspection, review_snapshot, snapshot_digest
from services.support_suggestions import evaluate_suggestions
from test_support_suggestions import fixture


def payload(snapshot, presentation, **changes):
    values = dict(snapshot_sha256=snapshot_digest(snapshot, presentation), review_scope='source_verified',
        source_reference='database-fixture-source', review_note='Test-only reviewer checked a complete fixture source.',
        activity_complete=True, assessments_complete=True, acknowledged_limitations=True)
    values.update(changes)
    return SnapshotReviewIn(**values)


def test_aggregate_review_cannot_claim_source_complete():
    snapshot, presentation = fixture()
    with pytest.raises(ValidationError): payload(snapshot, presentation, review_scope='aggregate_only')
    with pytest.raises(ValidationError): payload(snapshot, presentation, acknowledged_limitations=False)
    with pytest.raises(ValidationError): payload(snapshot, presentation, confirmed_by_user_id=str(uuid4()))
    with pytest.raises(ValidationError): payload(snapshot, presentation, activity_complete='true')


def test_legacy_and_changed_content_require_new_review():
    snapshot, presentation = fixture()
    snapshot.total_clicks_to_t += 1
    assert evaluate_suggestions(snapshot, presentation)[0] == 'insufficient_data'
    snapshot, presentation = fixture()
    del snapshot.raw_features_json['support_evidence']['review_version']
    assert evaluate_suggestions(snapshot, presentation)[0] == 'insufficient_data'


def test_partial_reviews_do_not_enable_unconfirmed_rules():
    snapshot, presentation = fixture(metadata={'activity_complete': False})
    assert [r['rule_id'] for r in evaluate_suggestions(snapshot, presentation)[1]] == ['G02_AGGREGATE']
    snapshot, presentation = fixture(metadata={'assessments_complete': False})
    assert [r['rule_id'] for r in evaluate_suggestions(snapshot, presentation)[1]] == ['G03']


@pytest.mark.anyio
async def test_demo_cannot_be_promoted_to_real_source():
    snapshot, presentation = fixture()
    snapshot.raw_features_json['data_source'] = 'synthetic_demo'
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    with pytest.raises(HTTPException) as error:
        await review_snapshot(db, snapshot, presentation, payload(snapshot, presentation), uuid4())
    assert error.value.status_code == 422
    db.add.assert_not_called()


@pytest.mark.anyio
async def test_stale_digest_and_contradictions_rejected_before_writes():
    snapshot, presentation = fixture()
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    request = payload(snapshot, presentation)
    snapshot.total_clicks_to_t += 1
    with pytest.raises(HTTPException) as error:
        await review_snapshot(db, snapshot, presentation, request, uuid4())
    assert error.value.status_code == 409
    snapshot.clicks_recent_7 = 99
    with pytest.raises(HTTPException) as error:
        await review_snapshot(db, snapshot, presentation, payload(snapshot, presentation), uuid4())
    assert error.value.status_code == 422
    db.add.assert_not_called()


@pytest.mark.anyio
async def test_review_clones_snapshot_with_actor_hash_and_audit():
    snapshot, presentation = fixture()
    old_id, old_raw = snapshot.id, snapshot.raw_features_json
    actor = uuid4()
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    result = await review_snapshot(db, snapshot, presentation,
        payload(snapshot, presentation, review_scope='demonstration'), actor)
    new = db.add.call_args_list[0].args[0]
    assert new.id != old_id and snapshot.raw_features_json is old_raw
    assert new.raw_features_json['support_evidence']['confirmed_by_user_id'] == str(actor)
    assert new.raw_features_json['data_source'] == 'synthetic_demo'
    assert snapshot_digest(new, presentation) == new.raw_features_json['support_evidence']['snapshot_sha256']
    state, suggestions, warnings, _ = evaluate_suggestions(new, presentation)
    assert state == 'available' and suggestions
    assert any('minh họa' in warning for warning in warnings)
    assert result['snapshot_id'] == new.id
    assert db.add.call_args_list[1].args[0].action == 'REVIEW_SUPPORT_EVIDENCE'
    db.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_aggregate_only_review_stays_insufficient():
    snapshot, presentation = fixture()
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    await review_snapshot(db, snapshot, presentation, payload(snapshot, presentation,
        review_scope='aggregate_only', activity_complete=False, assessments_complete=False), uuid4())
    reviewed = db.add.call_args_list[0].args[0]
    assert evaluate_suggestions(reviewed, presentation)[0] == 'insufficient_data'


def test_inspection_does_not_reinterpret_created_at_as_cutoff():
    snapshot, presentation = fixture()
    presentation.start_date = None
    assert inspection(snapshot, presentation)['cutoff_date'] is None
    assert inspection(snapshot, presentation)['issues']
