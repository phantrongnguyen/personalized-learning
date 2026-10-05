from ml.predictor import predict
from schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)


class PredictionService:

    @staticmethod
    def execute(model, data: PredictionRequest) -> PredictionResponse:
        result = predict(
            model=model,
            features=data.features.model_dump(),
        )

        return PredictionResponse(**result)