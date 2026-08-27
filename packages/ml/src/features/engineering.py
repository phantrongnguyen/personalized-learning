"""
Module: Feature Engineering for OULAD Dataset
Author: KLTN 13 - HUIT
"""

import os
import numpy as np
import pandas as pd


def extract_oulad_features(data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Extracts and merges demographic, assessment, and VLE interaction features
    from the raw OULAD CSV files.
    """
    # 1. Student demographic & registration info
    df_info = pd.read_csv(os.path.join(data_dir, "studentInfo.csv"))
    df_reg = pd.read_csv(os.path.join(data_dir, "studentRegistration.csv"))

    # 2. Student assessment features
    df_assess = pd.read_csv(os.path.join(data_dir, "assessments.csv"))
    df_stud_assess = pd.read_csv(os.path.join(data_dir, "studentAssessment.csv"))

    df_sa = df_stud_assess.merge(df_assess, on="id_assessment", how="left")
    df_sa["weighted_score_val"] = df_sa["score"] * df_sa["weight"]
    df_sa["is_late"] = (df_sa["date_submitted"] > df_sa["date"]).astype(int)

    stud_assess_agg = df_sa.groupby(["id_student", "code_module", "code_presentation"]).agg(
        avg_score=("score", "mean"),
        min_score=("score", "min"),
        max_score=("score", "max"),
        std_score=("score", "std"),
        total_assessments_taken=("score", "count"),
        late_submissions=("is_late", "sum"),
        sum_weighted_score=("weighted_score_val", "sum"),
        sum_weight=("weight", "sum")
    ).reset_index()

    stud_assess_agg["weighted_avg_score"] = stud_assess_agg["sum_weighted_score"] / np.maximum(
        stud_assess_agg["sum_weight"], 1e-5
    )
    stud_assess_agg["std_score"] = stud_assess_agg["std_score"].fillna(0)
    stud_assess_agg.drop(columns=["sum_weighted_score", "sum_weight"], inplace=True)

    # 3. Student VLE behavioral features
    df_vle = pd.read_csv(os.path.join(data_dir, "vle.csv"))
    df_svle = pd.read_csv(
        os.path.join(data_dir, "studentVle.csv"),
        usecols=["code_module", "code_presentation", "id_student", "id_site", "date", "sum_click"]
    )
    df_svle = df_svle.merge(df_vle[["id_site", "activity_type"]], on="id_site", how="left")

    df_svle["click_early"] = np.where(df_svle["date"] <= 30, df_svle["sum_click"], 0)
    df_svle["click_mid"] = np.where((df_svle["date"] > 30) & (df_svle["date"] <= 100), df_svle["sum_click"], 0)
    df_svle["click_late"] = np.where(df_svle["date"] > 100, df_svle["sum_click"], 0)

    vle_total_agg = df_svle.groupby(["code_module", "code_presentation", "id_student"]).agg(
        total_clicks=("sum_click", "sum"),
        active_days=("date", "nunique"),
        clicks_early=("click_early", "sum"),
        clicks_mid=("click_mid", "sum"),
        clicks_late=("click_late", "sum")
    ).reset_index()

    top_activities = ["forumng", "oucontent", "resource", "subpage", "url", "homepage", "quiz"]
    activity_piv = df_svle[df_svle["activity_type"].isin(top_activities)].pivot_table(
        index=["code_module", "code_presentation", "id_student"],
        columns="activity_type",
        values="sum_click",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    activity_piv.columns = [f"clicks_{c}" if c in top_activities else c for c in activity_piv.columns]

    # 4. Merge all sources
    df_final = df_info.merge(df_reg, on=["code_module", "code_presentation", "id_student"], how="left")
    df_final = df_final.merge(stud_assess_agg, on=["code_module", "code_presentation", "id_student"], how="left")
    df_final = df_final.merge(vle_total_agg, on=["code_module", "code_presentation", "id_student"], how="left")
    df_final = df_final.merge(activity_piv, on=["code_module", "code_presentation", "id_student"], how="left")

    return df_final
