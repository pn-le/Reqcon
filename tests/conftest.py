import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def load_fixture_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def load_fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture(autouse=True)
def no_backoff_sleep(monkeypatch):
    """Keep retry backoff from slowing the suite down."""
    monkeypatch.setattr("reqcon.adapters.base.time.sleep", lambda _s: None)
