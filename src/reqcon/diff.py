"""Diff engine: compare a board's current fetch against its previous snapshot.

Encapsulates the rules from PRD §7.3 and §12:
- first-ever run reports postings as baseline, not added
- an AdapterError carries the previous snapshot forward untouched
- a drop to zero from a nonzero snapshot needs two consecutive zero runs
  before postings are marked removed (suspicious-drop rule)
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ChangedPosting, Diff, Posting

_COMPARED_FIELDS = ("title", "url", "location")


@dataclass
class BoardOutcome:
    status: str  # "ok" | "baseline" | "error"
    diff: Diff | None
    error: str | None
    new_snapshot: dict | None  # None means carry the previous snapshot forward


def diff_postings(previous: list[Posting], current: list[Posting]) -> Diff:
    prev_by_id = {p.posting_id: p for p in previous}
    curr_by_id = {p.posting_id: p for p in current}
    diff = Diff()
    diff.added = [p for pid, p in curr_by_id.items() if pid not in prev_by_id]
    diff.removed = [p for pid, p in prev_by_id.items() if pid not in curr_by_id]
    for pid, curr in curr_by_id.items():
        prev = prev_by_id.get(pid)
        if prev and any(getattr(prev, f) != getattr(curr, f) for f in _COMPARED_FIELDS):
            diff.changed.append(ChangedPosting(previous=prev, current=curr))
    return diff


def _snapshot(postings: list[Posting], fetched_at: str, zero_pending: bool = False) -> dict:
    snap = {"fetched_at": fetched_at, "postings": [p.to_dict() for p in postings]}
    if zero_pending:
        snap["zero_pending"] = True
    return snap


def evaluate_board(
    prev_snapshot: dict | None,
    current: list[Posting] | None,
    error: str | None,
    fetched_at: str,
) -> BoardOutcome:
    """Turn a fetch result (postings or error) into a diff outcome + new snapshot."""
    if error is not None:
        return BoardOutcome(status="error", diff=None, error=error, new_snapshot=None)
    assert current is not None

    if prev_snapshot is None:
        return BoardOutcome(
            status="baseline",
            diff=Diff(baseline=list(current)),
            error=None,
            new_snapshot=_snapshot(current, fetched_at),
        )

    previous = [Posting.from_dict(d) for d in prev_snapshot.get("postings", [])]

    if not current and previous and not prev_snapshot.get("zero_pending"):
        # Suspicious drop: keep the old postings, flag it, confirm on the next run.
        carried = dict(prev_snapshot)
        carried["zero_pending"] = True
        return BoardOutcome(
            status="error",
            diff=None,
            error=f"suspicious drop to zero postings (previously {len(previous)}); "
            "will treat as removed if the next run is also zero",
            new_snapshot=carried,
        )

    return BoardOutcome(
        status="ok",
        diff=diff_postings(previous, current),
        error=None,
        new_snapshot=_snapshot(current, fetched_at),
    )
