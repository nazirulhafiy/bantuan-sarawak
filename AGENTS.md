# Agents

For every screenshot, use `tools/shots.mjs` with `tools/shots.config.json` (3× phone, cropped to the change, light and dark).

When opening the **live** site ([bantuan.sarawak.news](https://bantuan.sarawak.news)), always use `?internal=1` so the first-party `ga_internal` cookie (~1 year) is set. That marks GA4 with `traffic_type: 'internal'` and **skips** the Cloudflare Web Analytics beacon. Example: `https://bantuan.sarawak.news/?internal=1`. Use `?internal=0` only when you intentionally clear that cookie. Local/`dist` previews and non-production hosts do not load GA or the CF beacon. See `docs/design.md` (Analytics).

Any change to how the site looks or behaves — layout, colours, fonts, icons, motion, interactions, or content structure — must update `docs/design.md` or the relevant file under `docs/` in the same PR. A PR that changes design without updating the docs is not ready.

See [docs/design.md](docs/design.md) for the live design system.

Pull requests run the **docs check** GitHub Action on design/behaviour paths. If the check fails, update `docs/` or add the **`no-docs-needed`** label when documentation does not need to change.
