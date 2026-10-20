#!/usr/bin/env python3
"""Compare live source fetches to committed sources/ snapshots.

Writes a markdown report of any cleaned-text hash (or transcript asset byte)
changes. Always exits 0 by default — never fails a PR, never commits.

Usage:
  python3 scripts/check_source_changes.py --out /tmp/source-changed.md
  python3 scripts/check_source_changes.py --write-baselines
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import snapshot_sources as snap  # noqa: E402

FTES_IMAGE_IDS = [
    1181,
    1182,
    1183,
    1184,
    1185,
    1171,
    1172,
    1173,
    1174,
    1176,
    1177,
    1178,
    1180,
]
SRAS_CANVA = (
    "https://www.canva.com/design/DAGcCS78TpA/pLyXdL9SE2VdQa4gWvJTPw/view?embed"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_ok(url: str) -> tuple[bytes | None, str | None]:
    try:
        data, ctype = snap.fetch_bytes(url)
        return data, ctype
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def diff_html_or_pdf(source_id: str, url: str, committed: dict) -> list[str]:
    lines: list[str] = []
    data, ctype_or_err = fetch_ok(url)
    if data is None:
        lines.append(f"- `{source_id}`: fetch failed ({ctype_or_err})")
        return lines

    ctype = (ctype_or_err or "").lower()
    if "pdf" in ctype or data[:5].startswith(b"%PDF") or "attachment/show" in url:
        try:
            text = snap.pdf_to_text(data)
        except Exception as exc:  # noqa: BLE001
            lines.append(f"- `{source_id}`: pdftotext failed ({exc})")
            return lines
    else:
        html = data.decode("utf-8", errors="replace")
        text = snap.clean_html(html)
        if len(text) < 400:
            try:
                html = snap.chrome_rendered_html(url)
                text = snap.clean_html(html)
            except Exception:
                pass

    if not text.endswith("\n"):
        text += "\n"
    new_hash = snap.sha256_text(text)
    old_hash = committed.get("sha256")
    if new_hash != old_hash:
        old_txt = (snap.SOURCES_DIR / f"{source_id}.txt").read_text(encoding="utf-8")
        lines.append(f"### `{source_id}` ({committed.get('method')})")
        lines.append(f"- url: {url}")
        lines.append(f"- sha256: `{old_hash}` → `{new_hash}`")
        lines.append("")
        lines.append("```diff")
        old_lines = old_txt.splitlines()
        new_lines = text.splitlines()
        shown = 0
        for a, b in zip(old_lines, new_lines):
            if a != b:
                lines.append(f"- {a[:200]}")
                lines.append(f"+ {b[:200]}")
                shown += 1
                if shown >= 12:
                    lines.append("…")
                    break
        if len(new_lines) != len(old_lines) and shown < 12:
            lines.append(f"… line count {len(old_lines)} → {len(new_lines)}")
        lines.append("```")
        lines.append("")
    return lines


def diff_ftes_assets(committed: dict) -> list[str]:
    lines: list[str] = []
    expected = committed.get("asset_sha256") or {}
    if not expected:
        lines.append(
            "- `ftes`: no `asset_sha256` baseline in sources/ftes.json; skip byte compare"
        )
        return lines
    changed = []
    for image_id in FTES_IMAGE_IDS:
        url = f"https://meitd.sarawak.gov.my/admin/file_manager/download/?id={image_id}"
        data, err = fetch_ok(url)
        key = str(image_id)
        if data is None:
            changed.append(f"id={image_id} fetch failed ({err})")
            continue
        digest = sha256_bytes(data)
        old = expected.get(key)
        if old and old != digest:
            changed.append(f"id={image_id}: `{old[:12]}…` → `{digest[:12]}…`")
        elif not old:
            changed.append(f"id={image_id}: no baseline (got `{digest[:12]}…`)")
    if changed:
        lines.append("### `ftes` (transcript assets)")
        lines.append(f"- url: {committed.get('url')}")
        for c in changed:
            lines.append(f"- {c}")
        lines.append("")
    return lines


def diff_sras_canva(committed: dict) -> list[str]:
    """Compare cleaned Canva embed text (raw HTML bytes are too volatile)."""
    lines: list[str] = []
    expected = committed.get("canva_sha256")
    data, err = fetch_ok(SRAS_CANVA)
    if data is None:
        lines.append(f"- `sras`: Canva embed fetch failed ({err})")
        return lines
    text = snap.clean_html(data.decode("utf-8", errors="replace"))
    if not text.endswith("\n"):
        text += "\n"
    digest = snap.sha256_text(text)
    if expected and expected != digest:
        lines.append("### `sras` (Canva embed cleaned text)")
        lines.append(f"- embed: {SRAS_CANVA}")
        lines.append(f"- canva_sha256: `{expected}` → `{digest}`")
        lines.append("")
    elif not expected:
        lines.append(
            f"- `sras`: no `canva_sha256` baseline in sources/sras.json "
            f"(live digest `{digest[:12]}…`); skip"
        )
    return lines


def build_report() -> str:
    pairs = snap.load_unique_sources()
    sections: list[str] = []
    for source_id, url in pairs:
        meta_path = snap.SOURCES_DIR / f"{source_id}.json"
        committed = json.loads(meta_path.read_text(encoding="utf-8"))
        method = committed.get("method")
        if method == "manual":
            data, _err = fetch_ok(url)
            if data is not None:
                sections.append(
                    f"### `{source_id}` (manual)\n"
                    f"- Live fetch succeeded ({len(data)} bytes) but committed "
                    f"method is manual — review whether to refresh.\n"
                )
            continue
        if method == "transcript":
            if source_id == "ftes":
                sections.extend(diff_ftes_assets(committed))
            elif source_id == "sras":
                sections.extend(diff_sras_canva(committed))
            else:
                sections.append(f"- `{source_id}`: unknown transcript handler\n")
            continue
        sections.extend(diff_html_or_pdf(source_id, url, committed))

    if not any("→" in s or "succeeded" in s or "fetch failed" in s for s in sections):
        # Keep informational skip lines out of "changed" detection
        meaningful = [s for s in sections if "###" in s or "succeeded" in s]
        if not meaningful:
            return (
                "# source changed\n\n"
                "_No cleaned-text hash or transcript-asset byte changes detected._\n"
            )

    if not sections or not any("###" in s or "succeeded" in s for s in sections):
        return (
            "# source changed\n\n"
            "_No cleaned-text hash or transcript-asset byte changes detected._\n"
        )

    body = [
        "# source changed",
        "",
        "Weekly re-fetch found differences versus the committed `sources/` snapshots.",
        "This issue is the **only** output of the job — nothing was committed.",
        "",
        *sections,
    ]
    return "\n".join(body).rstrip() + "\n"


def ensure_asset_baselines() -> None:
    """Populate transcript asset digests on committed JSON if missing."""
    ftes_meta_path = snap.SOURCES_DIR / "ftes.json"
    ftes = json.loads(ftes_meta_path.read_text(encoding="utf-8"))
    if not ftes.get("asset_sha256"):
        assets = {}
        for image_id in FTES_IMAGE_IDS:
            url = f"https://meitd.sarawak.gov.my/admin/file_manager/download/?id={image_id}"
            data, err = fetch_ok(url)
            if data is None:
                raise SystemExit(f"ftes baseline fetch failed for {image_id}: {err}")
            assets[str(image_id)] = sha256_bytes(data)
        ftes["asset_sha256"] = assets
        ftes_meta_path.write_text(json.dumps(ftes, indent=2) + "\n", encoding="utf-8")
        print(f"wrote ftes asset_sha256 ({len(assets)} images)")

    sras_meta_path = snap.SOURCES_DIR / "sras.json"
    sras = json.loads(sras_meta_path.read_text(encoding="utf-8"))
    if not sras.get("canva_sha256"):
        data, err = fetch_ok(SRAS_CANVA)
        if data is None:
            raise SystemExit(f"sras canva baseline fetch failed: {err}")
        text = snap.clean_html(data.decode("utf-8", errors="replace"))
        if not text.endswith("\n"):
            text += "\n"
        sras["canva_sha256"] = snap.sha256_text(text)
        sras_meta_path.write_text(json.dumps(sras, indent=2) + "\n", encoding="utf-8")
        print(f"wrote sras canva_sha256={sras['canva_sha256'][:12]}…")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write markdown report here")
    parser.add_argument(
        "--write-baselines",
        action="store_true",
        help="fill missing transcript asset digests in sources/*.json",
    )
    args = parser.parse_args(argv)

    if args.write_baselines:
        ensure_asset_baselines()

    report = build_report()
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"check_source_changes error (non-fatal): {exc}", file=sys.stderr)
        raise SystemExit(0) from exc
