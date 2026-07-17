"""reqcon CLI: scan, list, init.

Exit codes: 0 success (even with zero changes), 1 any board errored, 2 config error.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import __version__, report, state
from .adapters import get_adapter
from .adapters.base import AdapterError
from .config import Config, ConfigError, load_config
from .diff import evaluate_board
from .models import BoardResult, tag_postings


def _now() -> datetime:
    return datetime.now().astimezone()


def _fetch_board(board: dict, config: Config):
    """Returns (postings, error). Exactly one is None."""
    adapter = get_adapter(board["adapter"])
    try:
        postings = adapter.fetch(board)
    except AdapterError as exc:
        return None, str(exc)
    tag_postings(postings, config.keywords_tag)
    return postings, None


def _select_boards(config: Config, board_id: str | None) -> list[dict]:
    if board_id:
        return [config.board(board_id)]
    return config.enabled_boards()


def cmd_scan(config: Config, board_id: str | None, readme_path: Path | None = None) -> int:
    run_at = _now()
    current_state = state.load_state(config.state_dir)
    results: list[BoardResult] = []

    for board in _select_boards(config, board_id):
        postings, error = _fetch_board(board, config)
        outcome = evaluate_board(
            current_state.get(board["id"]), postings, error, run_at.isoformat()
        )
        if outcome.new_snapshot is not None:
            current_state[board["id"]] = outcome.new_snapshot
        result = BoardResult(
            board_id=board["id"],
            name=board["name"],
            status=outcome.status,
            diff=outcome.diff,
            error=outcome.error,
            total_postings=len(postings) if postings is not None else None,
        )
        results.append(result)
        if result.status == "error":
            print(f"{result.board_id}: ERROR — {result.error}")
        elif result.status == "baseline":
            print(f"{result.board_id}: baseline recorded ({result.total_postings} postings)")
        else:
            d = result.diff
            print(
                f"{result.board_id}: +{len(d.added)} -{len(d.removed)} ~{len(d.changed)} "
                f"({result.total_postings} postings)"
            )

    state.save_state(config.state_dir, current_state)
    run_date = run_at.date().isoformat()
    state.save_history(config.state_dir, current_state, run_date)

    data = report.build_report_data(run_at.isoformat(), results)
    json_path = report.write_json_report(config.output_dir, data)
    md_path = report.write_markdown_report(
        config.output_dir, run_date, report.build_markdown(run_at.isoformat(), results)
    )

    if readme_path is not None:
        section = report.build_openings_section(
            config.boards, current_state, run_at.strftime("%Y-%m-%d %H:%M %Z")
        )
        if report.update_readme_openings(readme_path, section):
            print(f"readme: current openings updated in {readme_path}")

    s = data["summary"]
    print(
        f"summary: {s['added']} added, {s['removed']} removed, {s['changed']} changed | "
        f"{s['boards_ok']} boards ok, {s['boards_error']} errored"
    )
    print(f"reports: {json_path} {md_path}")
    return 1 if s["boards_error"] else 0


def cmd_list(config: Config) -> int:
    current_state = state.load_state(config.state_dir)
    rows = [("ID", "ADAPTER", "ENABLED", "LAST FETCH", "POSTINGS")]
    for board in config.boards:
        snap = current_state.get(board["id"]) or {}
        rows.append(
            (
                board["id"],
                board["adapter"],
                "yes" if board.get("enabled", True) else "no",
                (snap.get("fetched_at") or "-")[:19],
                str(len(snap["postings"])) if snap.get("postings") is not None else "-",
            )
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return 0


def cmd_init(config: Config) -> int:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    (config.state_dir / "history").mkdir(exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"state dir:  {config.state_dir}")
    print(f"output dir: {config.output_dir}")
    failures = 0
    for board in config.enabled_boards():
        postings, error = _fetch_board(board, config)
        if error:
            failures += 1
            print(f"{board['id']}: ERROR — {error}")
        else:
            print(f"{board['id']}: ok ({len(postings)} postings)")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reqcon", description="Recon for job reqs")
    parser.add_argument("--version", action="version", version=f"reqcon {__version__}")
    parser.add_argument(
        "--config", type=Path, default=Path("boards.yaml"), help="path to boards.yaml"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="fetch all enabled boards, diff, write reports")
    scan.add_argument("--board", help="scan a single board by id")
    sub.add_parser("list", help="show configured boards and last fetch state")
    sub.add_parser("init", help="create dirs, validate config, dry-run each enabled board")

    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    try:
        if args.command == "scan":
            readme = args.config.resolve().parent / "README.md"
            return cmd_scan(config, args.board, readme)
        if args.command == "list":
            return cmd_list(config)
        return cmd_init(config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
