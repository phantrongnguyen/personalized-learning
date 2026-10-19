from __future__ import annotations

from dataclasses import dataclass
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

@dataclass(frozen=True)
class ModelConfig:
    name: str
    estimator: object
    scale: bool = False

def configs(seed: int = 42):
    return [
        ModelConfig('LogisticRegression', LogisticRegression(max_iter=600, class_weight='balanced', random_state=seed), True),
        ModelConfig('DecisionTree', DecisionTreeClassifier(max_depth=8, min_samples_leaf=10, class_weight='balanced', random_state=seed)),
        ModelConfig('RandomForest', RandomForestClassifier(n_estimators=80, min_samples_leaf=2, class_weight='balanced', random_state=seed, n_jobs=1)),
        ModelConfig('ExtraTrees', ExtraTreesClassifier(n_estimators=80, min_samples_leaf=2, class_weight='balanced', random_state=seed, n_jobs=1)),
        ModelConfig('HistGradientBoosting', HistGradientBoostingClassifier(max_iter=160, learning_rate=0.08, max_leaf_nodes=15, early_stopping=False, random_state=seed)),
    ]

def make_pipeline(frame, config: ModelConfig):
    categorical = frame.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    numerical = [c for c in frame.columns if c not in categorical]
    numeric_steps = [('imputer', SimpleImputer(strategy='median'))]
    if config.scale: numeric_steps.append(('scale', StandardScaler()))
    transformer = ColumnTransformer([
        ('num', Pipeline(numeric_steps), numerical),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical),
    ], remainder='drop')
    return Pipeline([('preprocess', transformer), ('model', config.estimator)])

def feature_columns(frame):
    blocked = {'id_student', 'final_result', 'risk', 'cutoff', 'cutoff_mode', 'score_policy', 'module_presentation_length'}
    return [c for c in frame.columns if c not in blocked]
