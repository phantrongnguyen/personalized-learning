import joblib
from pathlib import Path

# Đảm bảo tính tương thích unpickle khi scikit-learn >= 1.8 nạp pipeline lưu từ 1.6
try:
    import sklearn.compose._column_transformer as ct
    if not hasattr(ct, "_RemainderColsList"):
        class _RemainderColsList(list):
            pass
        ct._RemainderColsList = _RemainderColsList
except Exception:
    pass


def load_model(model_path: Path):
    if not model_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model tại: {model_path}"
        )

    model = joblib.load(model_path)
    return model