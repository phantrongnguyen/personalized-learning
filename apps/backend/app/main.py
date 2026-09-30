import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.prediction import _artifact, catalog, model_info, predict
from app.schemas.prediction import PredictionInput
from app.schemas.support import SupportInput
from app.services.support import demo_cases, evaluate_case, evaluate_support

@asynccontextmanager
async def lifespan(application: FastAPI):
    _artifact()
    yield


app = FastAPI(title="CLHT · Dự báo và gợi ý có căn cứ", version="0.2.0", lifespan=lifespan)
origins = os.getenv("CLHT_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5187,http://127.0.0.1:5187")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {"message": "CLHT API", "docs": "/docs"}


@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "service": "clht-risk-demo"}


@app.get("/api/v1/catalog")
def get_catalog():
    return catalog()


@app.get("/api/v1/model")
def get_model_info():
    return model_info()


@app.post("/api/v1/predict")
def post_predict(payload: PredictionInput):
    return predict(payload)


@app.get("/api/v1/support/cases")
def get_support_cases():
    return demo_cases()


@app.post("/api/v1/support/cases/{case_id}")
def post_support_case(case_id: str):
    return evaluate_case(case_id)


@app.post("/api/v1/support")
def post_support(payload: SupportInput):
    return evaluate_support(payload)
