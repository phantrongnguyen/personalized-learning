import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1] / "apps" / "backend"
sys.path.insert(0, str(BACKEND))

from ml.model_loader import load_model
from ml.predictor import feature_contributions

KEY = ["id_student", "code_module", "code_presentation"]
FRACTIONS = (0.75, 0.85, 1.0)
SOURCE_FILES = ("studentInfo", "studentRegistration", "courses", "vle", "studentVle", "assessments", "studentAssessment")


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_library(data_dir, output, model_path):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    model = load_model(model_path)
    metadata = json.loads((BACKEND / "artifacts" / "THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json").read_text(encoding="utf-8"))
    if metadata["cutoff_fraction"] != 0.75 or file_digest(model_path) != metadata["model_sha256"]:
        raise ValueError("Model không khớp artifact đã kiểm chứng tại cutoff 75%.")
    for name in SOURCE_FILES:
        if not (data_dir / f"{name}.csv").exists():
            raise FileNotFoundError(f"Thiếu {name}.csv trong thư mục dữ liệu nguồn")
    info = pd.read_csv(data_dir / "studentInfo.csv")
    registration = pd.read_csv(data_dir / "studentRegistration.csv")
    courses = pd.read_csv(data_dir / "courses.csv")
    base = info.merge(registration, on=KEY, validate="one_to_one").merge(courses, on=KEY[1:], validate="many_to_one")
    base["cutoff_day"] = np.floor(base.module_presentation_length * 0.75).astype(int)
    base = base.loc[(base.date_registration.isna() | (base.date_registration <= base.cutoff_day)) & (base.date_unregistration.isna() | (base.date_unregistration > base.cutoff_day))].copy()
    expected_rows = metadata["training_rows"] + metadata["test_rows_excluded"]
    if len(base) != expected_rows:
        raise ValueError(f"Số enrollment {len(base)} khác nguồn model {expected_rows}.")
    ids = np.random.default_rng(41).permutation(np.sort(info.id_student.unique()))
    held_out_ids = set(ids[round(len(ids) * 0.85):])
    base = base.loc[base.id_student.isin(held_out_ids)].reset_index(drop=True)
    if len(base) != metadata["test_rows_excluded"]:
        raise ValueError("Phân tập tham chiếu không khớp nhóm test độc lập của model.")
    if base["date_registration"].isna().any():
        raise ValueError("Hồ sơ tham chiếu thiếu date_registration; không tự điền giá trị.")
    sites = pd.read_csv(data_dir / "vle.csv", usecols=["id_site", "activity_type"])
    site_types = sites.set_index("id_site").activity_type.to_dict()
    daily_parts = []
    print(f"Tạo thư viện từ {len(base)} enrollment test độc lập; đọc nhật ký theo lô...", flush=True)
    for chunk in pd.read_csv(data_dir / "studentVle.csv", chunksize=300_000):
        chunk = chunk.loc[chunk.id_student.isin(held_out_ids)].copy()
        if chunk.empty:
            continue
        activity_type = chunk.id_site.map(site_types)
        chunk["resource"] = chunk.sum_click.where(activity_type == "resource", 0)
        chunk["url"] = chunk.sum_click.where(activity_type == "url", 0)
        daily_parts.append(chunk.groupby(KEY + ["date"], as_index=False)[["sum_click", "resource", "url"]].sum())
    daily = pd.concat(daily_parts, ignore_index=True).groupby(KEY + ["date"], as_index=False).sum(numeric_only=True)
    del daily_parts
    daily = daily.merge(base[KEY + ["module_presentation_length"]], on=KEY, validate="many_to_one")
    assessments = pd.read_csv(data_dir / "assessments.csv")
    submissions = pd.read_csv(data_dir / "studentAssessment.csv")
    submissions = submissions.loc[submissions.id_student.isin(held_out_ids)]
    submissions = submissions.merge(assessments, on="id_assessment", validate="many_to_one").merge(base[KEY + ["module_presentation_length"]], on=KEY, validate="many_to_one")
    course_assessments = assessments.merge(courses, on=KEY[1:], validate="many_to_one")
    snapshots = {}
    baseline_features = None
    for fraction in FRACTIONS:
        frame = base.copy()
        frame["day"] = np.floor(frame.module_presentation_length * fraction).astype(int)
        events = daily.loc[daily.date <= np.floor(daily.module_presentation_length * fraction)].copy()
        events["recent"] = events.date.ge(0) & events.date.gt(np.floor(events.module_presentation_length * fraction) - 30)
        events["recent_clicks"] = events.sum_click.where(events.recent, 0)
        aggregate = events.groupby(KEY).agg(total_clicks_to_t=("sum_click", "sum"), clicks_resource_to_t=("resource", "sum"), clicks_url_to_t=("url", "sum"), active_days_to_t=("date", "nunique"), last_activity=("date", "max"), recent_clicks=("recent_clicks", "sum")).reset_index()
        recent_days = events.loc[events.recent].groupby(KEY).date.nunique().rename("recent_active_days").reset_index()
        frame = frame.merge(aggregate, on=KEY, how="left", validate="one_to_one").merge(recent_days, on=KEY, how="left", validate="one_to_one")
        submitted = submissions.loc[submissions.date_submitted <= np.floor(submissions.module_presentation_length * fraction)].copy()
        submitted["late"] = submitted.date_submitted.gt(submitted.date).astype(int)
        submitted_aggregate = submitted.groupby(KEY).agg(assessments_submitted_to_t=("id_assessment", "nunique"), late_submissions_to_t=("late", "sum")).reset_index()
        due = course_assessments.loc[course_assessments.date <= np.floor(course_assessments.module_presentation_length * fraction)]
        due_counts = due.groupby(KEY[1:]).id_assessment.nunique().rename("due_assessments").reset_index()
        due_submitted = submitted.loc[submitted.date <= np.floor(submitted.module_presentation_length * fraction)].groupby(KEY).id_assessment.nunique().rename("due_assessments_submitted").reset_index()
        frame = frame.merge(submitted_aggregate, on=KEY, how="left", validate="one_to_one").merge(due_counts, on=KEY[1:], how="left", validate="many_to_one").merge(due_submitted, on=KEY, how="left", validate="one_to_one")
        if not frame[KEY].equals(base[KEY]):
            raise ValueError("Thứ tự hồ sơ thay đổi trong lúc tạo đặc trưng.")
        count_columns = ["total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t", "active_days_to_t", "recent_clicks", "recent_active_days", "assessments_submitted_to_t", "late_submissions_to_t", "due_assessments", "due_assessments_submitted"]
        frame[count_columns] = frame[count_columns].fillna(0)
        frame["due_submission_rate"] = frame.due_assessments_submitted.div(frame.due_assessments.where(frame.due_assessments > 0))
        snapshots[fraction] = frame
        if fraction == 0.75:
            frame["active_day_ratio"] = frame.active_days_to_t / frame.day.clip(lower=1)
            frame["submission_rate"] = frame.assessments_submitted_to_t / frame.due_assessments.clip(lower=1)
            frame["days_since_last_activity"] = (frame.day - frame.last_activity).clip(lower=0).fillna(frame.day + 1)
            for window in (7, 30):
                recent = events.loc[events.date.ge(0) & (events.date > np.floor(events.module_presentation_length * fraction) - window)]
                name = f"clicks_recent_{window}"
                counts = recent.groupby(KEY).sum_click.sum().rename(name).reset_index()
                frame = frame.merge(counts, on=KEY, how="left", validate="one_to_one")
                frame[name] = frame[name].fillna(0)
            if not frame[KEY].equals(base[KEY]):
                raise ValueError("Thứ tự hồ sơ thay đổi trong cửa sổ VLE.")
            baseline_features = frame[model["feature_columns"]]
    probabilities = model["pipeline"].predict_proba(baseline_features)[:, list(model["pipeline"].classes_).index(1)]
    baselines, contributions = feature_contributions(model, baseline_features)
    reconstructed = 1 / (1 + np.exp(-(baselines + contributions.sum(axis=1))))
    if not np.allclose(probabilities, reconstructed, atol=1e-8, rtol=0):
        raise ValueError("SHAP của thư viện không tái dựng đúng xác suất.")
    records = []
    for index, row in base.iterrows():
        key_text = "|".join(str(row[column]) for column in KEY)
        record = {"case_id": "OULAD-" + hashlib.sha256(key_text.encode()).hexdigest()[:12], "learner_key": hashlib.sha256(str(row.id_student).encode()).hexdigest(), "module": row.code_module, "presentation": row.code_presentation, "final_result": row.final_result, "risk_probability": float(probabilities[index]), "features": baseline_features.iloc[index].to_dict(), "contributions": dict(zip(model["feature_columns"], contributions[index].tolist())), "snapshots": []}
        for fraction in FRACTIONS:
            snapshot = snapshots[fraction].iloc[index]
            record["snapshots"].append({"fraction": fraction, "day": int(snapshot.day), "recent_active_days": int(snapshot.recent_active_days), "recent_clicks": int(snapshot.recent_clicks), "due_assessments": int(snapshot.due_assessments), "due_assessments_submitted": int(snapshot.due_assessments_submitted), "due_submission_rate": None if pd.isna(snapshot.due_submission_rate) else float(snapshot.due_submission_rate)})
        records.append(record)
    numeric_columns = baseline_features.select_dtypes("number").columns
    scales = {}
    for column in numeric_columns:
        values = baseline_features[column]
        if column not in ("submission_rate", "active_day_ratio", "date_registration"):
            values = np.log1p(values.clip(lower=0))
        scales[column] = max(float(values.quantile(0.95) - values.quantile(0.05)), 1e-6)
    manifest = {"schema_version": 1, "source": "OULAD · nhóm test độc lập theo id_student, seed 41", "cutoff_fraction": 0.75, "threshold": float(model["threshold"]), "model_sha256": file_digest(model_path), "matching_method": "same module + risk classification + weighted normalized behavioral distance + positive SHAP profile", "source_sha256": {name + ".csv": file_digest(data_dir / (name + ".csv")) for name in SOURCE_FILES}, "numeric_scales": scales, "records": records}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(".tmp")
    with gzip.open(temporary_output, "wt", encoding="utf-8") as destination:
        json.dump(manifest, destination, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    temporary_output.replace(output)
    recoveries = sum(record["risk_probability"] >= manifest["threshold"] and record["final_result"] in ("Pass", "Distinction") for record in records)
    print(f"Đã tạo {output.name}: {len(records)} hồ sơ, {recoveries} từng bị model xếp nguy cơ nhưng vượt qua cuối kỳ.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo thư viện lịch sử cục bộ từ 7 CSV OULAD, không huấn luyện lại model.")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=BACKEND / "artifacts" / "historical_cases.json.gz")
    args = parser.parse_args()
    build_library(args.data_dir.resolve(), args.output.resolve(), BACKEND / "artifacts" / "model_hco_vnls_lightgbm_cutoff75.joblib")
