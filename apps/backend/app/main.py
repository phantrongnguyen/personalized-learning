"""
FastAPI Server Entrypoint
Hệ thống Gợi ý Chiến lược Học tập Cá nhân hóa (KLTN 13)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="KLTN 13 - Personalized Learning Recommendation API",
    description="API dịch vụ gợi ý chiến lược học tập cá nhân hóa sử dụng thuật toán HCO-VNLS",
    version="1.0.0",
)

# Cấu hình CORS cho phép Frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to KLTN 13 Personalized Learning Recommendation API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/api/v1/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy", "service": "backend-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
