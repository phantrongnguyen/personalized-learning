"""
Module: Data Preprocessing Pipeline
Author: KLTN 13 - HUIT
"""

from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


class DataPipeline:
    def __init__(self, target_col: str = "final_result", binary_target: bool = True):
        self.target_col = target_col
        self.binary_target = binary_target
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []

    def prepare_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Prepares the target column if present.
        If binary_target=True: Pass/Distinction -> 1 (Success), Fail/Withdrawn -> 0 (At-Risk).
        """
        df = df.copy()
        if self.target_col not in df.columns:
            return df, None

        if self.binary_target:
            target_map = {
                "Distinction": 1,
                "Pass": 1,
                "Fail": 0,
                "Withdrawn": 0
            }
            y = df[self.target_col].map(target_map).fillna(0).astype(int)
        else:
            le = LabelEncoder()
            y = pd.Series(le.fit_transform(df[self.target_col].astype(str)), name=self.target_col)
            self.label_encoders[self.target_col] = le
        
        return df, y

    def clean_and_impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles missing values and cleans columns."""
        df = df.copy()

        # Drop ID / high cardinality key columns from direct feature set
        cols_to_drop = ["id_student", "date_unregistration", self.target_col]
        existing_drop = [c for c in cols_to_drop if c in df.columns]
        df.drop(columns=existing_drop, inplace=True)

        # Impute imd_band with 'Unknown'
        if "imd_band" in df.columns:
            df["imd_band"] = df["imd_band"].fillna("Unknown")

        # Impute registration date with median
        if "date_registration" in df.columns:
            df["date_registration"] = df["date_registration"].fillna(0)

        # Impute assessment aggregates
        assess_cols = [
            "avg_score", "min_score", "max_score", "std_score",
            "total_assessments_taken", "late_submissions", "weighted_avg_score"
        ]
        for c in assess_cols:
            if c in df.columns:
                df[c] = df[c].fillna(0)

        # Impute VLE aggregates
        vle_cols = [
            "total_clicks", "active_days", "clicks_early", "clicks_mid", "clicks_late",
            "clicks_forumng", "clicks_oucontent", "clicks_resource", "clicks_subpage",
            "clicks_url", "clicks_homepage", "clicks_quiz"
        ]
        for c in vle_cols:
            if c in df.columns:
                df[c] = df[c].fillna(0)

        return df

    def encode_and_scale(self, df: pd.DataFrame, is_train: bool = True) -> Tuple[np.ndarray, List[str]]:
        """Encodes categorical columns and standardizes numerical features."""
        df = df.copy()

        if is_train:
            self.feature_names = df.columns.tolist()
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

            for col in cat_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le

            scaled_vals = self.scaler.fit_transform(df)
            return scaled_vals, self.feature_names

        else:
            # Align columns with training feature_names
            for col in self.feature_names:
                if col not in df.columns:
                    df[col] = 0

            # Reorder columns exactly as in fit
            df = df[self.feature_names].copy()

            # Encode categories using fitted encoders
            for col, le in self.label_encoders.items():
                if col in df.columns:
                    mapping = dict(zip(le.classes_, range(len(le.classes_))))
                    df[col] = df[col].astype(str).map(mapping).fillna(-1).astype(int)

            # Ensure all values are numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            scaled_vals = self.scaler.transform(df)
            return scaled_vals, self.feature_names

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, pd.Series, List[str]]:
        """End-to-end fit and transformation of dataframe."""
        df_clean, y = self.prepare_target(df)
        df_clean = self.clean_and_impute(df_clean)
        X, feature_names = self.encode_and_scale(df_clean, is_train=True)
        return X, y, feature_names

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transforms new dataframe using fitted encoders and scaler."""
        df_clean = self.clean_and_impute(df)
        X, _ = self.encode_and_scale(df_clean, is_train=False)
        return X
