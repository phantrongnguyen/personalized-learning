"""Snapshot history, provenance and missing-risk semantics; DB fixtures roll back."""
import hashlib
import os
import tempfile
import unittest
import uuid
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from openpyxl import load_workbook
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

import test_course_scope as scope_fixture
import test_database_predictions as feature_fixture
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun, MLModel
from schemas.prediction import StudentFeatures, PredictionRequest
from services import prediction_service
from services.replay_service import replay_prediction
from services.risk_service import current_prediction, student_risk_summary

ARTIFACT = Path(__file__).resolve().parents[1] / "artifacts/model_hco_vnls_lightgbm_cutoff75.joblib"


class InputAndProvenanceTests(unittest.TestCase):
    def test_invalid_counts_ratios_categories_and_nonfinite_values(self):
        valid = prediction_service.database_features(*feature_fixture.records())
        invalid = {
            "total_clicks_to_t": [-1, .5, float("nan"), float("inf")],
            "submission_rate": [-.1, 1.1, float("nan"), float("inf")],
            "active_day_ratio": [-.1, 1.1], "studied_credits": [0, -1, float("inf")],
            "date_registration": [float("nan"), float("inf"), .5],
            "gender": ["X"], "code_module": ["UNKNOWN"],
            "age_band": ["18-23"], "highest_education": ["UNKNOWN"],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValidationError):
                        StudentFeatures(**{**valid, field: value})
        self.assertEqual(StudentFeatures(**{**valid, "date_registration": -45}).date_registration, -45)

    def test_shared_validation_rejects_invalid_database_demographics(self):
        args = feature_fixture.records()
        args[2].age_band = "18-23"
        with self.assertRaises(ValidationError):
            prediction_service.database_features(*args)

    def test_manual_inference_returns_exact_validated_inputs_and_model_identity(self):
        features = prediction_service.database_features(*feature_fixture.records())
        artifact = prediction_service.load_model(ARTIFACT)
        result = prediction_service.PredictionService.execute(artifact, PredictionRequest(features=features))
        self.assertEqual(result.provenance.features.model_dump(), features)
        self.assertEqual(result.provenance.model_sha256, hashlib.sha256(ARTIFACT.read_bytes()).hexdigest())
        self.assertEqual(result.provenance.threshold, artifact["threshold"])

    def test_archived_artifact_and_saved_inputs_replay_after_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.joblib"
            source.write_bytes(ARTIFACT.read_bytes())
            archive = root / "archive"
            artifact = prediction_service.load_model(source, archive_dir=archive)
            features = prediction_service.database_features(*feature_fixture.records())
            run = prediction_service.infer_record(artifact, features, uuid.uuid4(), uuid.uuid4(), None, "frozen-v1")
            original = deepcopy(run.inference_context)
            features["gender"] = "F"
            source.write_bytes(b"Source model replaced")
            self.assertEqual(run.inference_context, original)
            self.assertTrue(replay_prediction(run, archive_dir=archive)["matches_original"])
            archived = archive / f"{original['model_sha256']}.joblib"
            archived.write_bytes(b"Corrupted archive")
            with patch("services.replay_service.load_model") as deserialize:
                with self.assertRaisesRegex(ValueError, "checksum"):
                    replay_prediction(run, archive_dir=archive)
                deserialize.assert_not_called()

    def test_legacy_results_cannot_be_reconstructed_from_current_data(self):
        with self.assertRaisesRegex(ValueError, "Legacy"):
            replay_prediction(SimpleNamespace(inference_context=None))


@unittest.skipUnless(os.getenv("RUN_COURSE_SCOPE_DB") == "1", "Opt in to rollback-only PostgreSQL fixtures")
class PredictionIntegrityTests(unittest.IsolatedAsyncioTestCase):
    # Reuse setup/cleanup without inheriting and duplicating the scope test cases.
    asyncSetUp = scope_fixture.CourseScopeTests.asyncSetUp
    cleanup_fixture = scope_fixture.CourseScopeTests.cleanup_fixture
    request = scope_fixture.CourseScopeTests.request

    async def add_prediction(self, snapshot_id, probability, label):
        run = PredictionRun(snapshot_id=snapshot_id, model_id=self.predictions[0].model_id,
                            prediction_label=label, risk_probability=probability)
        self.db.add(run)
        await self.db.flush()
        return run

    async def test_update_creates_new_snapshot_and_preserves_old_values_and_prediction(self):
        old, run = await current_prediction(self.db, self.enrollments[0].id)
        before = {field: getattr(old, field) for field in prediction_service.BEHAVIOR_FIELDS}
        response = await self.request("PUT",
            f"/lecturer/courses/{self.presentations[0].id}/students/{self.profile.id}/assessment",
            json={"assessments_submitted": 4, "late_submissions": 1, "submission_rate": .8})
        self.assertEqual(response.status_code, 200, response.text)
        fresh, current = await current_prediction(self.db, self.enrollments[0].id)
        await self.db.refresh(old)
        self.assertNotEqual(fresh.id, old.id)
        self.assertEqual({field: getattr(old, field) for field in before}, before)
        self.assertEqual(run.snapshot_id, old.id)
        self.assertEqual(run.risk_probability, .1)
        self.assertIsNone(current)
        self.assertEqual(fresh.assessments_submitted_to_t, 4)
        self.assertEqual(fresh.raw_features_json["snapshot_metadata"]["previous_snapshot_id"], str(old.id))
        self.assertEqual(fresh.raw_features_json["snapshot_metadata"]["updated_by_user_id"], str(self.user.id))

    async def test_new_snapshot_is_not_safe_and_cannot_start_plan_from_old_prediction(self):
        await self.request("PUT",
            f"/lecturer/courses/{self.presentations[0].id}/students/{self.profile.id}/assessment",
            json={"submission_rate": .8})
        response = await self.request("GET", f"/student/courses/{self.enrollments[0].id}/risk-prediction")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["risk_level"], "NOT_PREDICTED")
        self.assertIsNone(response.json()["risk_probability"])
        self.assertEqual(response.json()["pedagogical_recommendations"], [])
        board = await self.request("GET", f"/lecturer/courses/{self.presentations[0].id}/risk-board")
        mine = next(row for row in board.json() if row["student_id"] == str(self.profile.id))
        self.assertIsNone(mine["risk_probability"])
        self.assertEqual(mine["risk_status"], "NOT_PREDICTED")
        overview = await self.request("GET", f"/advisor/students/{self.profile.id}/overview")
        self.assertEqual(overview.json()["latest_risk_level"], "NOT_PREDICTED")
        response = await self.request("POST", "/advisor/interventions",
            json={"student_id": str(self.profile.id), "enrollment_id": str(self.enrollments[0].id)})
        self.assertEqual(response.status_code, 400)

    async def test_missing_snapshot_returns_null_and_progress_update_requires_baseline(self):
        response = await self.request("GET", f"/student/courses/{self.foreign.id}/risk-prediction", self.other_user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk_level"], "NOT_PREDICTED")
        self.assertIsNone(response.json()["snapshot_id"])
        response = await self.request("PUT",
            f"/lecturer/courses/{self.presentations[0].id}/students/{self.other_profile.id}/assessment",
            json={"submission_rate": .8, "final_result": "PASS"})
        self.assertEqual(response.status_code, 409)
        await self.db.refresh(self.foreign)
        self.assertIsNone(self.foreign.final_result)

    async def test_final_result_only_does_not_create_or_change_snapshot(self):
        old, _ = await current_prediction(self.db, self.enrollments[0].id)
        response = await self.request("PUT",
            f"/lecturer/courses/{self.presentations[0].id}/students/{self.profile.id}/assessment",
            json={"final_result": "PASS"})
        self.assertEqual(response.status_code, 200, response.text)
        snapshot, prediction = await current_prediction(self.db, self.enrollments[0].id)
        self.assertEqual(snapshot.id, old.id)
        self.assertIsNotNone(prediction)

    async def test_database_rejects_snapshot_and_prediction_rewrites(self):
        snapshot, prediction = await current_prediction(self.db, self.enrollments[0].id)
        for statement in (
            update(StudentFeatureSnapshot).where(StudentFeatureSnapshot.id == snapshot.id).values(submission_rate=.99),
            update(PredictionRun).where(PredictionRun.id == prediction.id).values(risk_probability=.99),
            update(PredictionRun).where(PredictionRun.id == prediction.id).values(inference_context={"forged": True}),
        ):
            with self.assertRaises(IntegrityError):
                async with self.db.begin_nested():
                    await self.db.execute(statement.execution_options(synchronize_session=False))

    async def test_any_high_risk_course_wins_over_newer_safe_course(self):
        await self.add_prediction(self.predictions[0].snapshot_id, .8, 1)
        await self.add_prediction(self.predictions[1].snapshot_id, .1, 0)
        summary = await student_risk_summary(self.db, self.profile.id)
        self.assertEqual(summary["risk_level"], "HIGH_RISK")
        self.assertEqual(summary["risk_probability"], .8)
        self.assertEqual(summary["high_risk_courses"], 1)

    async def test_risk_uses_recorded_label_instead_of_hardcoded_threshold(self):
        await self.add_prediction(self.predictions[0].snapshot_id, .3, 1)
        board = await self.request("GET", f"/lecturer/courses/{self.presentations[0].id}/risk-board")
        mine = next(row for row in board.json() if row["student_id"] == str(self.profile.id))
        self.assertEqual(mine["risk_status"], "HIGH_RISK")

    async def test_class_statistics_and_export_keep_missing_risk_separate(self):
        # The second student has an enrollment but no snapshot or prediction.
        summary = await student_risk_summary(self.db, self.other_profile.id)
        self.assertEqual(summary["risk_level"], "NOT_PREDICTED")
        class_name = (await self.request("GET", "/advisor/classes", self.other_user)).json()[0]["class_name"]
        stats = await self.request("GET", f"/advisor/classes/{class_name}/statistics", self.other_user)
        self.assertEqual(stats.status_code, 200, stats.text)
        self.assertEqual(stats.json()["safe_count"], 0)
        self.assertEqual(stats.json()["not_predicted_count"], 1)
        self.assertIsNone(stats.json()["avg_risk_probability"])
        response = await self.request("GET", "/advisor/export/risk-report", self.other_user)
        sheet = load_workbook(BytesIO(response.content)).active
        self.assertIsNone(sheet.cell(2, 5).value)
        self.assertEqual(sheet.cell(2, 6).value, "NOT_PREDICTED")
        self.assertEqual(sheet.cell(2, 9).value, 1)

    async def test_all_safe_requires_predictions_for_every_course(self):
        summary = await student_risk_summary(self.db, self.profile.id)
        self.assertEqual(summary["risk_level"], "SAFE")
        snapshot = StudentFeatureSnapshot(enrollment_id=self.enrollments[1].id)
        self.db.add(snapshot)
        await self.db.flush()
        summary = await student_risk_summary(self.db, self.profile.id)
        self.assertEqual(summary["risk_level"], "NOT_PREDICTED")
        self.assertIsNone(summary["risk_probability"])
        self.assertEqual(summary["predicted_courses"], 1)
        await self.add_prediction(self.predictions[0].snapshot_id, .8, 1)
        summary = await student_risk_summary(self.db, self.profile.id)
        self.assertEqual(summary["risk_level"], "HIGH_RISK")
        self.assertEqual(summary["unpredicted_courses"], 1)

    async def test_legacy_prediction_is_identified_without_invented_version(self):
        response = await self.request("GET", f"/student/courses/{self.enrollments[0].id}/risk-prediction")
        self.assertEqual(response.json()["provenance_status"], "LEGACY_UNVERIFIED")
        self.assertIsNone(response.json()["provenance"])
        self.assertIsNone(response.json()["model_version"])

    async def test_saved_context_replays_after_profile_enrollment_and_registry_edits(self):
        course = (await self.db.execute(select(Course).where(Course.code_module == "CCC"))).scalars().first()
        if course is None:
            course = Course(code_module="CCC", name="Trace course")
            self.db.add(course)
            await self.db.flush()
        presentation = CoursePresentation(course_id=course.id, code_presentation=uuid.uuid4().hex[:18], module_presentation_length=268)
        self.db.add(presentation)
        await self.db.flush()
        enrollment = StudentEnrollment(student_id=self.profile.id, presentation_id=presentation.id, studied_credits=60)
        self.db.add(enrollment)
        await self.db.flush()
        fixture_snapshot, _, _, _ = feature_fixture.records()
        snapshot = StudentFeatureSnapshot(enrollment_id=enrollment.id,
            **{field: getattr(fixture_snapshot, field) for field in prediction_service.BEHAVIOR_FIELDS})
        self.db.add(snapshot)
        await self.db.flush()
        artifact = prediction_service.load_model(ARTIFACT)
        features = prediction_service.database_features(snapshot, enrollment, self.profile, course)
        model = await self.db.get(MLModel, self.predictions[0].model_id)
        run = prediction_service.infer_record(artifact, features, snapshot.id, model.id, self.user.id, model.version)
        self.db.add(run)
        await self.db.commit()
        saved = deepcopy(run.inference_context)
        self.profile.gender = "F"
        enrollment.studied_credits = 30
        model.version = f"edited-{uuid.uuid4().hex[:10]}"
        model.threshold = .9
        await self.db.commit()
        await self.db.refresh(run)
        self.assertEqual(run.inference_context, saved)
        self.assertEqual(len(saved["features"]), 17)
        self.assertEqual(saved["features"]["gender"], "M")
        self.assertEqual(saved["threshold"], .5)
        self.assertTrue(replay_prediction(run)["matches_original"])
        response = await self.request("GET", f"/student/courses/{enrollment.id}/risk-prediction")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["model_version"], saved["model_version"])
        self.assertEqual(response.json()["provenance_status"], "VERIFIED")
