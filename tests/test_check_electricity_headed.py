#!/usr/bin/env python3
"""Mocked paths for the on-demand electricity headed check."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_electricity_headed as elec  # noqa: E402
import snapshot_sources as snap  # noqa: E402
from text_normalize import normalize_text  # noqa: E402


class NormalizeShared(unittest.TestCase):
    def test_folds_unicode_hyphen_like_validate(self) -> None:
        snap_frag = "non \u2011commercial purposes"
        self.assertIn(normalize_text("non-commercial"), normalize_text(snap_frag))
        self.assertEqual(normalize_text("pro \u2013 rated"), normalize_text("pro-rated"))


class ComparePaths(unittest.TestCase):
    def setUp(self) -> None:
        committed = (ROOT / "sources" / "electricity.txt").read_text(encoding="utf-8")
        self.old_body = elec.strip_snapshot_preamble(committed)
        self.url = elec.load_committed_url()
        self.date = "2026-10-20"

    def test_no_change_when_normalized_match(self) -> None:
        # Same body → do nothing
        section, line = elec.compare_or_fail(
            self.old_body, None, url=self.url, date=self.date
        )
        self.assertIsNone(section)
        self.assertEqual(line, "electricity headed: no change")

    def test_changed_path_builds_section_with_diff(self) -> None:
        live = self.old_body.replace("Tariff D", "Tariff ZZZ", 1)
        section, line = elec.compare_or_fail(live, None, url=self.url, date=self.date)
        self.assertIsNotNone(section)
        assert section is not None
        self.assertIn(elec.SECTION_HEADING, section)
        self.assertIn("```diff", section)
        self.assertIn("Tariff ZZZ", section)
        self.assertIn("sha256", section)
        self.assertEqual(line, "electricity headed: source text differs")

    def test_load_failure_path_builds_status_note(self) -> None:
        section, line = elec.compare_or_fail(
            None, "HTTP 403", url=self.url, date=self.date
        )
        self.assertIsNotNone(section)
        assert section is not None
        self.assertIn(elec.SECTION_HEADING, section)
        self.assertIn("**load failure:** HTTP 403", section)
        self.assertIn(f"date: {self.date}", section)
        self.assertEqual(line, "electricity headed: load failure (HTTP 403)")

    def test_access_denied_and_empty_failure_strings(self) -> None:
        for status in ("Access Denied", "timeout", "empty body"):
            section, line = elec.compare_or_fail(
                None, status, url=self.url, date=self.date
            )
            self.assertIn(status, section or "")
            self.assertIn(status, line)

    def test_upsert_section_replaces_same_heading(self) -> None:
        first = elec.build_failure_section("HTTP 403", self.url, self.date)
        body = elec.upsert_section_body(None, first)
        self.assertIn("# source changed", body)
        second = elec.build_failure_section("timeout", self.url, self.date)
        updated = elec.upsert_section_body(body, second)
        self.assertEqual(updated.count(elec.SECTION_HEADING), 1)
        self.assertIn("timeout", updated)
        self.assertNotIn("HTTP 403", updated)

    def test_upsert_preserves_other_sections(self) -> None:
        existing = (
            "# source changed\n\n"
            "## skas (html)\n\n- sha256: `aaa` → `bbb`\n\n"
        )
        section = elec.build_failure_section("HTTP 403", self.url, self.date)
        merged = elec.upsert_section_body(existing, section)
        self.assertIn("## skas (html)", merged)
        self.assertIn(elec.SECTION_HEADING, merged)

    def test_cli_mock_changed_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            live_path = td_path / "live.txt"
            live_path.write_text(
                self.old_body.replace("Tariff D", "Tariff X", 1),
                encoding="utf-8",
            )
            out_changed = td_path / "changed.md"
            rc = elec.main(
                [
                    "--dry-run",
                    "--skip-issue",
                    "--mock-live-text",
                    str(live_path),
                    "--out",
                    str(out_changed),
                ]
            )
            self.assertEqual(rc, 0)
            body = out_changed.read_text(encoding="utf-8")
            self.assertIn(elec.SECTION_HEADING, body)
            self.assertIn("```diff", body)

            out_fail = td_path / "fail.md"
            rc = elec.main(
                [
                    "--dry-run",
                    "--skip-issue",
                    "--mock-failure",
                    "Access Denied",
                    "--out",
                    str(out_fail),
                ]
            )
            self.assertEqual(rc, 0)
            fail_body = out_fail.read_text(encoding="utf-8")
            self.assertIn("Access Denied", fail_body)
            self.assertIn("load failure", fail_body)


class SnapshotHelpers(unittest.TestCase):
    def test_strip_preamble_finds_title(self) -> None:
        raw = (
            "Sarawak Energy announcement (manual snapshot).\n"
            "note line\n"
            "EXTENSION OF ELECTRICITY DISCOUNTS FOR SARAWAK ENERGY\n"
            "body\n"
        )
        out = elec.strip_snapshot_preamble(raw)
        self.assertTrue(out.startswith("EXTENSION OF ELECTRICITY"))
        self.assertNotIn("manual snapshot", out)

    def test_sha256_stable(self) -> None:
        self.assertEqual(snap.sha256_text("a\n"), snap.sha256_text("a\n"))


if __name__ == "__main__":
    unittest.main()
