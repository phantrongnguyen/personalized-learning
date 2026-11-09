"""Load one prepared OULAD case into an explicitly isolated PostgreSQL database."""
import argparse
import asyncio
import hashlib
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BACKEND = Path(__file__).resolve().parents[1] / "apps/backend"
sys.path.insert(0, str(BACKEND))

from core.security import get_password_hash
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.assignment import CourseLecturer
from models.feature import StudentFeatureSnapshot
from models.profile import LecturerProfile, StudentProfile
from models.user import Role, User
from schemas.prediction import StudentFeatures
from services.model_registry import model_registry
from services.prediction_service import BEHAVIOR_FIELDS, infer_record
from services.support_suggestions import validated_assessment_details
from services.support_evidence import REVIEW_VERSION, snapshot_digest
from services.audit_service import write_audit_log


def verify(case, directory, source_hashes=None):
    features = StudentFeatures(**case["features"])
    if features.code_module != case["module"] or case["cutoff_day"] != int(case["module_length"] * .75):
        raise ValueError("Course or cutoff does not match the features")
    if set(case["source_sha256"]) != {
            "studentInfo", "studentRegistration", "courses", "assessments",
            "studentAssessment", "studentVle", "vle"}:
        raise ValueError("All seven OULAD source checksums are required")
    for name, expected in case["source_sha256"].items():
        if source_hashes is None:
            path = directory / f"{name}.parquet"
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual = digest.hexdigest()
        else:
            actual = source_hashes[name]
        if actual != expected:
            raise ValueError(f"Source changed since export: {name}")
    details = case["assessment_records"]
    snapshot = type("Snapshot", (), {name: getattr(features, name) for name in BEHAVIOR_FIELDS})()
    if validated_assessment_details(snapshot, {"assessment_records": details}, case["cutoff_day"]) is None:
        raise ValueError("Assessment records do not match snapshot features")
    if case["module_length"] <= 0 or case["source"] != "OULAD processed Parquet":
        raise ValueError("Invalid source or presentation length")
    return features


async def load(case, features, url, lecturer_code):
    engine = create_async_engine(url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            course = (await db.execute(select(Course).where(Course.code_module == case["module"]))).scalar_one()
            lecturer = (await db.execute(select(LecturerProfile).where(LecturerProfile.lecturer_code == lecturer_code))).scalar_one()
            role = (await db.execute(select(Role).where(Role.code == "STUDENT"))).scalar_one()
            presentation_code = f"OULAD_{case['presentation']}"
            existing = (await db.execute(select(CoursePresentation).where(
                CoursePresentation.course_id == course.id,
                CoursePresentation.code_presentation == presentation_code))).scalar_one_or_none()
            if existing is not None and existing.module_presentation_length != case["module_length"]:
                raise ValueError("Existing OULAD presentation has a different duration")
            student_code = f"OULAD-{case['student_id']}"
            existing_student = (await db.execute(select(StudentProfile).where(
                StudentProfile.student_code == student_code))).scalar_one_or_none()
            if existing_student is not None:
                raise ValueError("OULAD student already exists; import is not repeatable")
            model, artifact = await model_registry.active(db)
            presentation = existing or CoursePresentation(
                course_id=course.id, code_presentation=presentation_code,
                start_date=None, module_presentation_length=case["module_length"])
            user = User(email=f"oulad-{case['student_id']}@example.invalid",
                        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                        full_name=f"OULAD #{case['student_id']} (dữ liệu lịch sử)", roles=[role])
            db.add_all([presentation, user])
            await db.flush()
            profile = StudentProfile(user_id=user.id, student_code=student_code, gender=features.gender,
                                     highest_education=features.highest_education, age_band=features.age_band)
            db.add(profile)
            assignment = (await db.execute(select(CourseLecturer).where(
                CourseLecturer.presentation_id == presentation.id,
                CourseLecturer.lecturer_id == lecturer.id))).scalar_one_or_none()
            if assignment is None:
                db.add(CourseLecturer(presentation_id=presentation.id, lecturer_id=lecturer.id))
            await db.flush()
            enrollment = StudentEnrollment(student_id=profile.id, presentation_id=presentation.id,
                                            studied_credits=int(features.studied_credits),
                                            date_registration=features.date_registration)
            db.add(enrollment)
            await db.flush()
            metadata = {"support_evidence": {
                "timeline": "relative_course_day", "snapshot_day": case["cutoff_day"],
                "source": case["source"], "source_sha256": case["source_sha256"],
                "confirmed_at": case["confirmed_at"], "activity_complete": True,
                "assessments_complete": True, "assessment_records": case["assessment_records"],
            }}
            snapshot = StudentFeatureSnapshot(enrollment_id=enrollment.id, cutoff_stage="CUTOFF_75",
                                              raw_features_json=metadata,
                                              **{name: getattr(features, name) for name in BEHAVIOR_FIELDS})
            db.add(snapshot)
            await db.flush()
            evidence = metadata["support_evidence"]
            evidence.update(review_version=REVIEW_VERSION, review_scope="source_verified",
                            confirmed_by_user_id=str(lecturer.user_id),
                            confirmed_at=datetime.now(timezone.utc).isoformat(),
                            snapshot_sha256=snapshot_digest(snapshot, presentation))
            snapshot.raw_features_json = {"support_evidence": dict(evidence)}
            await write_audit_log(db, user_id=lecturer.user_id, action="IMPORT_OULAD_EVIDENCE",
                                 target_type="student_feature_snapshot", target_id=snapshot.id,
                                 detail=json.dumps(evidence, ensure_ascii=False))
            run = infer_record(artifact, features.model_dump(), snapshot.id, model.id, lecturer.user_id, model.version)
            db.add(run)
            await db.commit()
            print(f"Imported historical OULAD {presentation_code} / {student_code}; "
                  f"model risk={run.risk_probability:.6f}; no plan/task created")
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--lecturer-code", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url = make_url(args.database_url)
    if not url.database or not url.database.endswith("_oulad"):
        parser.error("Only a separately named *_oulad database is allowed")
    case = json.loads(args.case.read_text(encoding="utf-8-sig"))
    features = verify(case, args.parquet_dir)
    if not args.apply:
        print(f"Verified source hashes and {len(case['assessment_records'])} assessments. "
              "Dry run: no database write. Pass --apply to import into the isolated database.")
        return
    async_url = url.set(drivername="postgresql+asyncpg")
    asyncio.run(load(case, features, async_url.render_as_string(hide_password=False), args.lecturer_code))


if __name__ == "__main__":
    main()
