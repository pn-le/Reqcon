"""Live integration test (PRD §10). Skipped by default; run with: pytest -m network"""

import json

import pytest

from reqcon.cli import main


@pytest.mark.network
def test_scan_single_board_live(tmp_path):
    config = tmp_path / "boards.yaml"
    config.write_text(
        f"""
defaults:
  output_dir: {tmp_path / "out"}
  state_dir: {tmp_path / "data"}
boards:
  - id: lila-sciences
    name: Lila Sciences
    adapter: greenhouse
    board_token: lilasciences
"""
    )
    assert main(["--config", str(config), "scan", "--board", "lila-sciences"]) == 0
    data = json.loads((tmp_path / "out" / "changes-latest.json").read_text())
    assert data["boards"][0]["status"] == "baseline"
    assert len(data["boards"][0]["baseline"]) > 0
