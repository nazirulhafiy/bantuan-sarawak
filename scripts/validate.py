#!/usr/bin/env python3
"""Validate data/schemes.json: every scheme needs an allowed source label."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schemes_lib as L  # noqa: E402

schemes = L.load_json(L.SCHEMES)
allowed = L.load_allowed_sources()
errs = L.validate_collection(schemes, allowed)
if errs:
    print("\n".join(errs))
    sys.exit(1)
print(
    f"OK: {len(schemes)} schemes; source labels in allowed set ({len(allowed)} names)"
)
