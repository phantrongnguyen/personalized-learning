from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from core.database import get_db
from services.model_registry import model_registry

router = APIRouter()


@router.get("/health")
async def health_check(db=Depends(get_db)):
    try:
        _, artifact = await model_registry.active(db)
        return {"status": "ok", "model_loaded": True, "model": artifact["_provenance"]}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "model_loaded": False})
