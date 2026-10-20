#!/usr/bin/env python3
"""Fetch official scheme pages into sources/<id>.{txt,json}.

One snapshot per unique links[].url in data/schemes.json (19 URLs).
Methods: html | pdf | transcript | manual.

Usage:
  python3 scripts/snapshot_sources.py
  python3 scripts/snapshot_sources.py --only skas,electricity
  python3 scripts/snapshot_sources.py --check   # verify existing snapshots cover all URLs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMES_PATH = ROOT / "data" / "schemes.json"
SOURCES_DIR = ROOT / "sources"

USER_AGENT = (
    "Mozilla/5.0 (compatible; BantuanSarawakSnapshot/1.0; +https://bantuan.sarawak.news)"
)

# Stable source id per unique URL (shared pages keep one id).
URL_TO_SOURCE_ID: dict[str, str] = {
    "https://service.sarawak.gov.my/web/web/home/sla_view/0/821/": "skas",
    "https://www.sarawakenergy.com/media-info/announcements-publications/extension-of-electricity-discounts-for-sarawak-energy-account-holders-until-december-2026": "electricity",
    "https://myys.yayasansarawak.org.my/": "myys",
    "https://yayasansarawak.org.my/en/biasiswa-2/": "biasiswa",
    "https://meitd.sarawak.gov.my/web/subpage/webpage_view/156": "ftes",
    "https://yayasansarawak.org.my/en/bantuan-pelajar-ke-ipt2/": "bantuan-pelajar",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/163": "hdas",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/139": "sras",
    "https://hdc.sarawak.gov.my/web/subpage/webpage_view/127": "spektra-permata",
    "https://mudenr.sarawak.gov.my/web/attachment/show/?docid=U2JnN2NtQmNWZi9DWkhaYUlUMnhsdz09OjrhxKX9m6xObBhS-XQMz_Kf": "sri-pertiwi",
    "https://service.sarawak.gov.my/web/web/home/sla_view/0/742/": "schb",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/822": "kgc",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/847/": "bik",
    "https://service.sarawak.gov.my/web/web/home/sla_view/211/383/": "bib",
    "https://kpwk.sarawak.gov.my/web/subpage/webpage_view/100": "efs",
    "https://jwks.sarawak.gov.my/web/subpage/webpage_view/182": "kirwas",
    "https://service.sarawak.gov.my/web/web/home/sla_view/259/390": "smcs",
    "https://welfare.sarawak.gov.my/web/subpage/webpage_view/159": "geran-pelancaran",
    "https://welfare.sarawak.gov.my/web/subpage/webpage_view/130": "ba-bbb",
}

# Sources that must not overwrite a hand transcript / blocked fetch.
MANUAL_IDS = {"electricity"}
TRANSCRIPT_IDS = {"sras", "ftes"}

NAV_FOOTER_NOISE = re.compile(
    r"(?i)^(home|about us|services directory|payment|agency directory|"
    r"sitemap|connect with us|subscribe|copyright|disclaimer|"
    r"best viewed|visitor|hit counter|counter|login|register|"
    r"sarawakpass|english|bahasa malaysia|share this page|"
    r"is this page useful|useful\?|yes$|no$|back$|print$|"
    r"set as favourite|related services|not available|"
    r"download our mobile apps|loading\.+|ajax error|"
    r"sorry, failed to load|please contact your system|"
    r"close$|need help\?|where to get the service\?|what to bring\?)$"
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip = 0
        self._skip_tags = {"script", "style", "noscript", "svg", "nav", "footer", "header"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._skip_tags:
            self._skip += 1
        if tag.lower() in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._skip_tags and self._skip:
            self._skip -= 1
        if tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = data.strip()
        if text:
            self._chunks.append(text + " ")

    def text(self) -> str:
        raw = "".join(self._chunks)
        lines = []
        for line in raw.splitlines():
            cleaned = re.sub(r"[ \t]+", " ", line).strip()
            if not cleaned:
                continue
            if NAV_FOOTER_NOISE.match(cleaned):
                continue
            if re.fullmatch(r"\d{1,3}(,\d{3})*", cleaned):  # lone visitor counters
                continue
            lines.append(cleaned)
        # Collapse duplicate blank-ish runs
        out: list[str] = []
        prev_blank = False
        for line in lines:
            blank = not line
            if blank and prev_blank:
                continue
            out.append(line)
            prev_blank = blank
        return "\n".join(out).strip() + "\n"


def clean_html(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
            "Accept-Language": "en-MY,en;q=0.9,ms;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        return data, ctype


def pdf_to_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(data)
        tmp.flush()
        proc = subprocess.run(
            ["pdftotext", "-layout", "-nopgbrk", tmp.name, "-"],
            check=True,
            capture_output=True,
            text=True,
        )
    text = proc.stdout
    # Light cleanup
    lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip() + "\n"


def chrome_rendered_html(url: str) -> str:
    """Load URL in headless Chrome and return document HTML (hard timeout)."""
    chrome = _find_chrome()
    with tempfile.TemporaryDirectory() as td:
        profile = Path(td) / "chrome-profile"
        profile.mkdir()
        proc = subprocess.run(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                f"--user-data-dir={profile}",
                "--virtual-time-budget=8000",
                f"--user-agent={USER_AGENT}",
                "--dump-dom",
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=45,
        )
        return proc.stdout


def _find_chrome() -> str:
    for candidate in (
        "/usr/local/bin/google-chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ):
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("chrome/chromium not found")


def load_unique_sources() -> list[tuple[str, str]]:
    schemes = json.loads(SCHEMES_PATH.read_text(encoding="utf-8"))
    seen: dict[str, str] = {}
    missing: list[str] = []
    for scheme in schemes:
        for link in scheme.get("links") or []:
            url = link["url"]
            sid = URL_TO_SOURCE_ID.get(url)
            if not sid:
                missing.append(url)
                continue
            seen.setdefault(url, sid)
    if missing:
        raise SystemExit(f"Unmapped URLs (add to URL_TO_SOURCE_ID): {missing}")
    if len(seen) != 19:
        raise SystemExit(f"Expected 19 unique URLs, got {len(seen)}")
    return sorted(((sid, url) for url, sid in seen.items()), key=lambda x: x[0])


def write_snapshot(source_id: str, url: str, text: str, method: str, extra: dict | None = None) -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    text_path = SOURCES_DIR / f"{source_id}.txt"
    meta_path = SOURCES_DIR / f"{source_id}.json"
    normalized = text if text.endswith("\n") else text + "\n"
    text_path.write_text(normalized, encoding="utf-8")
    meta = {
        "url": url,
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256_text(normalized),
        "method": method,
    }
    if extra:
        meta.update(extra)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {source_id} ({method}) sha256={meta['sha256'][:12]}…")


def snapshot_one(source_id: str, url: str, *, force: bool = False) -> None:
    meta_path = SOURCES_DIR / f"{source_id}.json"
    text_path = SOURCES_DIR / f"{source_id}.txt"

    if source_id in MANUAL_IDS and not force:
        if text_path.exists() and meta_path.exists():
            print(f"  skip {source_id} (manual; keep committed transcript)")
            return
        raise SystemExit(
            f"{source_id}: method=manual needs a committed sources/{source_id}.txt "
            "(site returns 403 to automated clients)."
        )

    if source_id in TRANSCRIPT_IDS and not force:
        if text_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("method") == "transcript":
                print(f"  skip {source_id} (transcript; keep committed transcript)")
                return

    print(f"fetch {source_id}: {url}")

    if "attachment/show" in url or url.lower().endswith(".pdf"):
        data, ctype = fetch_bytes(url)
        if "pdf" not in ctype and not data[:5].startswith(b"%PDF"):
            # Still try pdftotext
            pass
        text = pdf_to_text(data)
        write_snapshot(source_id, url, text, "pdf")
        return

    try:
        data, ctype = fetch_bytes(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 403 and source_id in MANUAL_IDS:
            raise SystemExit(f"{source_id}: 403 — use method=manual transcript") from exc
        # Retry via Chrome dump-dom for JS portals
        print(f"  HTTP {exc.code}; trying headless Chrome")
        html = chrome_rendered_html(url)
        text = clean_html(html)
        write_snapshot(source_id, url, text, "html", {"via": "chrome-dump-dom"})
        return

    if "pdf" in ctype or data[:5].startswith(b"%PDF"):
        text = pdf_to_text(data)
        write_snapshot(source_id, url, text, "pdf")
        return

    html = data.decode("utf-8", errors="replace")
    text = clean_html(html)
    # Only fall back to Chrome when cleaned text is too thin (timeout hard-capped).
    if len(text) < 400:
        try:
            html = chrome_rendered_html(url)
            text = clean_html(html)
            write_snapshot(source_id, url, text, "html", {"via": "chrome-dump-dom"})
            return
        except Exception as exc:  # noqa: BLE001
            print(f"  chrome fallback failed: {exc}; keeping urllib text")
    write_snapshot(source_id, url, text, "html")


def check_coverage() -> int:
    pairs = load_unique_sources()
    missing = []
    for sid, url in pairs:
        txt = SOURCES_DIR / f"{sid}.txt"
        meta = SOURCES_DIR / f"{sid}.json"
        if not txt.exists() or not meta.exists():
            missing.append(sid)
            continue
        m = json.loads(meta.read_text(encoding="utf-8"))
        if m.get("url") != url:
            missing.append(f"{sid} url mismatch")
        if m.get("sha256") != sha256_text(txt.read_text(encoding="utf-8")):
            missing.append(f"{sid} sha256 mismatch")
        if m.get("method") not in {"html", "pdf", "transcript", "manual"}:
            missing.append(f"{sid} bad method")
    if missing:
        print("FAIL:", ", ".join(missing))
        return 1
    print(f"OK: {len(pairs)} sources")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="comma-separated source ids")
    parser.add_argument("--force", action="store_true", help="overwrite transcript/manual")
    parser.add_argument("--check", action="store_true", help="verify coverage only")
    args = parser.parse_args(argv)

    if args.check:
        return check_coverage()

    pairs = load_unique_sources()
    only = {x.strip() for x in args.only.split(",")} if args.only else None
    for sid, url in pairs:
        if only and sid not in only:
            continue
        snapshot_one(sid, url, force=args.force)
    return check_coverage()


if __name__ == "__main__":
    sys.exit(main())
