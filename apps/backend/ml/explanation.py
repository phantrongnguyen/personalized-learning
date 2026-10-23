"""Per-prediction LightGBM contributions on the raw log-odds scale."""
import math

import numpy as np
import pandas as pd


def explain_prediction(artifact: dict, features: dict, expected_probability: float) -> dict:
    pipeline = artifact["pipeline"]
    preprocess = pipeline.named_steps["preprocess"]
    estimator = pipeline.named_steps["model"]
    if list(pipeline.classes_) != [0, 1]:
        raise ValueError("Unexpected class order")

    columns = artifact["feature_columns"]
    if len(columns) != 17 or set(features) != set(columns):
        raise ValueError("Incomplete prediction inputs")
    frame = pd.DataFrame([features])[columns]
    transformed = preprocess.transform(frame)
    contributions = np.asarray(estimator.booster_.predict(transformed, pred_contrib=True))
    if contributions.shape != (1, transformed.shape[1] + 1) or not np.isfinite(contributions).all():
        raise ValueError("Invalid contribution shape or value")

    numeric = preprocess.transformers_[0][2]
    categorical = preprocess.transformers_[1][2]
    categories = preprocess.named_transformers_["cat"].named_steps["onehot"].categories_
    names = [*numeric, *(name for name, values in zip(categorical, categories) for _ in values)]
    expected_names = [*(f"num__{name}" for name in numeric),
                      *(f"cat__{name}_{value}" for name, values in zip(categorical, categories) for value in values)]
    if (len(names) != transformed.shape[1] or set(names) != set(columns)
            or list(preprocess.get_feature_names_out()) != expected_names):
        raise ValueError("Transformed columns differ from the 17 input fields")

    grouped = {name: 0.0 for name in columns}
    for name, contribution in zip(names, contributions[0, :-1]):
        grouped[name] += float(contribution)
    base_margin = float(contributions[0, -1])
    margin = base_margin + sum(grouped.values())
    probability = float(pipeline.predict_proba(frame)[0, 1])
    reconstructed = math.exp(-np.logaddexp(0, -margin))
    if not (math.isfinite(expected_probability) and
            math.isclose(probability, expected_probability, rel_tol=0, abs_tol=1e-6) and
            math.isclose(reconstructed, probability, rel_tol=0, abs_tol=1e-6)):
        raise ValueError("Contributions do not reproduce the recorded prediction")
    return {
        "method": "lightgbm_tree_contrib_log_odds",
        "base_margin": base_margin,
        "base_probability": math.exp(-np.logaddexp(0, -base_margin)),
        "contributions": grouped,
    }
