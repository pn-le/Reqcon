"""Snapshot state: load/save with atomic writes, daily history with pruning."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

STATE_FILENAME = "state.json"
HISTORY_KEEP = 7


def state_path(state_dir: Path) -> Path:
    return state_dir / STATE_FILENAME


def load_state(state_dir: Path) -> dict:
    path = state_path(state_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_state(state_dir: Path, state: dict) -> None:
    _atomic_write(state_path(state_dir), json.dumps(state, indent=2))


def save_history(state_dir: Path, state: dict, run_date: str) -> None:
    """Keep a per-day snapshot copy in history/, pruning to the last HISTORY_KEEP."""
    history_dir = state_dir / "history"
    _atomic_write(history_dir / f"state-{run_date}.json", json.dumps(state, indent=2))
    snapshots = sorted(history_dir.glob("state-*.json"))
    for old in snapshots[:-HISTORY_KEEP]:
        old.unlink()
