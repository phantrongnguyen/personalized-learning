from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


GOC = Path(__file__).resolve().parents[1]
NGHIEN_CUU = GOC
DATA = GOC.parents[1] / "data" / "raw"
KET_QUA = NGHIEN_CUU / "ket_qua"
HINH = NGHIEN_CUU / "hinh"
CAC_MOC = (0.50, 0.60, 0.65, 0.70, 0.75)
KHOA = ["id_student", "code_module", "code_presentation"]
BO_QUA = {
    "id_student", "final_result", "risk", "cutoff", "cutoff_mode",
    "score_policy", "module_presentation_length", "progress_fraction",
}


def tao_thu_muc() -> None:
    for thu_muc in (KET_QUA, HINH):
        thu_muc.mkdir(parents=True, exist_ok=True)


def duong_dan(moc: float) -> Path:
    return KET_QUA / f"du_lieu_cutoff_{round(moc * 100):02d}.csv"


def chia_nhom(ids: pd.Series | np.ndarray, seed: int = 41) -> pd.DataFrame:
    unique = np.sort(np.unique(np.asarray(ids)))
    shuffled = np.random.default_rng(seed).permutation(unique)
    train_end = round(len(shuffled) * 0.70)
    valid_end = round(len(shuffled) * 0.85)
    return pd.DataFrame({
        "id_student": shuffled,
        "split": np.select(
            [np.arange(len(unique)) < train_end, np.arange(len(unique)) < valid_end],
            ["train", "validation"], default="test",
        ),
    })


def nap_du_lieu(moc: float) -> pd.DataFrame:
    frame = pd.read_csv(duong_dan(moc))
    if frame.duplicated(KHOA).any():
        raise ValueError("Trùng enrollment")
    frame["risk"] = frame["risk"].astype(int)
    return frame


def chon_dac_trung(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame if column not in BO_QUA and not column.startswith("split")]


def tien_xu_ly(frame: pd.DataFrame) -> ColumnTransformer:
    categorical = frame.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    numeric = [column for column in frame if column not in categorical]
    return ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median", add_indicator=True), numeric),
        ("categorical", Pipeline([
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical),
    ])


def bo_sung_ty_le(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    denominator = result["cutoff_day"].clip(lower=1)
    result["clicks_per_day"] = result["total_clicks_to_t"] / denominator
    result["active_day_ratio"] = result["active_days_to_t"] / denominator
    result["clicks_per_active_day"] = result["total_clicks_to_t"] / result["active_days_to_t"].clip(lower=1)
    result["submission_rate"] = result["assessments_submitted_to_t"] / result["assessments_due_to_t"].clip(lower=1)
    result["missing_rate"] = result["missing_submissions_to_t"] / result["assessments_due_to_t"].clip(lower=1)
    result["late_rate"] = result["late_submissions_to_t"] / result["assessments_submitted_to_t"].clip(lower=1)
    result["days_since_last_activity"] = (result["cutoff_day"] - result["last_activity_day"]).clip(lower=0)
    result["days_since_last_activity"] = result["days_since_last_activity"].fillna(result["cutoff_day"] + 1)
    return result


def bo_sung_cua_so_vle(frame: pd.DataFrame, chunksize: int = 500_000) -> pd.DataFrame:
    """Đếm lượt click trong 7/30 ngày cuối và hai nửa trước cutoff."""
    courses = frame[["code_module", "code_presentation", "cutoff_day"]].drop_duplicates()
    chunks = []
    for chunk in pd.read_csv(DATA / "studentVle.csv", chunksize=chunksize):
        chunk = chunk.merge(courses, on=["code_module", "code_presentation"], how="inner", validate="many_to_one")
        chunk = chunk.loc[(chunk.date >= 0) & (chunk.date <= chunk.cutoff_day)].copy()
        if chunk.empty:
            continue
        age = chunk.cutoff_day - chunk.date
        chunk["clicks_recent_7"] = chunk.sum_click.where(age < 7, 0)
        chunk["clicks_recent_30"] = chunk.sum_click.where(age < 30, 0)
        chunk["clicks_first_half"] = chunk.sum_click.where(chunk.date <= chunk.cutoff_day / 2, 0)
        chunk["clicks_second_half"] = chunk.sum_click.where(chunk.date > chunk.cutoff_day / 2, 0)
        chunks.append(chunk.groupby(KHOA, as_index=False)[
            ["clicks_recent_7", "clicks_recent_30", "clicks_first_half", "clicks_second_half"]
        ].sum())
    if not chunks:
        raise ValueError("Không có hoạt động VLE tại cutoff")
    activity = pd.concat(chunks, ignore_index=True).groupby(KHOA, as_index=False).sum()
    result = frame.merge(activity, on=KHOA, how="left", validate="one_to_one")
    columns = ["clicks_recent_7", "clicks_recent_30", "clicks_first_half", "clicks_second_half"]
    result[columns] = result[columns].fillna(0)
    result["click_trend_ratio"] = (result.clicks_second_half + 1) / (result.clicks_first_half + 1)
    return result
