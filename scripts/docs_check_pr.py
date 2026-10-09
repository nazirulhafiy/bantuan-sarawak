#!/usr/bin/env python3
"""Fail PRs that change watched design/behaviour paths without updating docs/."""

from __future__ import annotations

import fnmatch
import os
import subprocess
import sys

# --- Watched paths (design / behaviour; not content data) ---
# Site static assets and the Python builder that emits index.html / about.html.
WATCH_PATTERNS = (
    "site/*.css",
    "site/*.js",
    "scripts/build.py",
)

FAIL_MESSAGE = (
    "This PR changes how the site looks or behaves but doesn't update docs/. "
    "Update docs/design.md, or add the no-docs-needed label if no doc change is needed."
)


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def matches_watch(path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in WATCH_PATTERNS)


def touches_docs(path: str) -> bool:
    return path == "docs" or path.startswith("docs/")


def has_label(labels_csv: str, name: str) -> bool:
    if not labels_csv.strip():
        return False
    return name in {part.strip() for part in labels_csv.split(",") if part.strip()}


def main() -> int:
    labels = os.environ.get("PR_LABELS", "")
    if has_label(labels, "no-docs-needed"):
        print("no-docs-needed label present; skipping docs requirement.")
        return 0

    base = os.environ["BASE_SHA"]
    head = os.environ["HEAD_SHA"]
    paths = changed_files(base, head)

    watched = [p for p in paths if matches_watch(p)]
    doc_paths = [p for p in paths if touches_docs(p)]

    if watched and not doc_paths:
        print(FAIL_MESSAGE, file=sys.stderr)
        print("Watched files changed:", ", ".join(watched), file=sys.stderr)
        return 1

    if watched:
        print(f"Watched and docs/ both changed ({len(doc_paths)} doc file(s)).")
    else:
        print("No watched design/behaviour files changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
