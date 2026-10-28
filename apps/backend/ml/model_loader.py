import joblib
import hashlib
from io import BytesIO
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


def load_model(model_path: Path, archive_dir: Path | None = None):
    if not model_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model tại: {model_path}"
        )

    payload = model_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    model = joblib.load(BytesIO(payload))
    # Archive the exact bytes that were loaded, independent of later file edits.
    archive_dir = archive_dir or Path(__file__).resolve().parents[1] / "artifacts/archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / f"{digest}.joblib"
    try:
        with archived.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if hashlib.sha256(archived.read_bytes()).hexdigest() != digest:
            raise ValueError("Archived model checksum mismatch")
    model["_provenance"] = {
        "model_sha256": digest,
        "model_version": str(model.get("version") or model.get("model_name") or digest),
        "threshold": float(model["threshold"]),
    }
    return model
