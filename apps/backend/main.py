from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.config import settings
from ml.model_loader import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model một lần khi ứng dụng khởi động
    app.state.model = load_model(settings.model_path)

    yield

    # Giải phóng tham chiếu khi ứng dụng tắt
    app.state.model = None


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

from pathlib import Path

# Thêm header cho phép trình duyệt truy cập private network (PNA)
@app.middleware("http")
async def add_cors_pna_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# Cho phép frontend (khác origin/port) gọi API trong môi trường dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

app.include_router(
    api_router,
    prefix="/api/v1",
)

# Phục vụ thư mục frontend trực tiếp từ backend tại /app
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
dist_dir = frontend_dir / "dist"
serve_dir = dist_dir if dist_dir.exists() else frontend_dir
if serve_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/app", StaticFiles(directory=str(serve_dir), html=True), name="frontend")


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Personalized Learning Recommendation System API is running",
        "docs": "/docs",
        "frontend": "/app",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
