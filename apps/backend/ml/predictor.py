import pandas as pd


def predict(model: dict, features: dict) -> dict:
    """Chạy suy luận trên pipeline LightGBM đã load từ artifacts.

    Model là dict chứa pipeline, danh sách cột và ngưỡng phân loại;
    pipeline yêu cầu DataFrame có tên cột đúng như lúc huấn luyện.
    """
    pipe = model["pipeline"]
    X = pd.DataFrame([features])[model["feature_columns"]]

    proba = pipe.predict_proba(X)[0]
    confidence = float(proba[list(pipe.classes_).index(1)])
    prediction = int(confidence >= model["threshold"])

    return {"prediction": prediction, "confidence": confidence}
