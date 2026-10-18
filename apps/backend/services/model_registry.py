"""Database-authoritative model selection with checksum-addressed worker caches."""
import hashlib
import json
import math
from collections import OrderedDict
from pathlib import Path

from anyio import to_thread
from fastapi import HTTPException
from sqlalchemy import select, text, update

from ml.model_loader import load_model
from ml.predictor import predict
from models.ml import MLModel
from schemas.prediction import PredictionResponse, StudentFeatures

BACKEND = Path(__file__).resolve().parents[1]
FEATURE_COLUMNS = [
    "code_module", "gender", "highest_education", "age_band", "studied_credits",
    "date_registration", "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
    "active_days_to_t", "assessments_submitted_to_t", "late_submissions_to_t",
    "active_day_ratio", "submission_rate", "days_since_last_activity",
    "clicks_recent_7", "clicks_recent_30",
]
REGISTRY_LOCK = 1810202603
RUNTIME_KEY = "validated_runtime"


def artifact_path(record):
    candidate = Path(record.model_file_path)
    if candidate.is_absolute():
        return candidate
    for base in (BACKEND, BACKEND.parents[1]):
        resolved = base / candidate
        if resolved.is_file():
            return resolved
    raise ValueError("Không tìm thấy artifact của mô hình")


def _same_number(left, right):
    try:
        return math.isfinite(float(left)) and math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def _check_declarations(record, artifact, declarations):
    """Check every declared field; sparse legacy registry metadata is allowed."""
    if not isinstance(declarations, dict):
        raise ValueError("Metadata phải là object")
    for key, expected in (("threshold", record.threshold), ("cutoff_fraction", record.cutoff_fraction)):
        if key in declarations and not _same_number(declarations[key], expected):
            raise ValueError(f"{key} khác hợp đồng mô hình")
    if "feature_columns" in declarations and declarations["feature_columns"] != FEATURE_COLUMNS:
        raise ValueError("Danh sách/thứ tự 17 đặc trưng không khớp")
    if "features_count" in declarations and declarations["features_count"] != 17:
        raise ValueError("Số đặc trưng không khớp")
    if "positive_label" in declarations and declarations["positive_label"] != 1:
        raise ValueError("positive_label phải là 1")
    if "version" in declarations and declarations["version"] != record.version:
        raise ValueError("Phiên bản metadata khác registry")
    if "input_schema" in declarations and [field.get("name") for field in declarations["input_schema"]] != FEATURE_COLUMNS:
        raise ValueError("Schema metadata không khớp")
    if "model_sha256" in declarations and declarations["model_sha256"] != artifact["_provenance"]["model_sha256"]:
        raise ValueError("SHA-256 artifact không khớp metadata")


def validate_artifact(record, artifact, sidecar=None):
    if not record.version or not _same_number(record.cutoff_fraction, .75):
        raise ValueError("Chỉ hỗ trợ phiên bản có cutoff_fraction = 0.75")
    if not math.isfinite(record.threshold) or not 0 <= record.threshold <= 1:
        raise ValueError("Threshold phải hữu hạn trong [0, 1]")
    if artifact.get("feature_columns") != FEATURE_COLUMNS or not _same_number(artifact.get("threshold"), record.threshold):
        raise ValueError("Artifact không khớp schema hoặc threshold registry")
    if not _same_number(artifact.get("cutoff_fraction"), record.cutoff_fraction):
        raise ValueError("Cutoff artifact không khớp registry")
    embedded = artifact.get("metadata", {})
    if not {"feature_columns", "cutoff_fraction", "threshold", "positive_label"} <= embedded.keys():
        raise ValueError("Artifact thiếu metadata hợp đồng đầu vào")
    for declaration in (embedded, record.metadata_json or {}, sidecar or {}):
        _check_declarations(record, artifact, declaration)
    pipeline = artifact.get("pipeline")
    if pipeline is None or not callable(getattr(pipeline, "predict_proba", None)):
        raise ValueError("Artifact thiếu pipeline dự báo xác suất")
    if list(pipeline.classes_) != [0, 1]:
        raise ValueError("Pipeline phải có hai lớp 0 và 1")
    if list(getattr(pipeline, "feature_names_in_", FEATURE_COLUMNS)) != FEATURE_COLUMNS:
        raise ValueError("Schema pipeline khác artifact")
    probe = StudentFeatures(
        code_module="CCC", gender="M", highest_education="HE Qualification", age_band="0-35",
        studied_credits=60, date_registration=-10,
        **{key: 0 for key in FEATURE_COLUMNS[6:]},
    )
    PredictionResponse(**predict(artifact, probe.model_dump()))


class ModelRegistry:
    def __init__(self, archive_dir=None, cache_size=4):
        self.archive_dir = archive_dir or BACKEND / "artifacts/archive"
        self.cache_size = cache_size
        self._cache = OrderedDict()

    async def _lock(self, db):
        # All API activations, reloads and first-time initialization serialize
        # across processes; PostgreSQL releases this lock on commit/rollback.
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": REGISTRY_LOCK})

    async def _active_record(self, db):
        records = (await db.execute(select(MLModel).where(MLModel.is_active.is_(True))
            .execution_options(populate_existing=True))).scalars().all()
        if len(records) != 1:
            raise HTTPException(503, "Cần đúng một mô hình ML đang active")
        return records[0]

    def _runtime(self, record, artifact):
        return {
            "model_id": str(record.id), "model_version": record.version,
            "threshold": float(record.threshold), "cutoff_fraction": float(record.cutoff_fraction),
            "positive_label": 1, "feature_columns": FEATURE_COLUMNS,
            "model_sha256": artifact["_provenance"]["model_sha256"],
        }

    def _bind(self, record, artifact):
        bound = dict(artifact)
        bound["_provenance"] = {key: value for key, value in self._runtime(record, artifact).items()
                                if key != "feature_columns"}
        return bound

    def prepare_source(self, record):
        path = artifact_path(record)
        artifact = load_model(path, archive_dir=self.archive_dir)
        metadata = record.metadata_json or {}
        sidecar = None
        metadata_path = metadata.get("metadata_file_path")
        if metadata_path:
            candidate = Path(metadata_path)
            metadata_path = candidate if candidate.is_absolute() else path.parent / candidate
        elif path.with_suffix(".json").is_file():
            metadata_path = path.with_suffix(".json")
        elif path.name == "model_hco_vnls_lightgbm_cutoff75.joblib":
            metadata_path = path.parent / "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json"
        if metadata_path:
            sidecar = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        validate_artifact(record, artifact, sidecar)
        existing = metadata.get(RUNTIME_KEY)
        runtime = self._runtime(record, artifact)
        if existing is not None and existing != runtime:
            raise ValueError("Phiên bản đã xác nhận không được thay artifact/hợp đồng; hãy đăng ký phiên bản mới")
        return self._bind(record, artifact)

    async def _prepare(self, record):
        try:
            return await to_thread.run_sync(self.prepare_source, record)
        except Exception as exc:
            detail = str(exc) if isinstance(exc, ValueError) else "Không nạp/kiểm tra được artifact hoặc metadata"
            raise HTTPException(422, detail) from exc

    def _remember(self, record, artifact):
        key = json.dumps(self._runtime(record, artifact), sort_keys=True)
        self._cache[key] = artifact
        self._cache.move_to_end(key)
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return artifact

    async def initialize(self, db):
        await self._lock(db)
        record = await self._active_record(db)
        if (record.metadata_json or {}).get(RUNTIME_KEY) is None:
            artifact = await self._prepare(record)
            record.metadata_json = {**(record.metadata_json or {}), RUNTIME_KEY: self._runtime(record, artifact)}
            await db.flush()
            return record, self._remember(record, artifact)
        return record, await self._pinned(record)

    async def _pinned(self, record):
        runtime = (record.metadata_json or {})[RUNTIME_KEY]
        key = json.dumps(runtime, sort_keys=True)
        try:
            digest = runtime["model_sha256"]
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("SHA-256 registry không hợp lệ")
            artifact = self._cache.get(key)
            if artifact is None:
                path = self.archive_dir / f"{digest}.joblib"
                payload = await to_thread.run_sync(path.read_bytes)
                if hashlib.sha256(payload).hexdigest() != digest:
                    raise ValueError("Artifact lưu trữ không khớp SHA-256 registry")
                artifact = await to_thread.run_sync(lambda: load_model(path, archive_dir=self.archive_dir))
                validate_artifact(record, artifact)
            if runtime != self._runtime(record, artifact):
                raise ValueError("Danh tính/hợp đồng active khác phiên bản đã xác nhận")
            _check_declarations(record, artifact, record.metadata_json or {})
            return self._remember(record, self._bind(record, artifact))
        except Exception as exc:
            raise HTTPException(503, "Mô hình active không hợp lệ hoặc artifact lưu trữ không sẵn sàng") from exc

    async def active(self, db):
        record = await self._active_record(db)
        if (record.metadata_json or {}).get(RUNTIME_KEY) is None:
            # Supports a freshly seeded database/CLI. The caller owns commit.
            return await self.initialize(db)
        return record, await self._pinned(record)

    async def activate(self, db, model_id):
        await self._lock(db)
        record = await db.get(MLModel, model_id, populate_existing=True)
        if record is None:
            raise HTTPException(404, "Phiên bản mô hình không tồn tại")
        artifact = await self._prepare(record)
        metadata = {**(record.metadata_json or {}), RUNTIME_KEY: self._runtime(record, artifact)}
        await db.execute(update(MLModel).where(MLModel.is_active.is_(True)).values(is_active=False))
        await db.execute(update(MLModel).where(MLModel.id == model_id).values(is_active=True, metadata_json=metadata))
        await db.refresh(record)
        self._remember(record, artifact)
        return record, artifact

    async def reload(self, db):
        await self._lock(db)
        record = await self._active_record(db)
        artifact = await self._prepare(record)
        record.metadata_json = {**(record.metadata_json or {}), RUNTIME_KEY: self._runtime(record, artifact)}
        await db.flush()
        return record, self._remember(record, artifact)


model_registry = ModelRegistry()
