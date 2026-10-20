"""Tests for allowed source-label validation (events #24 / AI #66 pattern)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import schemes_lib as L  # noqa: E402


class AllowedSourcesFile(unittest.TestCase):
    def test_allowed_sources_file_is_sorted_unique(self):
        payload = json.loads((ROOT / "data" / "allowed-sources.json").read_text())
        self.assertIsInstance(payload, list)
        self.assertEqual(payload, sorted(payload, key=str.casefold))
        self.assertEqual(len(payload), len(set(payload)))
        self.assertTrue(
            all(isinstance(name, str) and name.strip() == name for name in payload)
        )

    def test_published_source_labels_are_allowed(self):
        allowed = L.load_allowed_sources()
        schemes = L.load_json(L.SCHEMES)
        used = {scheme["links"][0]["label"] for scheme in schemes}
        self.assertTrue(used)
        self.assertTrue(used.issubset(allowed), sorted(used - allowed))


class Validation(unittest.TestCase):
    def setUp(self):
        self.allowed = {
            "Housing Development Corporation",
            "Service Sarawak",
            "Yayasan Sarawak",
        }
        self.good = {
            "id": "test-scheme",
            "links": [
                {
                    "label": "Housing Development Corporation",
                    "url": "https://hdc.sarawak.gov.my/web/subpage/webpage_view/139",
                }
            ],
        }

    def test_accepts_allowed_label(self):
        self.assertEqual(L.validate_scheme_source(self.good, self.allowed), [])

    def test_rejects_missing_links(self):
        errs = L.validate_scheme_source({"id": "x"}, self.allowed)
        self.assertTrue(any("exactly one source link" in e for e in errs))

    def test_rejects_blank_label(self):
        item = copy.deepcopy(self.good)
        item["links"][0]["label"] = "  "
        errs = L.validate_scheme_source(item, self.allowed)
        self.assertTrue(any("source label is required" in e for e in errs))

    def test_rejects_unknown_label(self):
        item = copy.deepcopy(self.good)
        item["links"][0]["label"] = "Fake Agency"
        errs = L.validate_scheme_source(item, self.allowed)
        self.assertTrue(any("not in data/allowed-sources.json" in e for e in errs))

    def test_rejects_near_miss_short_label(self):
        # Historical mistake shape: short form instead of the full agency name.
        item = copy.deepcopy(self.good)
        item["links"][0]["label"] = "HDC"
        errs = L.validate_scheme_source(item, self.allowed)
        self.assertTrue(any("not in data/allowed-sources.json" in e for e in errs))

    def test_collection_rejects_duplicate_id(self):
        a = copy.deepcopy(self.good)
        errs = L.validate_collection([a, a], self.allowed)
        self.assertTrue(any("duplicate id" in e for e in errs))


class ValidateScript(unittest.TestCase):
    def test_cli_passes_on_repo_schemes(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK:", result.stdout)


if __name__ == "__main__":
    unittest.main()
