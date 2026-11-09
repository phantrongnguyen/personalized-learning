from fastapi import APIRouter

from api.v1.endpoints import health, predictions, auth, admin, advisor, lecturer, student

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
)

api_router.include_router(
    student.router,
    prefix="/student",
    tags=["Student"],
)

api_router.include_router(
    advisor.router,
    prefix="/advisor",
    tags=["Advisor"],
)

api_router.include_router(
    lecturer.router,
    prefix="/lecturer",
    tags=["Lecturer"],
)

api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"],
)