"""HTML fallback adapter using Scrapling (optional extra: pip install reqcon[scrape]).

Config keys per board:
  url            page to fetch (required)
  item_selector  CSS selector for one posting element (required)
  title_selector CSS selector inside the item for the title (default: "a")
  url_selector   CSS selector inside the item for the link (default: "a")
  location_selector  optional CSS selector inside the item for the location
  stealth        true to use StealthyFetcher (headless browser) instead of plain HTTP
"""

from __future__ import annotations

from urllib.parse import urljoin

import httpx

from ..models import Posting, synthetic_posting_id
from .base import AdapterError


def fetch(board: dict, *, client: httpx.Client | None = None) -> list[Posting]:
    # client is unused (scrapling does its own I/O) but kept for adapter signature parity
    if not board.get("item_selector"):
        raise AdapterError(f"board '{board['id']}': selector not configured (item_selector)")
    try:
        from scrapling.fetchers import Fetcher, StealthyFetcher
    except ImportError:
        raise AdapterError(
            "scrapling is not installed — install the scrape extra: pip install 'reqcon[scrape]'"
        )

    url = board["url"]
    try:
        if board.get("stealth"):
            page = StealthyFetcher.fetch(url, headless=True)
        else:
            page = Fetcher.get(url, timeout=10, follow_redirects=True)
    except Exception as exc:
        raise AdapterError(f"fetch of {url} failed: {exc}")
    if getattr(page, "status", 200) != 200:
        raise AdapterError(f"fetch of {url} returned HTTP {page.status}")

    return extract_postings(page, board)


def _css_first(element, selector: str):
    matches = element.css(selector)
    return matches[0] if matches else None


def extract_postings(page, board: dict) -> list[Posting]:
    """Extract postings from a fetched Scrapling page. Split out for fixture-based tests."""
    items = page.css(board["item_selector"])
    if not items:
        raise AdapterError(
            f"board '{board['id']}': item_selector {board['item_selector']!r} matched nothing"
        )
    title_sel = board.get("title_selector", "a")
    url_sel = board.get("url_selector", "a")
    location_sel = board.get("location_selector")

    postings = []
    for item in items:
        title_el = _css_first(item, title_sel)
        if title_el is None:
            continue
        title = " ".join(str(title_el.text).split())
        link_el = _css_first(item, url_sel)
        href = link_el.attrib.get("href") if link_el is not None else None
        location = None
        if location_sel:
            loc_el = _css_first(item, location_sel)
            if loc_el is not None:
                location = " ".join(str(loc_el.text).split()) or None
        if href:
            absolute = urljoin(board["url"], href)
            posting_id = absolute
        else:
            absolute = board["url"]
            posting_id = synthetic_posting_id(title, location)
        postings.append(
            Posting(
                board_id=board["id"],
                posting_id=posting_id,
                title=title,
                url=absolute,
                location=location,
            )
        )
    if not postings:
        raise AdapterError(f"board '{board['id']}': selectors matched items but yielded no postings")
    return postings
