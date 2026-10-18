import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import FastAPI, HTTPException
from api.v1.endpoints import admin
from services import prediction_service as service


def records():
    snapshot = SimpleNamespace(id=uuid.uuid4(), cutoff_stage="CUTOFF_75",
        **dict(zip(service.BEHAVIOR_FIELDS, [280, 180, 50, 32, .4, 2, 25, 100, 8, 1, .8])))
    enrollment = SimpleNamespace(studied_credits=2, date_registration=0)
    profile = SimpleNamespace(gender="M", highest_education="HE Qualification", age_band="0-35")
    course = SimpleNamespace(code_module="CCC")
    return snapshot, enrollment, profile, course


class FeatureTests(unittest.TestCase):
    def test_actual_database_features(self):
        values = service.database_features(*records())
        self.assertEqual(len(values), 17)
        self.assertEqual(values["code_module"], "CCC")
        self.assertEqual(values["studied_credits"], 2)
        self.assertEqual(values["submission_rate"], .8)

    def test_invalid_data_rejected(self):
        for field, value in (("submission_rate", 1.2), ("active_day_ratio", -.1),
                             ("total_clicks_to_t", float("nan"))):
            args = records()
            setattr(args[0], field, value)
            with self.assertRaises(ValueError):
                service.database_features(*args)

    def test_model_failure_has_no_fallback(self):
        with patch.object(service, "predict", side_effect=KeyError("feature")):
            with self.assertRaises(KeyError):
                service.infer_record({}, service.database_features(*records()), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())

    def test_real_artifact_inference(self):
        model = service.load_model(Path(__file__).resolve().parents[1] /
            "artifacts/model_hco_vnls_lightgbm_cutoff75.joblib")
        features = service.database_features(*records())
        expected = service.predict(model, features)
        run = service.infer_record(model, features, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        self.assertEqual(run.risk_probability, expected["confidence"])
        self.assertEqual(run.prediction_label, int(run.risk_probability >= model["threshold"]))
        self.assertGreaterEqual(run.execution_time_ms, 0)


class TransactionTests(unittest.IsolatedAsyncioTestCase):
    async def test_student_cannot_trigger_admin_prediction(self):
        app = FastAPI()
        app.include_router(admin.router, prefix="/api/v1/admin")
        async def deny():
            raise HTTPException(403, "Admin only")
        app.dependency_overrides[admin.require_admin] = deny
        app.dependency_overrides[admin.get_db] = lambda: None
        with patch.object(admin, "generate_database_predictions", AsyncMock()) as generate:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/admin/ml/batch-predict")
        self.assertEqual(response.status_code, 403)
        generate.assert_not_awaited()

    async def test_threshold_mismatch_rejected(self):
        model = SimpleNamespace(id=uuid.uuid4(), threshold=.6, cutoff_fraction=.75)
        result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [model]))
        db = SimpleNamespace(execute=AsyncMock(return_value=result), add_all=Mock())
        with patch.object(service, "artifact_path", return_value=Path("dummy")), \
             patch.object(service, "load_model", return_value={"threshold": .5}):
            with self.assertRaises(HTTPException) as error:
                await service.generate_database_predictions(db, uuid.uuid4())
        self.assertEqual(error.exception.status_code, 400)
        db.add_all.assert_not_called()

    async def test_failure_rolls_back(self):
        db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        actor = SimpleNamespace(id=uuid.uuid4())
        with patch.object(admin, "generate_database_predictions", AsyncMock(side_effect=KeyError("feature"))):
            with self.assertRaises(HTTPException) as error:
                await admin.batch_predict_all_students(None, actor, db, uuid.uuid4())
        self.assertEqual(error.exception.status_code, 422)
        db.rollback.assert_awaited_once()
        db.commit.assert_not_awaited()

    async def test_success_commits_audit_and_predictions(self):
        db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        actor = SimpleNamespace(id=uuid.uuid4())
        model = SimpleNamespace(id=uuid.uuid4())
        runs = [SimpleNamespace(prediction_label=1)]
        enrollment_id = uuid.uuid4()
        with patch.object(admin, "generate_database_predictions", AsyncMock(return_value=(model, runs))) as generate, \
             patch.object(admin, "write_audit_log", AsyncMock()) as audit:
            result = await admin.batch_predict_all_students(None, actor, db, enrollment_id)
        generate.assert_awaited_once_with(db, actor.id, enrollment_id)
        audit.assert_awaited_once()
        db.commit.assert_awaited_once()
        self.assertEqual(result["high_risk_count"], 1)

    async def test_partial_inference_never_added(self):
        model = SimpleNamespace(id=uuid.uuid4(), threshold=.5, cutoff_fraction=.75, version="fixture")
        first = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [model]))
        second = SimpleNamespace(all=lambda: [records(), records()])
        db = SimpleNamespace(execute=AsyncMock(side_effect=[first, second]), add_all=Mock())
        with patch.object(service, "artifact_path", return_value=Path("dummy")), \
             patch.object(service, "load_model", return_value={"threshold": .5}), \
             patch.object(service, "infer_record", side_effect=[object(), ValueError("failure")]):
            with self.assertRaises(ValueError):
                await service.generate_database_predictions(db, uuid.uuid4())
        db.add_all.assert_not_called()

    async def test_missing_snapshot(self):
        model = SimpleNamespace(id=uuid.uuid4(), threshold=.5, cutoff_fraction=.75)
        first = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [model]))
        second = SimpleNamespace(all=lambda: [])
        db = SimpleNamespace(execute=AsyncMock(side_effect=[first, second]), add_all=Mock())
        with patch.object(service, "artifact_path", return_value=Path("dummy")), \
             patch.object(service, "load_model", return_value={"threshold": .5}):
            with self.assertRaises(HTTPException) as error:
                await service.generate_database_predictions(db, uuid.uuid4(), uuid.uuid4())
        self.assertEqual(error.exception.status_code, 404)
        db.add_all.assert_not_called()
