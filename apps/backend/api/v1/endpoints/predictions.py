from fastapi import APIRouter, HTTPException, Request

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