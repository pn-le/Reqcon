"""Greenhouse public boards API adapter (no auth)."""

from __future__ import annotations

import httpx

from ..models import Posting
from .base import AdapterError, request_json

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def fetch(board: dict, *, client: httpx.Client | None = None) -> list[Posting]:
    url = API_URL.format(board_token=board["board_token"])
    data = request_json("GET", url, client=client)
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        raise AdapterError(f"greenhouse response for {board['id']} has no 'jobs' list")
    postings = []
    try:
        for job in jobs:
            location = (job.get("location") or {}).get("name")
            postings.append(
                Posting(
                    board_id=board["id"],
                    posting_id=str(job["id"]),
                    title=job["title"],
                    url=job["absolute_url"],
                    location=location,
                    raw_updated_at=job.get("updated_at"),
                )
            )
    except (KeyError, TypeError) as exc:
        raise AdapterError(f"greenhouse response for {board['id']} has unexpected shape: {exc}")
    return postings
