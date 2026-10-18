from fastapi import APIRouter, Depends, HTTPException, Request

from core.permissions import get_current_user
from models.user import User

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
def create_prediction(
    data: PredictionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    model = getattr(request.app.state, "model", None)

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model chưa sẵn sàng",
        )

    try:
        return PredictionService.execute(model, data)

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Dữ liệu đầu vào không hợp lệ: {exc}",
        ) from exc
