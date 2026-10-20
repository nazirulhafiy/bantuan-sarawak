"""Replay proof: fact-check must FAIL on #72/#74 bases and PASS on current schemes."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "scripts" / "validate.py"
FIXTURES = ROOT / "tests" / "fixtures"


def _run_validate(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class FactcheckReplay(unittest.TestCase):
    def test_current_schemes_pass(self) -> None:
        result = _run_validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK:", result.stdout)
        self.assertIn("PASS fact-check", result.stdout)

    def test_pr72_base_fails_named_cards(self) -> None:
        """#72 base a4e263d — wrong BKK/Books/SRAS/BA amounts and related tokens."""
        fixture = FIXTURES / "schemes-pr72-replay.json"
        self.assertTrue(fixture.exists(), fixture)
        result = _run_validate("--schemes", str(fixture), "--skip-source-labels")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stdout)
        # Cards and rules called out in the plan's evidence set
        self.assertIn("bkk-ipt: token.rm", result.stdout)
        self.assertIn("book-voucher: token.rm", result.stdout)
        self.assertIn("sras: token.rm", result.stdout)
        self.assertIn("ba: token.rm", result.stdout)
        self.assertIn("bbb: token.rm", result.stdout)
        self.assertIn("ftes: quote.numbers", result.stdout)
        # Unsupported EFS "Withdraw at 18" and Sri Pertiwi "up to RM10,000" (no RM4,000)
        self.assertIn("efs: token.claim", result.stdout)
        self.assertIn("withdraw at 18", result.stdout)
        self.assertIn("sri-pertiwi: fact.on_card", result.stdout)
        self.assertIn("pertiwi-income-low", result.stdout)

    def test_pr74_base_fails_named_cards(self) -> None:
        """#74 base b87780e — FTES amount framing, SRAS/Sri Pertiwi incomplete lines."""
        fixture = FIXTURES / "schemes-pr74-replay.json"
        self.assertTrue(fixture.exists(), fixture)
        result = _run_validate("--schemes", str(fixture), "--skip-source-labels")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stdout)
        self.assertIn("ftes: quote.numbers", result.stdout)
        self.assertIn("sras: quote.missing", result.stdout)
        self.assertIn("sri-pertiwi: quote.missing", result.stdout)


if __name__ == "__main__":
    unittest.main()
