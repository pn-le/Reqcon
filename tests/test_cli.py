"""End-to-end CLI tests with a stub adapter (M1 acceptance: fake board produces
correct md/json; double-run shows no changes and touches nothing)."""

import json

import pytest

import reqcon.adapters as adapters
from reqcon.adapters.base import AdapterError
from reqcon.cli import main
from reqcon.models import Posting
from reqcon.readme import END_MARKER, START_MARKER


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
    (tmp_path / "README.md").write_text(
        f"# Test\n\n{START_MARKER}\n{END_MARKER}\n"
    )
    return stub, config, tmp_path / "out"


def scan(config, *extra):
    return main(["--config", str(config), "scan", *extra])


def test_first_scan_baselines_then_no_changes(env):
    stub, config, out = env
    assert scan(config) == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "baseline"
    assert data["summary"]["added"] == 0
    md = next(out.glob("reqcon-*.md")).read_text()
    assert "baseline" in md.lower()

    assert scan(config) == 0  # double run: zero changes
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "ok"
    assert data["summary"] == {
        "added": 0, "removed": 0, "changed": 0,
        "boards_ok": 1, "boards_error": 0, "boards_skipped": 0,
    }


def test_no_change_run_leaves_state_and_json_byte_identical(env):
    stub, config, out = env
    scan(config)
    scan(config)  # settle: baseline -> ok report
    state_path = config.parent / "data" / "state.json"
    before_state = state_path.read_bytes()
    before_json = (out / "changes-latest.json").read_bytes()
    assert scan(config) == 0
    assert state_path.read_bytes() == before_state
    assert (out / "changes-latest.json").read_bytes() == before_json


def test_added_posting_reported_tagged_with_first_seen(env):
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
    assert added["first_seen"] == data["run_at"][:10]
    # baseline postings kept their original first_seen
    state = json.loads((config.parent / "data" / "state.json").read_text())
    by_id = {p["posting_id"]: p for p in state["fake"]["postings"]}
    assert by_id["1"]["first_seen"] == data["run_at"][:10]  # same-day baseline here
    assert by_id["3"]["first_seen"] == data["run_at"][:10]


def test_update_readme_writes_dashboard(env):
    stub, config, out = env
    assert scan(config, "--update-readme") == 0
    text = (config.parent / "README.md").read_text()
    assert text.startswith("# Test")
    assert "**Last scan:**" in text
    assert "🎓 Fake Board | [Software Intern](https://x/1)" in text
    assert "<details>" in text


def test_update_readme_without_markers_exits_1(env):
    stub, config, out = env
    (config.parent / "README.md").write_text("# stripped\n")
    assert scan(config, "--update-readme") == 1


def test_scan_without_flag_leaves_readme_alone(env):
    stub, config, out = env
    before = (config.parent / "README.md").read_text()
    scan(config)
    assert (config.parent / "README.md").read_text() == before


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


def test_ci_mode_suppresses_error_exit(env):
    stub, config, out = env
    scan(config)
    stub.error = "timeout"
    assert scan(config, "--ci") == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "error"


def test_ci_mode_skips_enabled_ci_false(env, tmp_path):
    stub, config, out = env
    config.write_text(config.read_text() + "    enabled_ci: false\n")
    assert scan(config, "--ci") == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0] == {"board_id": "fake", "status": "skipped-ci"}
    assert data["summary"]["boards_skipped"] == 1
    # without --ci the board still runs
    assert scan(config) == 0
    data = json.loads((out / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "baseline"


def test_config_error_exits_2(tmp_path):
    bad = tmp_path / "boards.yaml"
    bad.write_text("boards:\n  - id: x\n    name: X\n    adapter: nope\n")
    assert main(["--config", str(bad), "scan"]) == 2


def test_unknown_board_id_exits_2(env):
    stub, config, out = env
    assert main(["--config", str(config), "scan", "--board", "nope"]) == 2
