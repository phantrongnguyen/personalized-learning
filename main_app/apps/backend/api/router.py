from fastapi import APIRouter

from api.v1.endpoints import health, predictions, historical_cases, actionable_recourse

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"],
)

api_router.include_router(
    historical_cases.router,
    prefix="/historical-cases",
    tags=["Historical cases"],
)

api_router.include_router(
    actionable_recourse.router,
    prefix="/actionable-recourse",
    tags=["Actionable Recourse"],
)
