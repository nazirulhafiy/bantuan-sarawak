#!/usr/bin/env python3
"""Fail if dist/ HTML analytics drift from data/analytics.json.

Checks each built ``*.html`` page:

- exactly one analytics loader script (unified ``data-sn-analytics`` marker, or
  one script that owns both GA4 + CF; hand-split GA/CF counts as two)
- every GA4 ID and CF beacon token appears in the registry
- cookie names are the registry ``internal_cookie`` (legacy names listed on the
  host entry are allowed when documented there)
- Cloudflare ``spa`` matches the registry fleet setting

Usage::

    python scripts/check_analytics_dist.py
    python scripts/check_analytics_dist.py --dist dist
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts.analytics_registry import (
        all_cf_tokens,
        all_ga4_ids,
        allowed_cookies,
        load_registry,
    )
except ImportError:
    from analytics_registry import (
        all_cf_tokens,
        all_ga4_ids,
        allowed_cookies,
        load_registry,
    )

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAME = Path(__file__).name

LOADER_MARKER_RE = re.compile(
    r"<script\b[^>]*\bdata-sn-analytics\b[^>]*>[\s\S]*?</script>",
    re.IGNORECASE,
)
SCRIPT_RE = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)
GA_ID_RE = re.compile(r"\bG-[A-Z0-9]+\b")
GTAG_HINT = "googletagmanager.com/gtag/js"
BEACON_HINT = "cloudflareinsights.com/beacon.min.js"


def _is_analytics_script(block: str) -> bool:
    lower = block.lower()
    return (
        "data-sn-analytics" in lower
        or GTAG_HINT in lower
        or BEACON_HINT in lower
        or "data-cf-beacon" in lower
    )


def _extract_cf_payloads(html: str) -> list[dict]:
    payloads: list[dict] = []
    # Inline loader sets attribute with a JSON string literal.
    for match in re.finditer(
        r"""data-cf-beacon['"]?\s*,\s*['"](\{[^'\"]*\})['"]""",
        html,
    ):
        try:
            payloads.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    for match in re.finditer(
        r"""setAttribute\(\s*['"]data-cf-beacon['"]\s*,\s*['"](\{[^'\"]*\})['"]""",
        html,
    ):
        try:
            payloads.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    for match in re.finditer(
        r"""data-cf-beacon\s*=\s*['"](\{[^'\"]*\})['"]""",
        html,
    ):
        try:
            payloads.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return payloads


def _cookie_names_in_analytics(html: str) -> set[str]:
    """Internal-traffic cookie name literals inside analytics scripts.

    Fleet convention is ``*_internal`` (plus the shared ``sn_internal`` name).
    Avoid scanning arbitrary string literals — ``get('internal')`` and similar
    are query params, not cookies.
    """
    names: set[str] = set()
    for block in SCRIPT_RE.findall(html):
        if not _is_analytics_script(block):
            continue
        for match in re.finditer(r"""['"]([A-Za-z][A-Za-z0-9_]*_internal)['"]""", block):
            names.add(match.group(1))
        for match in re.finditer(r"""['"](sn_internal|ga_internal)['"]""", block):
            names.add(match.group(1))
    return names


def check_page(path: Path, registry: dict, primary: str) -> list[str]:
    html = path.read_text(encoding="utf-8")
    rel = str(path)
    errors: list[str] = []

    marked = LOADER_MARKER_RE.findall(html)
    analytics_scripts = [s for s in SCRIPT_RE.findall(html) if _is_analytics_script(s)]

    if marked:
        loader_count = len(marked)
        loader_kind = "marked data-sn-analytics loader"
    else:
        loader_count = len(analytics_scripts)
        loader_kind = "hand-typed analytics script"

    if loader_count == 0:
        errors.append(f"{rel}: zero analytics loaders ({loader_kind})")
    elif loader_count > 1:
        errors.append(
            f"{rel}: {loader_count} analytics loaders (want exactly one; {loader_kind})"
        )

    allowed_ids = all_ga4_ids(registry)
    # Only IDs that appear inside analytics scripts count.
    page_ids: set[str] = set()
    for block in analytics_scripts:
        page_ids.update(GA_ID_RE.findall(block))
    for ga_id in page_ids:
        if ga_id not in allowed_ids:
            errors.append(f"{rel}: GA4 id {ga_id} not in registry")

    allowed_tokens = all_cf_tokens(registry)
    payloads = _extract_cf_payloads(html)
    for payload in payloads:
        token = payload.get("token")
        if isinstance(token, str) and token not in allowed_tokens:
            errors.append(f"{rel}: CF beacon token not in registry")
        if "spa" in payload and payload["spa"] is not registry["spa"]:
            errors.append(
                f"{rel}: spa={payload['spa']!r} but registry spa={registry['spa']!r}"
            )

    # If beacon is present without parseable spa, still require registry spa when
    # the raw JSON substring is visible.
    if BEACON_HINT in html and payloads:
        pass
    elif BEACON_HINT in html and '"spa":true' in html.replace(" ", "") and registry["spa"] is False:
        errors.append(f"{rel}: spa=true but registry spa=false")
    elif BEACON_HINT in html and '"spa":false' in html.replace(" ", "") and registry["spa"] is True:
        errors.append(f"{rel}: spa=false but registry spa=true")

    allowed = allowed_cookies(registry, primary)
    found_cookies = _cookie_names_in_analytics(html)
    for name in found_cookies:
        if name not in allowed:
            errors.append(
                f"{rel}: cookie {name!r} not allowed "
                f"(registry {registry['internal_cookie']!r}; legacy ok: "
                f"{sorted(allowed - {registry['internal_cookie']})})"
            )

    # Primary shared cookie must appear whenever analytics scripts are present.
    # Legacy-only pages (e.g. hand-typed main with ga_internal) are cookie drift.
    if loader_count >= 1 and registry["internal_cookie"] not in found_cookies:
        errors.append(
            f"{rel}: missing registry cookie name {registry['internal_cookie']!r} "
            f"(found {sorted(found_cookies) or 'none'})"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Analytics dist check ({SCRIPT_NAME})")
    parser.add_argument(
        "--dist",
        type=Path,
        default=ROOT / "dist",
        help="Built site directory (default: dist/)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "data" / "analytics.json",
        help="Analytics registry JSON",
    )
    parser.add_argument(
        "--primary-host",
        default="bantuan.sarawak.news",
        help="Primary host key in the registry for this repo",
    )
    args = parser.parse_args(argv)

    print(f"{SCRIPT_NAME}: checking {args.dist} against {args.registry}")

    if not args.dist.is_dir():
        print(f"{SCRIPT_NAME}: FAIL — dist directory missing: {args.dist}", file=sys.stderr)
        return 1

    try:
        registry = load_registry(args.registry)
    except SystemExit as exc:
        print(f"{SCRIPT_NAME}: FAIL — {exc}", file=sys.stderr)
        return 1

    if args.primary_host not in registry["hosts"]:
        print(
            f"{SCRIPT_NAME}: FAIL — primary host {args.primary_host!r} missing from registry",
            file=sys.stderr,
        )
        return 1

    pages = sorted(args.dist.rglob("*.html"))
    if not pages:
        print(f"{SCRIPT_NAME}: FAIL — no HTML pages under {args.dist}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for page in pages:
        errors.extend(check_page(page, registry, args.primary_host))

    if errors:
        print(f"{SCRIPT_NAME}: FAIL ({len(errors)} issue(s))")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        f"{SCRIPT_NAME}: PASS — {len(pages)} page(s), "
        f"cookie={registry['internal_cookie']!r}, spa={registry['spa']!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
