import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.database import engine


@pytest.fixture(autouse=True)
async def cleanup_db_connections():
    yield
    await engine.dispose()
