from math import isfinite

from fastapi import APIRouter, HTTPException, Request

from schemas.historical_cases import HistoricalCasesRequest, HistoricalCasesResponse

router = APIRouter()


@router.post("/", response_model=HistoricalCasesResponse)
def compare_historical_cases(data: HistoricalCasesRequest, request: Request):
    library = getattr(request.app.state, "historical_cases", None)
    if library is None:
        return HistoricalCasesResponse(status="unavailable", message="Thư viện lịch sử chưa sẵn sàng; không hiển thị trường hợp giả lập.")
    features = data.features.model_dump()
    if any(not isfinite(value) or value < 0 for name, value in features.items() if isinstance(value, (int, float)) and name != "date_registration"):
        raise HTTPException(status_code=422, detail="Chỉ số hành vi phải là số hữu hạn và không âm.")
    if not isfinite(features["date_registration"]):
        raise HTTPException(status_code=422, detail="Ngày đăng ký phải là số hữu hạn.")
    try:
        return HistoricalCasesResponse(**library.compare(features))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"Không thể đối chiếu hồ sơ: {exc}") from exc
