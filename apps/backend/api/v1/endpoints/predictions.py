from fastapi import APIRouter, Depends, HTTPException, Request

from core.permissions import get_current_user
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from anyio import to_thread
from core.database import get_db
from services.model_registry import model_registry

from schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from services.prediction_service import PredictionService

router = APIRouter()


@router.post(
    "/",
    response_model=PredictionResponse,
    summary="Dự đoán bằng Machine Learning",
)
async def create_prediction(
    data: PredictionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _, model = await model_registry.active(db)

    try:
        return await to_thread.run_sync(PredictionService.execute, model, data)

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Dữ liệu đầu vào không hợp lệ: {exc}",
        ) from exc
