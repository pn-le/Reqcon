"""Self-updating README section (PRD §8.3).

Owns everything between the REQCON:START/END markers: a status line,
a "New this week" table, and a collapsed full posting list. Rendering is
deterministic (stable sorts) so a no-change run leaves the README
byte-identical and CI produces no commit.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from .models import STUDENT_ROLE_TAG, BoardResult, Posting

START_MARKER = "<!-- REQCON:START -->"
END_MARKER = "<!-- REQCON:END -->"
NEW_THIS_WEEK_CAP = 30
ALL_POSTINGS_CAP = 400
_STATUS_LINE_PREFIX = "**Last scan:**"


class ReadmeError(Exception):
    pass


def _status_emoji(result: BoardResult | None) -> str:
    if result is None:
        return "▫️"  # board not part of this run (--board scan)
    if result.status in ("ok", "baseline"):
        return "✅"
    if result.status == "skipped-ci":
        return "⏭️"
    return "⚠️"


def _row(board_name: str, p: Posting) -> str:
    grad = "🎓 " if STUDENT_ROLE_TAG in p.tags else ""
    location = p.location or "—"
    return f"| {grad}{board_name} | [{p.title}]({p.url}) | {location} | {p.first_seen or '—'} |"


def render_section(
    boards: list[dict],
    state: dict,
    results: list[BoardResult],
    now_local,
    latest_digest: str | None,
) -> str:
    """Build the marker-delimited README content. `now_local` is an aware
    datetime in America/New_York."""
    by_id = {r.board_id: r for r in results}
    postings_by_board: dict[str, list[Posting]] = {}
    for board in boards:
        snap = state.get(board["id"])
        if snap:
            postings_by_board[board["id"]] = [
                Posting.from_dict(d) for d in snap.get("postings", [])
            ]
    board_names = {b["id"]: b["name"] for b in boards}

    added = sum(len(r.diff.added) for r in results if r.diff)
    removed = sum(len(r.diff.removed) for r in results if r.diff)

    lines = [
        f"{_STATUS_LINE_PREFIX} {now_local.strftime('%Y-%m-%d %H:%M %Z')} · "
        f"{len(boards)} boards · {added} new · {removed} removed",
        "",
        " · ".join(f"{_status_emoji(by_id.get(b['id']))} {b['name']}" for b in boards),
        "",
        "### New this week",
        "",
    ]

    week_ago = (now_local.date() - timedelta(days=6)).isoformat()
    fresh = [
        (board_names[bid], p)
        for bid, postings in postings_by_board.items()
        for p in postings
        if p.first_seen and p.first_seen >= week_ago
    ]
    # student-role first, then first_seen desc, then board_id, then title (§8.3)
    fresh.sort(
        key=lambda np: (
            STUDENT_ROLE_TAG not in np[1].tags,
            _desc(np[1].first_seen or ""),
            np[1].board_id,
            np[1].title.casefold(),
        )
    )
    if fresh:
        lines += ["| Company | Role | Location | First seen |", "|---|---|---|---|"]
        lines += [_row(name, p) for name, p in fresh[:NEW_THIS_WEEK_CAP]]
        overflow = len(fresh) - NEW_THIS_WEEK_CAP
        if overflow > 0:
            target = f"reports/{latest_digest}" if latest_digest else "reports/"
            lines.append("")
            lines.append(f"…and {overflow} more — see the [latest digest]({target}).")
    else:
        lines.append("_No new postings in the last 7 days._")

    total = sum(len(p) for p in postings_by_board.values())
    lines += ["", "<details>", f"<summary>All tracked postings ({total})</summary>", ""]
    rows_used = 0
    for board in boards:
        postings = postings_by_board.get(board["id"])
        if postings is None:
            continue
        lines.append(f"**{board['name']}** ({len(postings)})")
        for p in sorted(
            postings,
            key=lambda p: (STUDENT_ROLE_TAG not in p.tags, p.title.casefold()),
        ):
            if rows_used >= ALL_POSTINGS_CAP:
                lines.append(f"\n_…truncated at {ALL_POSTINGS_CAP} rows ({total} total)._")
                break
            location = f" — {p.location}" if p.location else ""
            grad = "🎓 " if STUDENT_ROLE_TAG in p.tags else ""
            lines.append(f"- {grad}[{p.title}]({p.url}){location}")
            rows_used += 1
        else:
            lines.append("")
            continue
        break
    lines += ["", "</details>"]
    return "\n".join(lines)


def _desc(s: str) -> tuple:
    """Sort key inverting lexicographic order for ISO dates (desc sort)."""
    return tuple(-ord(c) for c in s)


def _strip_volatile(section: str) -> str:
    """Drop the status line (its timestamp changes every run) for comparison."""
    return "\n".join(
        line for line in section.splitlines() if not line.startswith(_STATUS_LINE_PREFIX)
    )


def update_readme(readme_path: Path, section: str) -> bool:
    """Replace the marker-delimited section. Returns True if the file was written.

    Fails loudly if the file or markers are missing (PRD §8.3). Skips the write
    when nothing but the status-line timestamp changed, so a no-change scan
    leaves the README byte-identical.
    """
    if not readme_path.exists():
        raise ReadmeError(f"README not found: {readme_path}")
    text = readme_path.read_text()
    if START_MARKER not in text or END_MARKER not in text:
        raise ReadmeError(
            f"markers {START_MARKER} / {END_MARKER} missing from {readme_path}; "
            "refusing to modify the file"
        )
    head, rest = text.split(START_MARKER, 1)
    old_section, tail = rest.split(END_MARKER, 1)
    if _strip_volatile(old_section.strip("\n")) == _strip_volatile(section):
        return False
    readme_path.write_text(head + START_MARKER + "\n" + section + "\n" + END_MARKER + tail)
    return True
