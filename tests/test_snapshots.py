"""Coverage check for sources/ snapshots."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SnapshotCoverageTests(unittest.TestCase):
    def test_nineteen_sources_present(self) -> None:
        proc = subprocess.run(
            ["python3", "scripts/snapshot_sources.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK: 19 sources", proc.stdout)


if __name__ == "__main__":
    unittest.main()
