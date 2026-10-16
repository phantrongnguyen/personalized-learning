"""Course reminders derived from active intervention plans, without duplicate records."""
import hashlib
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.feature import StudentFeatureSnapshot
from models.ml import PredictionRun
from models.intervention import InterventionPlan, InterventionTask


def build_course_reminders(rows, today: date):
    grouped = {}
    for task, plan, enrollment, course, presentation in rows:
        if task.is_completed or plan.status != "ACTIVE":
            continue
        group = grouped.setdefault(enrollment.id, {
            "enrollment_id": enrollment.id, "code_module": course.code_module,
            "course_name": course.name, "code_presentation": presentation.code_presentation,
            "task_ids": set(), "dates": set(),
        })
        group["task_ids"].add(str(task.id))
        if plan.target_completion_date is not None:
            group["dates"].add(plan.target_completion_date)
    reminders = []
    for group in grouped.values():
        due = min(group["dates"]) if group["dates"] else None
        days = (due - today).days if due is not None else None
        state = "overdue" if days is not None and days < 0 else "due_soon" if days is not None and days <= 3 else "pending"
        level = {"overdue": "danger", "due_soon": "warning", "pending": "info"}[state]
        pending = len(group["task_ids"])
        message = f"Bạn còn {pending} nhiệm vụ chưa hoàn thành."
        if days is not None:
            if days < 0:
                message += f" Hạn kế hoạch gần nhất đã qua {abs(days)} ngày."
            elif days == 0:
                message += " Kế hoạch gần nhất đến hạn hôm nay."
            else:
                message += f" Còn {days} ngày đến hạn kế hoạch gần nhất."
        signature = f"{group['enrollment_id']}:{due}:{state}:{','.join(sorted(group['task_ids']))}"
        reminders.append({
            "id": hashlib.sha256(signature.encode()).hexdigest()[:24],
            "enrollment_id": group["enrollment_id"], "code_module": group["code_module"],
            "course_name": group["course_name"], "code_presentation": group["code_presentation"],
            "title": f"Nhắc nhở môn {group['code_module']}", "message": message,
            "pending_tasks": pending, "due_date": due, "days_remaining": days,
            "state": state, "level": level,
        })
    priority = {"overdue": 0, "due_soon": 1, "pending": 2}
    return sorted(reminders, key=lambda r: (priority[r["state"]], r["due_date"] or date.max, r["code_module"]))


async def get_student_course_reminders(db, student_id):
    query = (
        select(InterventionTask, InterventionPlan, StudentEnrollment, Course, CoursePresentation)
        .join(InterventionPlan, InterventionPlan.id == InterventionTask.plan_id)
        .join(PredictionRun, PredictionRun.id == InterventionPlan.prediction_run_id)
        .join(StudentFeatureSnapshot, StudentFeatureSnapshot.id == PredictionRun.snapshot_id)
        .join(StudentEnrollment, StudentEnrollment.id == StudentFeatureSnapshot.enrollment_id)
        .join(CoursePresentation, CoursePresentation.id == StudentEnrollment.presentation_id)
        .join(Course, Course.id == CoursePresentation.course_id)
        .where(InterventionPlan.student_id == student_id,
               StudentEnrollment.student_id == student_id,
               InterventionPlan.status == "ACTIVE", InterventionTask.is_completed == False)
    )
    rows = (await db.execute(query)).all()
    today = datetime.now(timezone(timedelta(hours=7))).date()
    return build_course_reminders(rows, today)
