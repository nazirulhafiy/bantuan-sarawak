"""Load and validate data/analytics.json (fleet analytics registry)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "analytics.json"

GA4_ID_RE = __import__("re").compile(r"^G-[A-Z0-9]+$")
HOST_RE = __import__("re").compile(r"^[a-z0-9.-]+$")
COOKIE_RE = __import__("re").compile(r"^[A-Za-z][A-Za-z0-9_]*$")
TOKEN_RE = __import__("re").compile(r"^[a-f0-9]{32}$")


def _fail(message: str) -> None:
    raise SystemExit(f"analytics registry: {message}")


def validate_registry(payload: Any, *, path: Path | None = None) -> dict:
    """Validate registry shape. Returns the payload when valid."""
    label = path.name if path else "analytics.json"
    if not isinstance(payload, dict):
        _fail(f"{label} must be a JSON object")

    version = payload.get("version")
    if version != 1:
        _fail(f"{label} version must be 1, got {version!r}")

    cookie = payload.get("internal_cookie")
    if not isinstance(cookie, str) or not COOKIE_RE.fullmatch(cookie):
        _fail(f"{label} internal_cookie must be a simple cookie name")

    spa = payload.get("spa")
    if not isinstance(spa, bool):
        _fail(f"{label} spa must be a boolean")

    hosts = payload.get("hosts")
    if not isinstance(hosts, dict) or not hosts:
        _fail(f"{label} hosts must be a non-empty object")

    seen_hosts: set[str] = set()
    for primary, entry in hosts.items():
        if not isinstance(primary, str) or not HOST_RE.fullmatch(primary):
            _fail(f"invalid primary host {primary!r}")
        if primary in seen_hosts:
            _fail(f"duplicate host {primary!r}")
        seen_hosts.add(primary)
        if not isinstance(entry, dict):
            _fail(f"{primary} entry must be an object")

        ga4 = entry.get("ga4_measurement_id")
        if not isinstance(ga4, str) or not GA4_ID_RE.fullmatch(ga4):
            _fail(f"{primary} ga4_measurement_id must look like G-XXXXXXXX")

        token = entry.get("cf_beacon_token")
        if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
            _fail(f"{primary} cf_beacon_token must be a 32-char hex token")

        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list):
            _fail(f"{primary} aliases must be a list")
        for alias in aliases:
            if not isinstance(alias, str) or not HOST_RE.fullmatch(alias):
                _fail(f"{primary} has invalid alias {alias!r}")
            if alias in seen_hosts or alias == primary:
                _fail(f"duplicate host {alias!r}")
            seen_hosts.add(alias)

        legacy = entry.get("legacy_internal_cookies", [])
        if not isinstance(legacy, list):
            _fail(f"{primary} legacy_internal_cookies must be a list")
        for name in legacy:
            if not isinstance(name, str) or not COOKIE_RE.fullmatch(name):
                _fail(f"{primary} has invalid legacy cookie {name!r}")
            if name == cookie:
                _fail(f"{primary} legacy cookie must not equal internal_cookie")

    return payload


def load_registry(path: Path | None = None) -> dict:
    target = path or DEFAULT_PATH
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(f"missing {target}")
    except json.JSONDecodeError as exc:
        _fail(f"invalid JSON in {target}: {exc}")
    return validate_registry(payload, path=target)


def production_hosts(registry: dict, primary: str) -> tuple[str, ...]:
    entry = registry["hosts"][primary]
    aliases = entry.get("aliases") or []
    return (primary, *aliases)


def host_entry_for(registry: dict, hostname: str) -> tuple[str, dict] | None:
    for primary, entry in registry["hosts"].items():
        names = (primary, *(entry.get("aliases") or []))
        if hostname in names:
            return primary, entry
    return None


def allowed_cookies(registry: dict, primary: str) -> set[str]:
    entry = registry["hosts"][primary]
    names = {registry["internal_cookie"]}
    names.update(entry.get("legacy_internal_cookies") or [])
    return names


def all_ga4_ids(registry: dict) -> set[str]:
    return {entry["ga4_measurement_id"] for entry in registry["hosts"].values()}


def all_cf_tokens(registry: dict) -> set[str]:
    return {entry["cf_beacon_token"] for entry in registry["hosts"].values()}


if __name__ == "__main__":
    data = load_registry()
    print(f"ok: {DEFAULT_PATH.relative_to(ROOT)} ({len(data['hosts'])} host entr{'y' if len(data['hosts']) == 1 else 'ies'})")
