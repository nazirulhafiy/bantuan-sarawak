# Fact-check replay fixtures

| File | Source |
| --- | --- |
| `schemes-pr72-base.json` | `data/schemes.json` at #72 base commit `a4e263d` |
| `schemes-pr74-base.json` | `data/schemes.json` at #74 base commit `b87780e` |
| `schemes-pr72-replay.json` | #72 base card text + current quotes/facts (misaligned where corrected) |
| `schemes-pr74-replay.json` | #74 base card text + current quotes/facts (misaligned where corrected) |

Replay fixtures are what `scripts/validate.py` must **FAIL**. Current `data/schemes.json` must **PASS**.
