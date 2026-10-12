import joblib
from pathlib import Path


def load_model(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model tại: {model_path}"
        )

    model = joblib.load(model_path)

    return model