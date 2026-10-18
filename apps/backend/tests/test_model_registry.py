"""Model contract, atomic activation, per-worker caches and API parity."""
import asyncio
import json
import os
import tempfile
import unittest
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import joblib
from fastapi import HTTPException
from sqlalchemy import select, update, func

import test_course_scope as scope_fixture
import test_database_predictions as feature_fixture
from api.v1.endpoints import admin, health, predictions
from core.database import engine
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import MLModel, PredictionRun
from models.audit import AuditLog
from services import prediction_service
from services.model_registry import ModelRegistry, RUNTIME_KEY, validate_artifact

ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts/model_hco_vnls_lightgbm_cutoff75.joblib"


class ModelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = prediction_service.load_model(ARTIFACT)

    def record(self, **overrides):
        values = dict(id=uuid.uuid4(), version="contract-v1", threshold=.5, cutoff_fraction=.75, metadata_json={})
        return SimpleNamespace(**{**values, **overrides})

    def test_real_artifact_matches_contract(self):
        validate_artifact(self.record(), self.artifact)

    def test_threshold_cutoff_columns_positive_label_and_checksum_must_match(self):
        for metadata in ({"threshold": .7}, {"cutoff_fraction": .5},
                         {"positive_label": 0}, {"feature_columns": []},
                         {"features_count": 18}, {"model_sha256": "0" * 64}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                validate_artifact(self.record(metadata_json=metadata), self.artifact)
        for values in (dict(threshold=.7), dict(threshold=float("nan")), dict(cutoff_fraction=.5)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_artifact(self.record(**values), self.artifact)

    def test_artifact_requires_complete_metadata_and_pipeline(self):
        for changes in ({"metadata": {}}, {"pipeline": None}, {"feature_columns": []},
                        {"cutoff_fraction": .5}, {"threshold": .7}):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                validate_artifact(self.record(), {**self.artifact, **changes})

    def test_sidecar_contract_is_checked(self):
        with self.assertRaises(ValueError):
            validate_artifact(self.record(), self.artifact, {"positive_label": 0})


@unittest.skipUnless(os.getenv("RUN_COURSE_SCOPE_DB") == "1", "Opt in to rollback-only PostgreSQL fixtures")
class ModelRegistryDatabaseTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUpBase = scope_fixture.CourseScopeTests.asyncSetUp
    cleanup_fixture = scope_fixture.CourseScopeTests.cleanup_fixture
    request = scope_fixture.CourseScopeTests.request

    async def asyncSetUp(self):
        await self.asyncSetUpBase()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = ModelRegistry(archive_dir=self.root / "archive")
        self.admin = SimpleNamespace(id=self.user.id, roles=[SimpleNamespace(code="ADMIN")])
        for module in (admin, health, predictions, prediction_service):
            patcher = patch.object(module, "model_registry", self.registry)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app.include_router(admin.router, prefix="/api/v1/admin")
        self.app.include_router(predictions.router, prefix="/api/v1/predictions")
        self.app.include_router(health.router, prefix="/api/v1")
        await self.db.execute(update(MLModel).values(is_active=False))
        source = prediction_service.load_model(ARTIFACT, archive_dir=self.root / "archive")
        self.first = await self.add_model(source, 1., "first")
        self.second = await self.add_model(source, 0., "second")
        self.first_id, self.second_id = self.first.id, self.second.id
        course = (await self.db.execute(select(Course).where(Course.code_module == "CCC"))).scalars().first()
        if course is None:
            course = Course(code_module="CCC", name="Registry test")
            self.db.add(course)
            await self.db.flush()
        presentation = CoursePresentation(course_id=course.id, code_presentation=uuid.uuid4().hex[:18], module_presentation_length=268)
        self.db.add(presentation)
        await self.db.flush()
        enrollment = StudentEnrollment(student_id=self.profile.id, presentation_id=presentation.id, studied_credits=2, date_registration=0)
        self.db.add(enrollment)
        await self.db.flush()
        fixture, _, _, _ = feature_fixture.records()
        snapshot = StudentFeatureSnapshot(enrollment_id=enrollment.id,
            **{field: getattr(fixture, field) for field in prediction_service.BEHAVIOR_FIELDS})
        self.db.add(snapshot)
        await self.db.flush()
        self.features = prediction_service.database_features(snapshot, enrollment, self.profile, course)
        self.enrollment_id = enrollment.id
        # Keep all fixture data in the outer transaction even when an API rolls
        # back its own savepoint. Nothing is committed to the actual database.
        await self.db.commit()
        await self.registry.activate(self.db, self.first_id)
        await self.db.commit()

    async def add_model(self, source, threshold, name):
        value = {key: item for key, item in source.items() if key != "_provenance"}
        value["metadata"] = {**source["metadata"], "threshold": threshold}
        value["threshold"] = threshold
        path = self.root / f"{name}.joblib"
        joblib.dump(value, path)
        record = MLModel(model_name=name, version=f"{name}-{uuid.uuid4().hex[:10]}",
            model_file_path=str(path), threshold=threshold, cutoff_fraction=.75,
            metadata_json={"positive_label": 1, "features_count": 17}, is_active=False)
        self.db.add(record)
        await self.db.flush()
        return record

    async def activate(self, model_id):
        return await self.request("POST", "/admin/ml/models/activate", self.admin, json={"model_id": str(model_id)})

    async def predict(self):
        return await self.request("POST", "/predictions/", self.admin, json={"features": self.features})

    async def test_activation_updates_manual_batch_and_other_worker_on_next_request(self):
        worker = ModelRegistry(archive_dir=self.registry.archive_dir)
        old_record, _ = await worker.active(self.db)
        self.assertEqual(old_record.id, self.first_id)
        old_prediction = await self.predict()
        switched = await self.activate(self.second_id)
        self.assertEqual(switched.status_code, 200, switched.text)
        manual = await self.predict()
        batch = await self.request("POST", f"/admin/ml/batch-predict?enrollment_id={self.enrollment_id}", self.admin)
        self.assertEqual(manual.status_code, 200, manual.text)
        self.assertEqual(batch.status_code, 200, batch.text)
        run = (await self.db.execute(select(PredictionRun)
            .where(PredictionRun.model_id == self.second_id))).scalars().one()
        self.assertEqual(run.risk_probability, manual.json()["confidence"])
        self.assertEqual(run.prediction_label, manual.json()["prediction"])
        self.assertEqual(run.inference_context, manual.json()["provenance"])
        self.assertEqual(batch.json()["model_id"], str(self.second_id))
        self.assertEqual(batch.json()["threshold"], 0.)
        self.assertNotEqual(old_prediction.json()["prediction"], manual.json()["prediction"])
        new_record, new_artifact = await worker.active(self.db)
        self.assertEqual(new_record.id, self.second_id)
        self.assertEqual(new_artifact["_provenance"]["model_id"], str(self.second_id))

    async def test_reload_uses_active_record_and_ignores_model_path_setting(self):
        await self.activate(self.second_id)
        from core.config import settings
        with patch.object(settings, "model_path", self.root / "missing-configured-model.joblib"):
            result = await self.request("POST", "/admin/ml/reload", self.admin)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["model"]["model_id"], str(self.second_id))
        self.assertEqual((await self.predict()).json()["provenance"]["model_id"], str(self.second_id))

    async def test_missing_corrupt_and_incompatible_candidate_keep_previous_model(self):
        for kind in ("missing", "corrupt", "threshold", "metadata"):
            record = await self.db.get(MLModel, self.second_id)
            path = Path(record.model_file_path)
            original = path.read_bytes()
            old_threshold = record.threshold
            if kind == "missing":
                path.unlink()
            elif kind == "corrupt":
                path.write_bytes(b"invalid artifact")
            elif kind == "threshold":
                record.threshold = .6
            else:
                record.metadata_json = {"positive_label": 0}
            await self.db.commit()
            response = await self.activate(self.second_id)
            self.assertEqual(response.status_code, 422, response.text)
            active, _ = await self.registry.active(self.db)
            self.assertEqual(active.id, self.first_id)
            self.assertEqual((await self.predict()).status_code, 200)
            path.write_bytes(original)
            record = await self.db.get(MLModel, self.second_id)
            record.threshold = old_threshold
            record.metadata_json = {"positive_label": 1, "features_count": 17}
            await self.db.commit()

    async def test_failed_reload_keeps_pinned_artifact_available_to_all_workers(self):
        original = (await self.predict()).json()
        Path(self.first.model_file_path).write_bytes(b"replaced source")
        response = await self.request("POST", "/admin/ml/reload", self.admin)
        self.assertEqual(response.status_code, 422, response.text)
        current = (await self.predict()).json()
        self.assertEqual(current, original)
        worker = ModelRegistry(archive_dir=self.registry.archive_dir)
        record, _ = await worker.active(self.db)
        self.assertEqual(record.id, self.first_id)

    async def test_commit_failure_rolls_back_activation_and_audit(self):
        with patch.object(self.db, "commit", AsyncMock(side_effect=RuntimeError("Commit failed"))):
            response = await self.activate(self.second_id)
        self.assertEqual(response.status_code, 500)
        record, _ = await self.registry.active(self.db)
        self.assertEqual(record.id, self.first_id)
        count = (await self.db.execute(select(func.count()).select_from(AuditLog)
            .where(AuditLog.target_id == self.second_id))).scalar_one()
        self.assertEqual(count, 0)

    async def test_missing_model_id_is_404_and_role_gate_rejects_student(self):
        response = await self.activate(uuid.uuid4())
        self.assertEqual(response.status_code, 404)
        student = SimpleNamespace(id=self.admin.id, roles=[SimpleNamespace(code="STUDENT")])
        response = await self.request("POST", "/admin/ml/models/activate", student, json={"model_id": str(self.second_id)})
        self.assertEqual(response.status_code, 403)

    async def test_no_or_multiple_active_models_fail_closed_instead_of_using_cache(self):
        for count in (0, 2):
            await self.db.execute(update(MLModel).values(is_active=False))
            if count:
                await self.db.execute(update(MLModel).where(MLModel.id.in_([self.first_id, self.second_id])).values(is_active=True))
            await self.db.commit()
            response = await self.predict()
            self.assertEqual(response.status_code, 503, response.text)
            health_response = await self.request("GET", "/health", self.admin)
            self.assertEqual(health_response.status_code, 503)
            self.assertFalse(health_response.json()["model_loaded"])

    async def test_registry_edits_cannot_reuse_old_cache_identity(self):
        record = await self.db.get(MLModel, self.first_id)
        record.threshold = .7
        await self.db.commit()
        self.assertEqual((await self.predict()).status_code, 503)

    async def test_changed_artifact_cannot_replace_pinned_version(self):
        path = Path(self.first.model_file_path)
        altered = joblib.load(path)
        altered["metadata"]["revision_note"] = "New bytes, unchanged schema and threshold"
        joblib.dump(altered, path)
        response = await self.activate(self.first_id)
        self.assertEqual(response.status_code, 422)
        self.assertEqual((await self.predict()).status_code, 200)

    async def test_sidecar_checksum_mismatch_cannot_activate(self):
        sidecar = self.root / "metadata.json"
        sidecar.write_text(json.dumps({"model_sha256": "0" * 64}), encoding="utf-8")
        self.second.metadata_json = {"metadata_file_path": str(sidecar)}
        await self.db.commit()
        response = await self.activate(self.second_id)
        self.assertEqual(response.status_code, 422)
        self.assertEqual((await self.predict()).json()["provenance"]["model_id"], str(self.first_id))

    async def test_legacy_registry_record_is_initialized_and_pinned(self):
        self.first.metadata_json = {"positive_label": 1, "features_count": 17}
        await self.db.commit()
        worker = ModelRegistry(archive_dir=self.registry.archive_dir)
        record, artifact = await worker.initialize(self.db)
        await self.db.commit()
        self.assertEqual(record.metadata_json[RUNTIME_KEY]["model_sha256"], artifact["_provenance"]["model_sha256"])
        self.assertEqual(record.metadata_json[RUNTIME_KEY]["model_id"], str(self.first_id))

    async def test_cold_worker_rejects_corrupted_archive(self):
        _, artifact = await self.registry.active(self.db)
        archived = self.registry.archive_dir / f"{artifact['_provenance']['model_sha256']}.joblib"
        archived.write_bytes(b"Corrupted archived bytes")
        worker = ModelRegistry(archive_dir=self.registry.archive_dir)
        with self.assertRaises(HTTPException) as error:
            await worker.active(self.db)
        self.assertEqual(error.exception.status_code, 503)

    async def test_startup_without_active_registry_does_not_fall_back_to_config(self):
        import main
        await self.db.execute(update(MLModel).values(is_active=False))
        await self.db.commit()
        @asynccontextmanager
        async def session():
            yield self.db
        with patch.object(main, "AsyncSessionLocal", session), patch.object(main, "model_registry", self.registry):
            with self.assertRaises(HTTPException) as error:
                async with main.lifespan(self.app):
                    self.fail("Startup must reject missing active model")
        self.assertEqual(error.exception.status_code, 503)

    async def test_startup_and_health_resolve_database_active_model(self):
        import main
        await self.activate(self.second_id)
        @asynccontextmanager
        async def session():
            yield self.db
        fresh_worker = ModelRegistry(archive_dir=self.registry.archive_dir)
        with patch.object(main, "AsyncSessionLocal", session), patch.object(main, "model_registry", fresh_worker):
            async with main.lifespan(self.app):
                model, artifact = await fresh_worker.active(self.db)
                self.assertEqual(model.id, self.second_id)
                self.assertEqual(artifact["_provenance"]["threshold"], 0.)
        response = await self.request("GET", "/health", self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model"]["model_id"], str(self.second_id))


@unittest.skipUnless(os.getenv("RUN_COURSE_SCOPE_DB") == "1", "Opt in to PostgreSQL advisory lock verification")
class RegistryLockTests(unittest.IsolatedAsyncioTestCase):
    async def test_registry_mutations_serialize_across_connections(self):
        registry = ModelRegistry()
        async with engine.connect() as first, engine.connect() as second:
            transaction1 = await first.begin()
            transaction2 = await second.begin()
            try:
                await registry._lock(first)
                waiting = asyncio.create_task(registry._lock(second))
                await asyncio.sleep(.05)
                self.assertFalse(waiting.done())
                await transaction1.rollback()
                await asyncio.wait_for(waiting, timeout=3)
            finally:
                if transaction1.is_active:
                    await transaction1.rollback()
                await transaction2.rollback()
        await engine.dispose()
