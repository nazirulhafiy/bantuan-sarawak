# Official source snapshots

One cleaned snapshot per unique scheme `links[].url` in `data/schemes.json` (19 URLs).

| File | Method |
| --- | --- |
| `*.txt` | Cleaned main text used for fact-checking |
| `*.json` | `{url, fetched, sha256, method}` where `method` is `html`, `pdf`, `transcript`, or `manual` |

Refresh:

```bash
python3 scripts/snapshot_sources.py
```

Special cases:

- `sras` — HDC Canva embed (`method: transcript`)
- `ftes` — MEITD FAQ images (`method: transcript`)
- `electricity` — Sarawak Energy returns HTTP 403 to automated clients (`method: manual`)

Shared URLs (several cards, one snapshot): `myys`, `biasiswa`, `bantuan-pelajar`, `ba-bbb`.

Change detection (no commits) is `scripts/check_source_changes.py`, run by `.github/workflows/source-refetch.yml` on `workflow_dispatch` only (Maintainer Monday section 1 via the Sarawak News Cursor Project — no repo schedule). It opens or updates one issue titled `source changed` when hashes or transcript asset bytes differ.
