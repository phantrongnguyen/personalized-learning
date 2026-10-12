from core.database import Base
from models.user import User, Role, user_roles
from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
from models.academic import Course, CoursePresentation, StudentEnrollment
from models.assignment import CourseLecturer, AdvisorStudent
from models.feature import StudentFeatureSnapshot
from models.ml import MLModel, PredictionRun
from models.intervention import InterventionPlan, InterventionTask, AdvisingNote
from models.help_request import StudentHelpRequest
from models.audit import AuditLog

__all__ = [
    "Base",
    "User",
    "Role",
    "user_roles",
    "StudentProfile",
    "AdvisorProfile",
    "LecturerProfile",
    "Course",
    "CoursePresentation",
    "StudentEnrollment",
    "CourseLecturer",
    "AdvisorStudent",
    "StudentFeatureSnapshot",
    "MLModel",
    "PredictionRun",
    "InterventionPlan",
    "InterventionTask",
    "AdvisingNote",
    "StudentHelpRequest",
    "AuditLog",
]
