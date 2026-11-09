import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Tìm thư mục gốc của project (nơi chứa .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent.parent


class Settings(BaseSettings):
    app_name: str = "Personalized Learning Recommendation API"
    app_version: str = "0.1.0"
    model_path: Path = BASE_DIR / "artifacts" / "model_hco_vnls_lightgbm_cutoff75.joblib"
    avatar_upload_dir: Path = BASE_DIR / "uploads" / "avatars"

    @field_validator("avatar_upload_dir", mode="after")
    @classmethod
    def _resolve_avatar_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else ROOT_DIR / value

    @field_validator("model_path", mode="after")
    @classmethod
    def _resolve_model_path(cls, value: Path) -> Path:
        # Chuẩn hóa đường dẫn tương đối theo thư mục gốc project
        # để không phụ thuộc vào thư mục làm việc hiện tại (cwd) khi chạy uvicorn.
        if not value.is_absolute():
            value = ROOT_DIR / value
        return value

    # Database Settings
    database_url: str

    # JWT Settings
    secret_key: str
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    refresh_token_expire_days: int = 7

    @property
    def async_database_url(self) -> str:
        """Đảm bảo URL kết nối luôn sử dụng async driver asyncpg"""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = str(ROOT_DIR / ".env")
        extra = "ignore"


settings = Settings()
