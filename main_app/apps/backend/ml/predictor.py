import numpy as np
import pandas as pd
from scipy.special import expit


def feature_contributions(model: dict, data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    pipeline = model["pipeline"]
    preprocessor = pipeline[:-1]
    classifier = pipeline.steps[-1][1]
    transformed = preprocessor.transform(data)
    contributions = classifier.booster_.predict(transformed, pred_contrib=True)
    if hasattr(contributions, "toarray"):
        contributions = contributions.toarray()
    contributions = np.asarray(contributions)
    if list(classifier.classes_) != [0, 1]:
        raise ValueError("Giải thích hiện chỉ hỗ trợ mô hình nhị phân với nhãn nguy cơ là 1.")

    contributions = contributions * float(classifier.booster_.params.get("sigmoid", 1.0))
    columns = model["feature_columns"]
    feature_totals = np.zeros((len(data), len(columns)))
    transformed_names = preprocessor.get_feature_names_out()
    if len(transformed_names) != contributions.shape[1] - 1:
        raise ValueError("Số biến đóng góp không khớp với bộ tiền xử lý.")

    for encoded_index, name in enumerate(transformed_names):
        original_name = name.split("__", 1)[-1]
        owner = next(
            (column for column in sorted(columns, key=len, reverse=True)
             if original_name == column or original_name.startswith(f"{column}_")),
            None,
        )
        if owner is None:
            raise ValueError(f"Không thể ánh xạ biến đã mã hoá: {name}")
        feature_totals[:, columns.index(owner)] += contributions[:, encoded_index]

    return contributions[:, -1], feature_totals


def explain_prediction(model: dict, data: pd.DataFrame, confidence: float) -> dict:
    baselines, totals = feature_contributions(model, data)
    feature_totals = dict(zip(model["feature_columns"], totals[0]))

    baseline_raw_score = float(baselines[0])
    raw_score = baseline_raw_score + sum(feature_totals.values())
    reconstructed_probability = float(expit(raw_score))
    if not np.isclose(reconstructed_probability, confidence, atol=1e-8, rtol=0):
        raise ValueError("Giải thích không tái dựng đúng xác suất của mô hình.")

    return {
        "method": "LightGBM TreeSHAP",
        "unit": "log_odds",
        "baseline_raw_score": baseline_raw_score,
        "baseline_probability": float(expit(baseline_raw_score)),
        "raw_score": raw_score,
        "reconstructed_probability": reconstructed_probability,
        "contributions": [
            {
                "feature": column,
                "value": data.iloc[0][column].item()
                if isinstance(data.iloc[0][column], np.generic)
                else data.iloc[0][column],
                "contribution": contribution,
                "direction": "increase" if contribution > 1e-10
                else "decrease" if contribution < -1e-10 else "neutral",
            }
            for column, contribution in sorted(
                feature_totals.items(), key=lambda item: abs(item[1]), reverse=True
            )
        ],
    }


def predict(model: dict, features: dict) -> dict:
    """Chạy suy luận trên pipeline LightGBM đã load từ artifacts.

    Model là dict chứa pipeline, danh sách cột và ngưỡng phân loại;
    pipeline yêu cầu DataFrame có tên cột đúng như lúc huấn luyện.
    """
    pipe = model["pipeline"]
    data = pd.DataFrame([features])[model["feature_columns"]]

    proba = pipe.predict_proba(data)[0]
    confidence = float(proba[list(pipe.classes_).index(1)])
    prediction = int(confidence >= model["threshold"])

    return {
        "prediction": prediction,
        "confidence": confidence,
        "threshold": float(model["threshold"]),
        "explanation": explain_prediction(model, data, confidence),
    }
