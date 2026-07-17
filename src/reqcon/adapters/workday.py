"""Workday CXS jobs adapter. Unofficial endpoint — parse defensively (PRD §7.2, §12)."""

from __future__ import annotations

import httpx

from ..models import Posting
from .base import AdapterError, request_json

PAGE_SIZE = 20
MAX_PAGES = 100  # safety cap: 2000 postings


def fetch(board: dict, *, client: httpx.Client | None = None) -> list[Posting]:
    host, tenant, site = board["wd_host"], board["tenant"], board["site"]
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    postings: list[Posting] = []
    seen_ids: set[str] = set()
    offset = 0
    total = None
    for _ in range(MAX_PAGES):
        data = request_json(
            "POST", url, client=client,
            json_body={"limit": PAGE_SIZE, "offset": offset, "searchText": ""},
        )
        try:
            if total is None:  # later pages report total=0; only the first page is truthful
                total = int(data["total"])
            page = data["jobPostings"]
            if not isinstance(page, list):
                raise TypeError("jobPostings is not a list")
            for job in page:
                external_path = job["externalPath"]
                bullet_fields = job.get("bulletFields") or []
                posting_id = str(bullet_fields[0]) if bullet_fields else external_path
                if posting_id in seen_ids:
                    continue  # postings can shift between pages while paginating
                seen_ids.add(posting_id)
                postings.append(
                    Posting(
                        board_id=board["id"],
                        posting_id=posting_id,
                        title=job["title"],
                        url=f"https://{host}/en-US/{site}{external_path}",
                        location=job.get("locationsText"),
                        raw_updated_at=job.get("postedOn"),
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise AdapterError(f"workday response for {board['id']} has unexpected shape: {exc}")
        offset += PAGE_SIZE
        if offset >= total or not page:
            break
    else:
        raise AdapterError(f"workday pagination for {board['id']} exceeded {MAX_PAGES} pages")
    return postings
