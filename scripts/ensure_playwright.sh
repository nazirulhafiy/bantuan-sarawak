#!/usr/bin/env bash
# Idempotent Playwright + Chromium bootstrap for Monday §2
# (scripts/check_electricity_headed.py). Safe to re-run on agent VMs.
set -euo pipefail

python3 -m pip install --user -q playwright
# Ensure ~/.local/bin is visible when pip put the CLI there
export PATH="${HOME}/.local/bin:${PATH}"
python3 -m playwright install chromium

python3 - <<'PY'
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()
print("playwright + chromium ok")
PY
