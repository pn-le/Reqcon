"""End-to-end CLI tests with a stub adapter (M1 acceptance: fake board produces
correct md/json; double-run shows no changes)."""

import json

import pytest

import reqcon.adapters as adapters
from reqcon.adapters.base import AdapterError
from reqcon.cli import main
from reqcon.models import Posting


class StubAdapter:
    def __init__(self):
        self.postings = [
            Posting(board_id="fake", posting_id="1", title="Software Intern", url="https://x/1"),
            Posting(board_id="fake", posting_id="2", title="Staff Engineer", url="https://x/2"),
        ]
        self.error = None

    def fetch(self, board, *, client=None):
        if self.error:
            raise AdapterError(self.error)
        return [Posting.from_dict(p.to_dict()) for p in self.postings]


@pytest.fixture
def env(tmp_path, monkeypatch):
    stub = StubAdapter()
    monkeypatch.setitem(adapters._REGISTRY, "greenhouse", stub)
    config = tmp_path / "boards.yaml"
    config.write_text(
        f"""
defaults:
  output_dir: {tmp_path / "out"}
  state_dir: {tmp_path / "data"}
  keywords_tag: [intern]
boards:
  - id: fake
    name: Fake Board
    adapter: greenhouse
    board_token: fake
"""
    )
    return stub, config, tmp_path / "out"


def scan(config):
    return main(["--config", str(config), "scan"])


def test_first_scan_baselines_then_no_changes(env, capsys):
    stub, config, out = env
    assert scan(config) == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "baseline"
    assert data["summary"]["added"] == 0

    assert scan(config) == 0  # double run: zero changes
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "ok"
    assert data["summary"] == {"added": 0, "removed": 0, "changed": 0, "boards_ok": 1, "boards_error": 0}
    md = next(out.glob("reqcon-*.md")).read_text()
    assert "No changes across 1 boards." in md


def test_added_posting_reported_and_tagged(env):
    stub, config, out = env
    scan(config)
    stub.postings.append(
        Posting(board_id="fake", posting_id="3", title="ML Intern", url="https://x/3")
    )
    assert scan(config) == 0
    data = json.loads((out / "changes-latest.json").read_text())
    (added,) = data["boards"][0]["added"]
    assert added["posting_id"] == "3"
    assert added["tags"] == ["student-role"]


def test_adapter_error_exits_1_and_preserves_state(env):
    stub, config, out = env
    scan(config)
    stub.error = "timeout"
    assert scan(config) == 1
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0] == {"board_id": "fake", "status": "error", "error": "timeout"}

    stub.error = None  # recovery: previous snapshot intact, so no phantom adds
    assert scan(config) == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["summary"]["added"] == 0


def test_config_error_exits_2(tmp_path):
    bad = tmp_path / "boards.yaml"
    bad.write_text("boards:\n  - id: x\n    name: X\n    adapter: nope\n")
    assert main(["--config", str(bad), "scan"]) == 2


def test_unknown_board_id_exits_2(env):
    stub, config, out = env
    assert main(["--config", str(config), "scan", "--board", "nope"]) == 2
