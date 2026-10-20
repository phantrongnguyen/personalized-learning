from __future__ import annotations

from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

KEY = ["id_student", "code_module", "code_presentation"]
RISK_MAP = {"Pass": 0, "Distinction": 0, "Fail": 1, "Withdrawn": 1}


def source_manifest(data_dir: str | Path) -> dict:
    data_dir = Path(data_dir)
    names = ["studentInfo.csv", "studentRegistration.csv", "assessments.csv", "studentAssessment.csv", "studentVle.csv", "vle.csv", "courses.csv"]
    result = {}
    for name in names:
        path = data_dir / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = pd.read_csv(path, nrows=5)
        result[name] = {"sha256": digest, "columns": frame.columns.tolist(), "bytes": path.stat().st_size}
    return result


def merge_full_tables(data_dir: str | Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    info = pd.read_csv(data_dir / "studentInfo.csv")
    registration = pd.read_csv(data_dir / "studentRegistration.csv")
    assessments = pd.read_csv(data_dir / "assessments.csv")
    submissions = pd.read_csv(data_dir / "studentAssessment.csv")
    vle = pd.read_csv(data_dir / "vle.csv", usecols=["id_site", "activity_type"])
    courses = pd.read_csv(data_dir / "courses.csv")
    sa = submissions.merge(assessments, on="id_assessment", how="left", validate="many_to_one")
    sa["weighted_score"] = sa["score"] * sa["weight"]
    sa["is_late"] = (sa["date_submitted"] > sa["date"]).astype(int)
    assess = sa.groupby(KEY).agg(avg_score=("score", "mean"), min_score=("score", "min"), max_score=("score", "max"), std_score=("score", "std"), total_assessments_taken=("score", "count"), late_submissions=("is_late", "sum"), weighted_score_sum=("weighted_score", "sum"), weight_sum=("weight", "sum")).reset_index()
    assess["weighted_avg_score"] = assess["weighted_score_sum"] / assess["weight_sum"].clip(lower=1e-5)
    assess["std_score"] = assess["std_score"].fillna(0)
    assess = assess.drop(columns=["weighted_score_sum", "weight_sum"])
    parts = []
    day_parts = []
    last_parts = []
    usecols = ["code_module", "code_presentation", "id_student", "id_site", "date", "sum_click"]
    site_type = dict(zip(vle.id_site, vle.activity_type))
    for chunk in pd.read_csv(data_dir / "studentVle.csv", usecols=usecols, chunksize=500000):
        chunk["activity_type"] = chunk.id_site.map(site_type).fillna("other")
        total = chunk.groupby(KEY).agg(total_clicks=("sum_click", "sum"), clicks_early=("sum_click", lambda x: int(x.loc[chunk.loc[x.index, "date"] <= 30].sum())), clicks_mid=("sum_click", lambda x: int(x.loc[(chunk.loc[x.index, "date"] > 30) & (chunk.loc[x.index, "date"] <= 100)].sum())), clicks_late=("sum_click", lambda x: int(x.loc[chunk.loc[x.index, "date"] > 100].sum()))).reset_index()
        day_parts.append(chunk[KEY + ["date"]].drop_duplicates())
        last_parts.append(chunk.groupby(KEY, as_index=False)["date"].max().rename(columns={"date": "last_activity_day"}))
        piv = chunk[chunk.activity_type.isin(["forumng", "oucontent", "resource", "subpage", "url", "homepage", "quiz"])].pivot_table(index=KEY, columns="activity_type", values="sum_click", aggfunc="sum", fill_value=0).reset_index()
        piv.columns = ["clicks_" + c if c in ["forumng", "oucontent", "resource", "subpage", "url", "homepage", "quiz"] else c for c in piv.columns]
        parts.append(total.merge(piv, on=KEY, how="outer"))
    activity = pd.concat(parts, ignore_index=True).groupby(KEY, as_index=False).sum(numeric_only=True)
    unique_days = pd.concat(day_parts, ignore_index=True).drop_duplicates(KEY + ["date"])
    active_days = unique_days.groupby(KEY, as_index=False)["date"].nunique().rename(columns={"date": "active_days"})
    last_activity = pd.concat(last_parts, ignore_index=True).groupby(KEY, as_index=False)["last_activity_day"].max()
    activity = activity.merge(active_days, on=KEY, how="outer").merge(last_activity, on=KEY, how="outer")
    result = info.merge(registration, on=KEY, how="left", validate="one_to_one").merge(assess, on=KEY, how="left", validate="one_to_one").merge(activity, on=KEY, how="left", validate="one_to_one").merge(courses, on=["code_module", "code_presentation"], how="left", validate="many_to_one")
    count_columns = [c for c in result.columns if c.startswith("clicks_") or c in ["total_clicks", "active_days", "total_assessments_taken", "late_submissions"]]
    result[count_columns] = result[count_columns].fillna(0)
    result["risk"] = result.final_result.map(RISK_MAP).astype("Int64")
    return result


def create_asof(data_dir: str | Path, cutoff: float, cutoff_mode: str = "fraction", score_policy: str = "strict") -> pd.DataFrame:
    data_dir = Path(data_dir)
    info = pd.read_csv(data_dir / "studentInfo.csv")
    reg = pd.read_csv(data_dir / "studentRegistration.csv")
    courses = pd.read_csv(data_dir / "courses.csv")
    if cutoff_mode == "fraction":
        if not 0 <= cutoff <= 1: raise ValueError("fraction must be between 0 and 1")
        courses["cutoff_day"] = np.floor(cutoff * courses.module_presentation_length).astype(int)
    elif cutoff_mode == "day":
        if cutoff < 0: raise ValueError("day must be non-negative")
        courses["cutoff_day"] = int(cutoff)
        courses["cutoff_day"] = courses[["cutoff_day", "module_presentation_length"]].min(axis=1)
    else: raise ValueError("cutoff_mode must be fraction or day")
    courses["progress_fraction"] = courses.cutoff_day / courses.module_presentation_length
    frame = info.merge(reg, on=KEY, how="left", validate="one_to_one").merge(courses, on=["code_module", "code_presentation"], how="left", validate="many_to_one")
    frame = frame.loc[(frame.date_registration.isna() | (frame.date_registration <= frame.cutoff_day)) & (frame.date_unregistration.isna() | (frame.date_unregistration > frame.cutoff_day))].copy()
    site_type = dict(zip(pd.read_csv(data_dir / "vle.csv", usecols=["id_site", "activity_type"]).id_site, pd.read_csv(data_dir / "vle.csv", usecols=["id_site", "activity_type"]).activity_type))
    parts = []
    day_parts = []
    last_parts = []
    for chunk in pd.read_csv(data_dir / "studentVle.csv", chunksize=500000):
        chunk = chunk.merge(courses[["code_module", "code_presentation", "cutoff_day"]], on=["code_module", "code_presentation"], how="inner", validate="many_to_one")
        chunk = chunk.loc[chunk.date <= chunk.cutoff_day].copy()
        if chunk.empty: continue
        chunk["activity_type"] = chunk.id_site.map(site_type).fillna("other")
        values = chunk.groupby(KEY).agg(total_clicks_to_t=("sum_click", "sum")).reset_index()
        day_parts.append(chunk[KEY + ["date"]].drop_duplicates())
        last_parts.append(chunk.groupby(KEY, as_index=False)["date"].max().rename(columns={"date": "last_activity_day"}))
        piv = chunk[chunk.activity_type.isin(["forumng", "oucontent", "resource", "subpage", "url", "homepage", "quiz"])].pivot_table(index=KEY, columns="activity_type", values="sum_click", aggfunc="sum", fill_value=0).reset_index()
        piv.columns = ["clicks_" + c + "_to_t" if c in ["forumng", "oucontent", "resource", "subpage", "url", "homepage", "quiz"] else c for c in piv.columns]
        parts.append(values.merge(piv, on=KEY, how="outer"))
    if parts:
        activity = pd.concat(parts, ignore_index=True).groupby(KEY, as_index=False).sum(numeric_only=True)
        unique_days = pd.concat(day_parts, ignore_index=True).drop_duplicates(KEY + ["date"])
        active_days = unique_days.groupby(KEY, as_index=False)["date"].nunique().rename(columns={"date": "active_days_to_t"})
        last_activity = pd.concat(last_parts, ignore_index=True).groupby(KEY, as_index=False)["last_activity_day"].max()
        activity = activity.merge(active_days, on=KEY, how="outer").merge(last_activity, on=KEY, how="outer")
    else:
        activity = pd.DataFrame(columns=KEY + ["total_clicks_to_t", "active_days_to_t", "last_activity_day"])
    frame = frame.merge(activity, on=KEY, how="left", validate="one_to_one")
    assessment = pd.read_csv(data_dir / "studentAssessment.csv").merge(pd.read_csv(data_dir / "assessments.csv"), on="id_assessment", how="left", validate="many_to_one").merge(courses[["code_module", "code_presentation", "cutoff_day"]], on=["code_module", "code_presentation"], how="left", validate="many_to_one")
    assessment = assessment.loc[assessment.date_submitted <= assessment.cutoff_day].copy()
    assessment["is_late_to_t"] = (assessment.date_submitted > assessment.date).astype(int)
    assessed = assessment.groupby(KEY).agg(assessments_submitted_to_t=("id_assessment", "nunique"), late_submissions_to_t=("is_late_to_t", "sum")).reset_index()
    due = pd.read_csv(data_dir / "assessments.csv").merge(courses[["code_module", "code_presentation", "cutoff_day"]], on=["code_module", "code_presentation"], how="left", validate="many_to_one").query("date <= cutoff_day").groupby(["code_module", "code_presentation"], as_index=False).agg(assessments_due_to_t=("id_assessment", "nunique"))
    frame = frame.merge(assessed, on=KEY, how="left", validate="one_to_one").merge(due, on=["code_module", "code_presentation"], how="left", validate="many_to_one")
    for col in [c for c in frame.columns if c.endswith("_to_t") or c.startswith("clicks_")]: frame[col] = frame[col].fillna(0)
    frame["missing_submissions_to_t"] = (frame.assessments_due_to_t.fillna(0) - frame.assessments_submitted_to_t.fillna(0)).clip(lower=0)
    frame["risk"] = frame.final_result.map(RISK_MAP).astype("Int64")
    frame["cutoff"] = cutoff; frame["cutoff_mode"] = cutoff_mode; frame["score_policy"] = score_policy
    frame = frame.drop(columns=["date_unregistration"], errors="ignore")
    if frame[KEY].duplicated().any(): raise AssertionError("duplicate enrollment in as-of data")
    return frame.reset_index(drop=True)
