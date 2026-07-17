import json

from reqcon import state


def test_load_missing_state_returns_empty(tmp_path):
    assert state.load_state(tmp_path) == {}


def test_save_and_load_roundtrip(tmp_path):
    data = {"board": {"fetched_at": "t", "postings": []}}
    state.save_state(tmp_path, data)
    assert state.load_state(tmp_path) == data
    # no leftover temp files from the atomic write
    assert [p.name for p in tmp_path.iterdir()] == ["state.json"]


def test_save_is_atomic_replace(tmp_path):
    state.save_state(tmp_path, {"v": 1})
    state.save_state(tmp_path, {"v": 2})
    assert json.loads((tmp_path / "state.json").read_text()) == {"v": 2}


def test_history_prunes_to_last_seven(tmp_path):
    for day in range(1, 11):
        state.save_history(tmp_path, {"day": day}, f"2026-07-{day:02d}")
    kept = sorted(p.name for p in (tmp_path / "history").glob("state-*.json"))
    assert len(kept) == 7
    assert kept[0] == "state-2026-07-04.json"
    assert kept[-1] == "state-2026-07-10.json"
