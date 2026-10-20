"""Analytics registry schema + dist check."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.analytics_registry as registry
import scripts.build as build
import scripts.check_analytics_dist as check_dist

ROOT = Path(__file__).resolve().parents[1]


class AnalyticsRegistryTests(unittest.TestCase):
    def test_load_repo_registry(self):
        data = registry.load_registry()
        self.assertEqual(data["internal_cookie"], "sn_internal")
        self.assertIs(data["spa"], False)
        site = data["hosts"]["bantuan.sarawak.news"]
        self.assertEqual(site["ga4_measurement_id"], "G-PYSEQGMJLC")
        self.assertEqual(site["cf_beacon_token"], "bfba3801f65a489185b168a7446c7a62")
        self.assertEqual(site["legacy_internal_cookies"], ["ga_internal"])

    def test_rejects_bad_ga4(self):
        payload = registry.load_registry()
        payload = json.loads(json.dumps(payload))
        payload["hosts"]["bantuan.sarawak.news"]["ga4_measurement_id"] = "bad"
        with self.assertRaises(SystemExit):
            registry.validate_registry(payload)

    def test_dist_check_passes_on_built_site(self):
        build.build()
        self.assertEqual(check_dist.main(["--dist", str(ROOT / "dist")]), 0)

    def test_dist_check_fails_on_two_loaders(self):
        build.build()
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            html = (ROOT / "dist" / "index.html").read_text(encoding="utf-8")
            page.write_text(html + html, encoding="utf-8")
            self.assertEqual(check_dist.main(["--dist", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
