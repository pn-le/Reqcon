"""boards.yaml loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_KEYWORDS = ["intern", "internship", "co-op", "coop", "undergraduate", "co op"]

_REQUIRED_BY_ADAPTER = {
    "greenhouse": ("board_token",),
    "workday": ("tenant", "wd_host", "site"),
    "html": ("url",),
}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    output_dir: Path
    state_dir: Path
    keywords_tag: list[str]
    boards: list[dict] = field(default_factory=list)

    def enabled_boards(self) -> list[dict]:
        return [b for b in self.boards if b.get("enabled", True)]

    def board(self, board_id: str) -> dict:
        for b in self.boards:
            if b["id"] == board_id:
                return b
        raise ConfigError(f"unknown board id: {board_id}")


def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("boards"), list):
        raise ConfigError(f"{path} must contain a 'boards' list")

    defaults = raw.get("defaults") or {}
    base = path.resolve().parent

    def _resolve(value: str) -> Path:
        p = Path(value).expanduser()
        return p if p.is_absolute() else base / p

    boards = []
    seen_ids = set()
    for i, board in enumerate(raw["boards"]):
        if not isinstance(board, dict):
            raise ConfigError(f"boards[{i}] is not a mapping")
        for key in ("id", "name", "adapter"):
            if not board.get(key):
                raise ConfigError(f"boards[{i}] missing required key '{key}'")
        adapter = board["adapter"]
        if adapter not in _REQUIRED_BY_ADAPTER:
            raise ConfigError(f"board '{board['id']}': unknown adapter '{adapter}'")
        for key in _REQUIRED_BY_ADAPTER[adapter]:
            if not board.get(key):
                raise ConfigError(f"board '{board['id']}': adapter '{adapter}' requires '{key}'")
        if board["id"] in seen_ids:
            raise ConfigError(f"duplicate board id: {board['id']}")
        seen_ids.add(board["id"])
        boards.append(board)

    return Config(
        output_dir=_resolve(defaults.get("output_dir", "./reports")),
        state_dir=_resolve(defaults.get("state_dir", "./data")),
        keywords_tag=list(defaults.get("keywords_tag") or DEFAULT_KEYWORDS),
        boards=boards,
    )
