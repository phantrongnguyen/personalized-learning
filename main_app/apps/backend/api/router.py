from fastapi import APIRouter

from api.v1.endpoints import health, predictions

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