"""Run active-model inference for one enrollment; --save persists with audit."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from core.database import AsyncSessionLocal, engine
from models.user import User, Role
from models.profile import StudentProfile
from models.academic import StudentEnrollment, CoursePresentation, Course
from services.prediction_service import generate_database_predictions
from services.audit_service import write_audit_log
from repositories.student_repo import get_enrollment_prediction
from api.v1.endpoints.student import get_my_course_radar


async def execute(args):
    try:
        async with AsyncSessionLocal() as db:
            admin = (await db.execute(select(User).where(
                User.email == args.admin_email,
                User.is_active == True,
                User.roles.any(Role.code == "ADMIN"),
            ))).scalar_one()
            row = (await db.execute(
                select(StudentEnrollment, StudentProfile, User)
                .join(StudentProfile, StudentProfile.id == StudentEnrollment.student_id)
                .join(User, User.id == StudentProfile.user_id)
                .join(CoursePresentation, CoursePresentation.id == StudentEnrollment.presentation_id)
                .join(Course, Course.id == CoursePresentation.course_id)
                .where(StudentProfile.student_code == args.student_code,
                       Course.code_module == args.course_code,
                       CoursePresentation.code_presentation == args.presentation)
            )).one()
            enrollment, profile, student = row
            model, runs = await generate_database_predictions(db, admin.id, enrollment.id)
            run = runs[0]
            output = {
                "saved": args.save, "student_code": args.student_code,
                "code_module": args.course_code, "enrollment_id": str(enrollment.id),
                "snapshot_id": str(run.snapshot_id), "model_id": str(model.id),
                "model_version": model.version, "threshold": model.threshold,
                "risk_probability": run.risk_probability,
                "prediction_label": run.prediction_label,
                "execution_time_ms": run.execution_time_ms,
            }
            if args.save:
                await write_audit_log(
                    db, user_id=admin.id, action="PREDICT_ENROLLMENT",
                    target_type="ML_MODEL", target_id=model.id,
                    detail=f"CLI inference: enrollment={enrollment.id}; snapshot={run.snapshot_id}",
                )
                await db.commit()
                output["prediction_run_id"] = str(run.id)
                output["student_prediction"] = await get_enrollment_prediction(db, enrollment.id, profile.id)
                output["student_radar"] = await get_my_course_radar(enrollment.id, student, db)
            else:
                await db.rollback()
            print(json.dumps(output, ensure_ascii=False, default=str, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-code", required=True)
    parser.add_argument("--course-code", required=True)
    parser.add_argument("--presentation", default="2013J")
    parser.add_argument("--admin-email", default="admin@huit.edu.vn")
    parser.add_argument("--save", action="store_true")
    asyncio.run(execute(parser.parse_args()))
