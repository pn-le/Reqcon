"""Adapter protocol, AdapterError, and shared HTTP plumbing."""

from __future__ import annotations

import time
from typing import Protocol

import httpx

from .. import __version__
from ..models import Posting

USER_AGENT = f"reqcon/{__version__} (personal job-board monitor)"
# 10s to connect/write, but large boards (Anduril: 2000+ jobs, multi-MB JSON)
# need longer to stream the response body.
TIMEOUT = httpx.Timeout(10.0, read=30.0)
MAX_RETRIES = 2  # retries beyond the first attempt
_BACKOFF_SECONDS = (1.0, 2.0)


class AdapterError(Exception):
    """Raised on any fetch/parse failure. Never return [] on error: an empty
    list means the board really has zero postings."""


class Adapter(Protocol):
    def fetch(self, board: dict, *, client: httpx.Client | None = None) -> list[Posting]: ...


def request_json(
    method: str,
    url: str,
    *,
    client: httpx.Client | None = None,
    json_body: dict | None = None,
) -> dict:
    """One HTTP request with up to MAX_RETRIES retries and backoff. Returns parsed JSON."""
    owned = client is None
    client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=True)
    try:
        last_error: Exception | None = None
        for attempt in range(1 + MAX_RETRIES):
            if attempt:
                time.sleep(_BACKOFF_SECONDS[attempt - 1])
            try:
                response = client.request(
                    method, url, json=json_body, headers={"User-Agent": USER_AGENT}
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
        raise AdapterError(f"{method} {url} failed after {1 + MAX_RETRIES} attempts: {last_error}")
    finally:
        if owned:
            client.close()
