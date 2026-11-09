"""Verify a saved prediction without reading current profile or course features."""
import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.database import AsyncSessionLocal, engine
from models.ml import PredictionRun
from services.replay_service import replay_prediction


async def main(prediction_id):
    try:
        async with AsyncSessionLocal() as db:
            run = await db.get(PredictionRun, prediction_id)
            if run is None:
                raise ValueError("Prediction not found")
            result = replay_prediction(run)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if not result["matches_original"]:
                raise ValueError("Replay differs from original prediction")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction-id", type=uuid.UUID, required=True)
    asyncio.run(main(parser.parse_args().prediction_id))
