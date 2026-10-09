from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Personalized Learning Recommendation API"
    app_version: str = "0.1.0"
    model_path: Path = BASE_DIR / "artifacts" / "model_hco_vnls_lightgbm_cutoff75.joblib"


settings = Settings()
