"""Prepare one historical OULAD enrollment for an isolated app database."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from math import floor
from pathlib import Path

import pandas as pd

FILES = ("studentInfo", "studentRegistration", "courses", "assessments", "studentAssessment", "studentVle", "vle")


def build_case(directory, module, presentation, student_id):
    directory = Path(directory)
    sources = {name: directory / f"{name}.parquet" for name in FILES}
    for path in sources.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    filters = [("code_module", "=", module), ("code_presentation", "=", presentation)]
    info = pd.read_parquet(sources["studentInfo"], filters=filters)
    info = info[info.id_student.eq(student_id)]
    course = pd.read_parquet(sources["courses"], filters=filters)
    registration = pd.read_parquet(sources["studentRegistration"], filters=filters)
    registration = registration[registration.id_student.eq(student_id)]
    if len(info) != 1 or len(course) != 1 or len(registration) != 1:
        raise ValueError("Expected one enrollment, course and registration")
    student, course_row, registered = info.iloc[0], course.iloc[0], registration.iloc[0]
    if int(course_row.module_presentation_length) <= 0:
        raise ValueError("Course duration must be positive")
    cutoff = floor(int(course_row.module_presentation_length) * .75)
    if (pd.isna(registered.date_registration) or registered.date_registration > cutoff
            or (pd.notna(registered.date_unregistration) and registered.date_unregistration <= cutoff)):
        raise ValueError("Student was not enrolled at the observation day")

    assessments = pd.read_parquet(sources["assessments"], filters=filters)
    due = assessments[assessments.date.notna() & assessments.date.le(cutoff)]
    if due.empty or due.id_assessment.duplicated().any():
        raise ValueError("Assessment schedule is empty or ambiguous")
    submissions = pd.read_parquet(sources["studentAssessment"])
    submissions = submissions[submissions.id_student.eq(student_id)
                              & submissions.id_assessment.isin(due.id_assessment)
                              & submissions.date_submitted.le(cutoff)]
    if submissions.id_assessment.duplicated().any():
        raise ValueError("Multiple submissions per assessment need manual review")
    submitted_by_id = submissions.set_index("id_assessment")
    details = []
    for assignment in due.sort_values("date").itertuples():
        submission = submitted_by_id.loc[assignment.id_assessment] if assignment.id_assessment in submitted_by_id.index else None
        details.append({"id": int(assignment.id_assessment), "type": str(assignment.assessment_type),
                        "due_day": int(assignment.date),
                        "submitted_day": None if submission is None else int(submission.date_submitted),
                        "score": None if submission is None or pd.isna(submission.score) else float(submission.score)})

    activity = pd.read_parquet(sources["studentVle"], filters=filters)
    activity = activity[activity.id_student.eq(student_id) & activity.date.le(cutoff)]
    sites = pd.read_parquet(sources["vle"], filters=filters)
    if sites.id_site.duplicated().any():
        raise ValueError("VLE site identifiers are ambiguous")
    activity = activity.merge(sites[["id_site", "activity_type"]], on="id_site", how="left", validate="many_to_one")
    if activity.activity_type.isna().any():
        raise ValueError("VLE log contains sites missing from the catalog")
    clicks = int(activity.sum_click.sum())
    active_days = int(activity.date.nunique())
    since = cutoff - int(activity.date.max()) if not activity.empty else cutoff + 1
    recent = activity[activity.date.ge(0)]
    submitted = sum(item["submitted_day"] is not None for item in details)
    late = sum(item["submitted_day"] is not None and item["submitted_day"] > item["due_day"] for item in details)
    features = {
        "code_module": module, "gender": str(student.gender),
        "highest_education": str(student.highest_education), "age_band": str(student.age_band),
        "studied_credits": int(student.studied_credits), "date_registration": int(registered.date_registration),
        "total_clicks_to_t": clicks,
        "clicks_resource_to_t": int(activity.loc[activity.activity_type.eq("resource"), "sum_click"].sum()),
        "clicks_url_to_t": int(activity.loc[activity.activity_type.eq("url"), "sum_click"].sum()),
        "active_days_to_t": active_days, "active_day_ratio": active_days / max(1, cutoff),
        "days_since_last_activity": since,
        "clicks_recent_7": int(recent.loc[recent.date.gt(cutoff - 7), "sum_click"].sum()),
        "clicks_recent_30": int(recent.loc[recent.date.gt(cutoff - 30), "sum_click"].sum()),
        "assessments_submitted_to_t": submitted, "late_submissions_to_t": late,
        "submission_rate": submitted / len(details),
    }
    sha = {}
    for name, path in sources.items():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        sha[name] = digest.hexdigest()
    return {
        "source": "OULAD processed Parquet", "source_sha256": sha,
        "module": module, "presentation": presentation, "student_id": student_id,
        "module_length": int(course_row.module_presentation_length), "cutoff_day": cutoff,
        "features": features, "assessment_records": details,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--module", default="AAA")
    parser.add_argument("--presentation", default="2013J")
    parser.add_argument("--student-id", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    case = build_case(args.parquet_dir, args.module, args.presentation, args.student_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {case['module']}/{case['presentation']} student {case['student_id']}: "
          f"{len(case['assessment_records'])} due assessments at day {case['cutoff_day']}; "
          f"saved to {args.output}")


if __name__ == "__main__":
    main()
