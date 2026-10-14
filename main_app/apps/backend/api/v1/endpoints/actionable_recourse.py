from fastapi import APIRouter, HTTPException, Request

from schemas.prediction import PredictionRequest
from schemas.recourse import ActionableRecourseResponse
from services.actionable_recourse_service import ActionableRecourseService

router = APIRouter()


@router.post(
    "/",
    response_model=ActionableRecourseResponse,
    summary="Tính toán mục tiêu can thiệp khả thi (Actionable Recourse) và kế hoạch SRL",
)
def compute_actionable_recourse(
    data: PredictionRequest,
    request: Request,
):
    model = getattr(request.app.state, "model", None)

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model chưa sẵn sàng trên máy chủ",
        )

    try:
        return ActionableRecourseService.generate_recourse(
            model=model,
            features=data.features.model_dump(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Lỗi khi tính toán mục tiêu can thiệp: {exc}",
        ) from exc
