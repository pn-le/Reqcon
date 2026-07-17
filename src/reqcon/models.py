"""Core dataclasses and posting identity helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

STUDENT_ROLE_TAG = "student-role"

_POSTING_FIELDS = ("board_id", "posting_id", "title", "url", "location", "raw_updated_at", "tags")


@dataclass
class Posting:
    board_id: str
    posting_id: str
    title: str
    url: str
    location: str | None = None
    raw_updated_at: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Posting":
        return cls(
            board_id=d["board_id"],
            posting_id=d["posting_id"],
            title=d["title"],
            url=d["url"],
            location=d.get("location"),
            raw_updated_at=d.get("raw_updated_at"),
            tags=list(d.get("tags") or []),
        )


@dataclass
class ChangedPosting:
    previous: Posting
    current: Posting

    def to_dict(self) -> dict:
        return {"previous": self.previous.to_dict(), "current": self.current.to_dict()}


@dataclass
class Diff:
    added: list[Posting] = field(default_factory=list)
    removed: list[Posting] = field(default_factory=list)
    changed: list[ChangedPosting] = field(default_factory=list)
    baseline: list[Posting] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


@dataclass
class BoardResult:
    board_id: str
    name: str
    status: str  # "ok" | "baseline" | "error"
    diff: Diff | None = None
    error: str | None = None
    total_postings: int | None = None


def _normalize(text: str | None) -> str:
    return " ".join((text or "").split()).casefold()


def synthetic_posting_id(title: str, location: str | None) -> str:
    """Stable identity for postings with no native ID and no per-posting URL."""
    key = _normalize(title) + "|" + _normalize(location)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def tag_postings(postings: list[Posting], keywords: list[str]) -> None:
    """Add the student-role tag to postings whose title matches any keyword.

    Whole-word match (optional plural) so 'intern' hits 'Intern'/'Interns'
    but not 'International' or 'Internal'.
    """
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")s?\b", re.IGNORECASE
    )
    for posting in postings:
        if pattern.search(posting.title) and STUDENT_ROLE_TAG not in posting.tags:
            posting.tags.append(STUDENT_ROLE_TAG)
