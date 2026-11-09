"""Apply the additive snapshot/provenance upgrade in a single transaction."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.database import engine


async def main():
    script = Path(__file__).resolve().parents[3] / "docker/postgres/init-scripts/03_prediction_integrity.sql"
    try:
        async with engine.begin() as connection:
            raw = await connection.get_raw_connection()
            await raw.driver_connection.execute(script.read_text(encoding="utf-8"))
        print("Applied prediction provenance column and immutability guards.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
