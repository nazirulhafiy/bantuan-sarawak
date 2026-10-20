#!/usr/bin/env python3
"""Re-export the shared kit analytics registry for existing script imports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kit.python.analytics_registry import *  # noqa: E402,F403
from kit.python.analytics_registry import (  # noqa: E402
    ANALYTICS_PATH,
    AnalyticsRegistry,
    HostEntry,
    load_analytics,
    validate_analytics_payload,
)

__all__ = [
    "ANALYTICS_PATH",
    "AnalyticsRegistry",
    "HostEntry",
    "load_analytics",
    "load_registry",
    "validate_analytics_payload",
    "validate_registry",
    "production_hosts",
    "allowed_cookies",
    "all_ga4_ids",
    "all_cf_tokens",
]


def load_registry(path: Path | None = None) -> dict:
    """Return the raw registry dict (validated). Prefer ``load_analytics`` for typed access."""
    target = path or ANALYTICS_PATH
    load_analytics(target)  # validate
    return json.loads(target.read_text(encoding="utf-8"))


def validate_registry(payload, *, path: Path | None = None) -> dict:
    """Validate a payload dict; return it unchanged when valid."""
    label = str(path) if path else "data/analytics.json"
    validate_analytics_payload(payload, path=label)
    return payload


def production_hosts(registry: dict | AnalyticsRegistry, primary: str) -> tuple[str, ...]:
    if isinstance(registry, AnalyticsRegistry):
        entry = registry.hosts[primary]
        return entry.hostnames
    entry = registry["hosts"][primary]
    aliases = entry.get("aliases") or []
    return (primary, *aliases)


def allowed_cookies(registry: dict | AnalyticsRegistry, primary: str) -> set[str]:
    if isinstance(registry, AnalyticsRegistry):
        return set(registry.honour_cookies)
    entry = registry["hosts"][primary]
    names = {registry["internal_cookie"]}
    names.update(entry.get("legacy_internal_cookies") or [])
    return names


def all_ga4_ids(registry: dict | AnalyticsRegistry) -> set[str]:
    if isinstance(registry, AnalyticsRegistry):
        return registry.ga4_ids()
    return {entry["ga4_measurement_id"] for entry in registry["hosts"].values()}


def all_cf_tokens(registry: dict | AnalyticsRegistry) -> set[str]:
    if isinstance(registry, AnalyticsRegistry):
        return registry.cf_tokens()
    return {entry["cf_beacon_token"] for entry in registry["hosts"].values()}


if __name__ == "__main__":
    data = load_registry()
    print(
        f"ok: data/analytics.json "
        f"({len(data['hosts'])} host entr{'y' if len(data['hosts']) == 1 else 'ies'})"
    )
