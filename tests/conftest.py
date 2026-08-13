from pathlib import Path

import pytest

FIXTURE_SEED = Path(__file__).resolve().parent / "fixtures" / "seed"


@pytest.fixture
def seed_dir() -> Path:
    return FIXTURE_SEED
