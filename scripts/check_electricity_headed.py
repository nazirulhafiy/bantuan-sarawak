#!/usr/bin/env python3
"""On-demand headed Chromium check for the Sarawak Energy electricity page.

Opens the official announcement in **headed** Playwright Chromium, extracts
main text (same HTML cleaner as snapshot_sources), normalizes with
text_normalize.normalize_text (same rules as validate / the fact-check stack),
and compares to sources/electricity.txt.

Behaviour:
  - load failure (403, timeout, Access Denied, empty body): upsert the single
    GitHub issue titled exactly "source changed" with a status note + date
  - normalized difference vs committed snapshot: upsert that same issue with an
    "electricity (headed weekly check)" section and a short diff
  - match and loaded fine: do nothing (exit 0, no issue touch)

Not a repo schedule and not a Cursor timer. Triggered on demand via the
Maintainer Bot Monday message (section 2) through the Sarawak News Cursor
Project. See docs/automation.md.

Usage:
  python3 scripts/check_electricity_headed.py
  python3 scripts/check_electricity_headed.py --dry-run --out /tmp/elec.md
  python3 scripts/check_electricity_headed.py --mock-live-text PATH
  python3 scripts/check_electricity_headed.py --mock-failure "HTTP 403"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import snapshot_sources as snap  # noqa: E402
from text_normalize import normalize_text  # noqa: E402

SOURCE_ID = "electricity"
ISSUE_TITLE = "source changed"
SECTION_HEADING = "## electricity (headed weekly check)"
DEFAULT_URL = (
    "https://www.sarawakenergy.com/media-info/announcements-publications/"
    "extension-of-electricity-discounts-for-sarawak-energy-account-holders-"
    "until-december-2026"
)
SNAPSHOT_TXT = snap.SOURCES_DIR / f"{SOURCE_ID}.txt"
SNAPSHOT_JSON = snap.SOURCES_DIR / f"{SOURCE_ID}.json"

ACCESS_DENIED_RE = re.compile(r"access\s*denied|forbidden|request blocked", re.I)


class LoadFailure(Exception):
    """Page did not yield usable announcement text."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_committed_url() -> str:
    if SNAPSHOT_JSON.is_file():
        meta = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
        return meta.get("url") or DEFAULT_URL
    return DEFAULT_URL


def strip_snapshot_preamble(text: str) -> str:
    """Drop manual-snapshot header; keep from the announcement title onward."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("EXTENSION OF ELECTRICITY"):
            return "\n".join(lines[i:]).strip() + "\n"
    return text if text.endswith("\n") else text + "\n"


def short_diff(old: str, new: str, limit: int = 12) -> list[str]:
    lines: list[str] = ["```diff"]
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    shown = 0
    for a, b in zip(old_lines, new_lines):
        if a != b:
            lines.append(f"- {a[:200]}")
            lines.append(f"+ {b[:200]}")
            shown += 1
            if shown >= limit:
                lines.append("…")
                break
    if len(new_lines) != len(old_lines) and shown < limit:
        lines.append(f"… line count {len(old_lines)} → {len(new_lines)}")
    if shown == 0 and old != new:
        lines.append(f"- (normalized mismatch; raw lengths {len(old)} → {len(new)})")
        lines.append(f"+ first 200 live: {new[:200]!r}")
    lines.append("```")
    return lines


def fetch_live_text_headed(url: str, timeout_ms: int = 60000) -> str:
    """Open URL in headed Chromium; return cleaned main text or raise LoadFailure."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise LoadFailure(
            "playwright not installed (pip install playwright && playwright install chromium)"
        ) from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                page = browser.new_page()
                resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(2500)
                status = resp.status if resp else None
                if status is not None and status >= 400:
                    raise LoadFailure(f"HTTP {status}")
                title = page.title() or ""
                html = page.content()
                body_text = page.inner_text("body") if page.locator("body").count() else ""
            finally:
                browser.close()
    except LoadFailure:
        raise
    except PlaywrightTimeout as exc:
        raise LoadFailure("timeout") from exc
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).strip() or type(exc).__name__
        if "Timeout" in type(exc).__name__ or "timeout" in msg.lower():
            raise LoadFailure("timeout") from exc
        raise LoadFailure(msg[:200]) from exc

    if ACCESS_DENIED_RE.search(title) or ACCESS_DENIED_RE.search(body_text[:800]):
        raise LoadFailure("Access Denied")

    cleaned = snap.clean_html(html)
    if not cleaned.strip() or len(cleaned.strip()) < 80:
        raise LoadFailure("empty body")
    return cleaned


def build_changed_section(old_body: str, live: str, url: str, date: str) -> str:
    old_hash = snap.sha256_text(old_body)
    new_hash = snap.sha256_text(live)
    parts = [
        SECTION_HEADING,
        "",
        f"_Checked {date} (UTC) via headed Chromium._",
        "",
        f"- url: {url}",
        f"- sha256 (cleaned): `{old_hash}` → `{new_hash}`",
        "",
        *short_diff(old_body, live),
        "",
    ]
    return "\n".join(parts)


def build_failure_section(status: str, url: str, date: str) -> str:
    parts = [
        SECTION_HEADING,
        "",
        f"_Checked {date} (UTC) via headed Chromium._",
        "",
        f"- url: {url}",
        f"- **load failure:** {status}",
        f"- date: {date}",
        "",
        "The page did not yield usable announcement text. "
        "Re-run the headed check; do not treat silence as success.",
        "",
    ]
    return "\n".join(parts)


def upsert_section_body(existing: str | None, section: str) -> str:
    """Replace or append the electricity headed section; keep other issue content."""
    section = section.rstrip() + "\n"
    if not existing or not existing.strip():
        return f"# {ISSUE_TITLE}\n\n{section}"

    pattern = re.compile(
        r"(?ms)^## electricity \(headed weekly check\)\s*\n.*?(?=^## |\Z)"
    )
    if pattern.search(existing):
        return pattern.sub(section.rstrip() + "\n\n", existing).rstrip() + "\n"

    return existing.rstrip() + "\n\n" + section


def find_source_changed_issue() -> int | None:
    proc = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--state",
            "open",
            "--search",
            f'in:title "{ISSUE_TITLE}"',
            "--json",
            "number,title",
            "--jq",
            f'.[] | select(.title == "{ISSUE_TITLE}") | .number',
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue list failed: {proc.stderr.strip() or proc.stdout}")
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None


def read_issue_body(number: int) -> str:
    proc = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "body", "--jq", ".body"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue view failed: {proc.stderr.strip()}")
    return proc.stdout


def upsert_issue(section: str, *, dry_run: bool) -> str:
    """Open or update the single 'source changed' issue. Returns a one-line result."""
    existing_num = None if dry_run else find_source_changed_issue()
    existing_body = read_issue_body(existing_num) if existing_num else None
    body = upsert_section_body(existing_body, section)

    if dry_run:
        action = "would update" if existing_num else "would create"
        return f"electricity headed: {action} issue `{ISSUE_TITLE}` (dry-run)"

    body_file = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "electricity-source-changed.md"
    body_file.write_text(body, encoding="utf-8")

    if existing_num:
        proc = subprocess.run(
            ["gh", "issue", "edit", str(existing_num), "--body-file", str(body_file)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"gh issue edit failed: {proc.stderr.strip()}")
        return f"electricity headed: updated issue #{existing_num}"

    proc = subprocess.run(
        ["gh", "issue", "create", "--title", ISSUE_TITLE, "--body-file", str(body_file)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue create failed: {proc.stderr.strip()}")
    return f"electricity headed: created issue `{ISSUE_TITLE}` ({proc.stdout.strip()})"


def compare_or_fail(
    live_text: str | None,
    failure: str | None,
    *,
    url: str,
    date: str,
) -> tuple[str | None, str]:
    """Return (section_or_None, one_line_result)."""
    if failure:
        section = build_failure_section(failure, url, date)
        return section, f"electricity headed: load failure ({failure})"

    assert live_text is not None
    committed = SNAPSHOT_TXT.read_text(encoding="utf-8")
    old_body = strip_snapshot_preamble(committed)
    live = live_text if live_text.endswith("\n") else live_text + "\n"

    if normalize_text(old_body) == normalize_text(live):
        return None, "electricity headed: no change"

    section = build_changed_section(old_body, live, url, date)
    return section, "electricity headed: source text differs"


def run(
    *,
    dry_run: bool = False,
    mock_live_text: Path | None = None,
    mock_failure: str | None = None,
    out: Path | None = None,
    skip_issue: bool = False,
) -> int:
    url = load_committed_url()
    date = utc_today()

    live_text: str | None = None
    failure: str | None = None

    if mock_failure:
        failure = mock_failure
    elif mock_live_text is not None:
        live_text = mock_live_text.read_text(encoding="utf-8")
        if not live_text.strip():
            failure = "empty body"
            live_text = None
    else:
        try:
            live_text = fetch_live_text_headed(url)
        except LoadFailure as exc:
            failure = exc.status

    section, one_liner = compare_or_fail(live_text, failure, url=url, date=date)

    if out is not None:
        payload = section or f"# {ISSUE_TITLE}\n\n_No electricity headed change on {date}._\n"
        out.write_text(payload, encoding="utf-8")
        print(f"wrote {out}")

    if section is None:
        print(one_liner)
        return 0

    if skip_issue:
        print(one_liner)
        return 0

    result = upsert_issue(section, dry_run=dry_run)
    print(result)
    if dry_run and out is None:
        print(section)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="build the issue section but do not call gh",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="write the electricity section (or no-change stub) to this path",
    )
    parser.add_argument(
        "--mock-live-text",
        type=Path,
        help="skip browser; treat this file as cleaned live text",
    )
    parser.add_argument(
        "--mock-failure",
        type=str,
        help="skip browser; simulate a load failure with this status string",
    )
    parser.add_argument(
        "--skip-issue",
        action="store_true",
        help="never call gh (for tests); still print the one-line result",
    )
    args = parser.parse_args(argv)
    return run(
        dry_run=args.dry_run,
        mock_live_text=args.mock_live_text,
        mock_failure=args.mock_failure,
        out=args.out,
        skip_issue=args.skip_issue,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        # Never silent on unexpected errors: still try to surface a failure note.
        print(f"electricity headed: error ({exc})", file=sys.stderr)
        raise SystemExit(1) from exc
