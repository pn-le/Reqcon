"""Adapter registry: adapter name in boards.yaml → fetch function."""

from __future__ import annotations

from . import greenhouse, html_scrape, workday
from .base import Adapter, AdapterError

_REGISTRY: dict[str, Adapter] = {
    "greenhouse": greenhouse,
    "workday": workday,
    "html": html_scrape,
}


def get_adapter(name: str) -> Adapter:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise AdapterError(f"unknown adapter: {name}")
