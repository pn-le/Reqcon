"""Report writers: changes-latest.json (machine contract) and daily Markdown digest."""

from __future__ import annotations

import json
from pathlib import Path

from .models import STUDENT_ROLE_TAG, BoardResult, Posting

MARKDOWN_KEEP_DAYS = 14


def build_report_data(run_at: str, results: list[BoardResult]) -> dict:
    boards = []
    summary = {"added": 0, "removed": 0, "changed": 0, "boards_ok": 0, "boards_error": 0}
    for r in results:
        if r.status == "error":
            boards.append({"board_id": r.board_id, "status": "error", "error": r.error})
            summary["boards_error"] += 1
            continue
        diff = r.diff
        entry = {
            "board_id": r.board_id,
            "status": r.status,
            "added": [p.to_dict() for p in diff.added],
            "removed": [p.to_dict() for p in diff.removed],
            "changed": [c.to_dict() for c in diff.changed],
            "total_postings": r.total_postings,
        }
        if diff.baseline:
            entry["baseline"] = [p.to_dict() for p in diff.baseline]
        boards.append(entry)
        summary["added"] += len(diff.added)
        summary["removed"] += len(diff.removed)
        summary["changed"] += len(diff.changed)
        summary["boards_ok"] += 1
    return {"run_at": run_at, "boards": boards, "summary": summary}


def write_json_report(output_dir: Path, data: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "changes-latest.json"
    path.write_text(json.dumps(data, indent=2))
    return path


def _tagged_first(postings: list[Posting]) -> list[Posting]:
    return sorted(postings, key=lambda p: STUDENT_ROLE_TAG not in p.tags)


def _line(posting: Posting, prefix: str = "-") -> str:
    label = f"[{posting.title}]({posting.url})"
    if STUDENT_ROLE_TAG in posting.tags:
        label = f"**{label}**"
    location = f" — {posting.location}" if posting.location else ""
    return f"{prefix} {label}{location}"


def build_markdown(run_at: str, results: list[BoardResult]) -> str:
    errors = [r for r in results if r.status == "error"]
    ok = [r for r in results if r.status != "error"]
    added = sum(len(r.diff.added) for r in ok)
    removed = sum(len(r.diff.removed) for r in ok)
    changed = sum(len(r.diff.changed) for r in ok)
    baselined = [r for r in ok if r.diff.baseline]

    lines = [f"# Reqcon — {run_at}", ""]
    if errors:
        lines.append("> ⚠️ Errored boards: " + ", ".join(f"{r.name} ({r.error})" for r in errors))
        lines.append("")

    if not added and not removed and not changed and not baselined:
        lines.append(f"No changes across {len(ok)} boards.")
        return "\n".join(lines) + "\n"

    lines.append(f"**{added} added, {removed} removed, {changed} changed** across {len(ok)} boards.")
    lines.append("")

    for r in ok:
        diff = r.diff
        if not diff.has_changes and not diff.baseline:
            continue
        lines.append(f"## {r.name} ({r.total_postings} postings)")
        if diff.baseline:
            tagged = [p for p in diff.baseline if STUDENT_ROLE_TAG in p.tags]
            lines.append(f"First run: {len(diff.baseline)} postings recorded as baseline "
                         f"({len(tagged)} tagged {STUDENT_ROLE_TAG}).")
            for p in _tagged_first(tagged):
                lines.append(_line(p))
        if diff.added:
            lines.append("### Added")
            for p in _tagged_first(diff.added):
                lines.append(_line(p))
        if diff.removed:
            lines.append("### Removed")
            for p in _tagged_first(diff.removed):
                lines.append(_line(p))
        if diff.changed:
            lines.append("### Changed")
            for c in diff.changed:
                deltas = [
                    f"{f}: {getattr(c.previous, f)!r} → {getattr(c.current, f)!r}"
                    for f in ("title", "url", "location")
                    if getattr(c.previous, f) != getattr(c.current, f)
                ]
                lines.append(_line(c.current) + " (" + "; ".join(deltas) + ")")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


OPENINGS_START = "<!-- reqcon:openings -->"
OPENINGS_END = "<!-- /reqcon:openings -->"


def build_openings_section(boards: list[dict], state: dict, updated_at: str) -> str:
    """Render the auto-updated 'Current openings' README section from board state."""
    lines = [
        OPENINGS_START,
        "## Current openings",
        "",
        f"_Student roles (intern / co-op) spotted on tracked boards. "
        f"Auto-updated by `reqcon scan` on {updated_at}._",
        "",
    ]
    for board in boards:
        snap = state.get(board["id"])
        if not snap:
            continue
        postings = [Posting.from_dict(d) for d in snap.get("postings", [])]
        tagged = [p for p in postings if STUDENT_ROLE_TAG in p.tags]
        lines.append(f"### {board['name']} — {len(tagged)} of {len(postings)} postings")
        if tagged:
            for p in sorted(tagged, key=lambda p: p.title.casefold()):
                location = f" — {p.location}" if p.location else ""
                lines.append(f"- [{p.title}]({p.url}){location}")
        else:
            lines.append("- _no intern/co-op postings right now_")
        lines.append("")
    lines.append(OPENINGS_END)
    return "\n".join(lines)


def update_readme_openings(readme_path: Path, section: str) -> bool:
    """Replace (or append) the marker-delimited openings section. Returns True if changed."""
    if not readme_path.exists():
        return False
    text = readme_path.read_text()
    if OPENINGS_START in text and OPENINGS_END in text:
        head, rest = text.split(OPENINGS_START, 1)
        _, tail = rest.split(OPENINGS_END, 1)
        new_text = head + section + tail
    else:
        new_text = text.rstrip() + "\n\n" + section + "\n"
    if new_text == text:
        return False
    readme_path.write_text(new_text)
    return True


def write_markdown_report(output_dir: Path, run_date: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"reqcon-{run_date}.md"
    path.write_text(content)
    reports = sorted(output_dir.glob("reqcon-????-??-??.md"))
    for old in reports[:-MARKDOWN_KEEP_DAYS]:
        old.unlink()
    return path
