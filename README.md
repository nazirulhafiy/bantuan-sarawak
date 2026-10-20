# Bantuan Sarawak

Independent directory of Sarawak government assistance, for [bantuan.sarawak.news](https://bantuan.sarawak.news/). Site title, tagline, description, and About lead live only in [`data/site.json`](data/site.json); the build fills every page surface from that file. `python3 kit/generate_docs.py` writes the table below.

<!-- BEGIN GENERATED: site-copy -->
| Field | Value |
| --- | --- |
| `title` | Bantuan.Sarawak.News |
| `tagline` | Sarawak government assistance, in one directory. |
| `description` | Each scheme links to its source. |
<!-- END GENERATED: site-copy -->

This is not a news feed and not a government website. It lists state schemes. Each card has one link, to the official page its figure came from. The link name is usually the agency in charge; **Service Sarawak** when the only source is the Service Sarawak portal (`service.sarawak.gov.my`). The site does not take applications. The home page “Last updated” line is the only check date. If a ringgit amount was not on an official page, it is not shown. A time-sensitive card states the current phase, and a due date from that page is a red label.

A weekly GitHub Actions job re-fetches official source pages and opens or updates a single issue titled `source changed` when a snapshot hash changes. Separately, re-check the official pages once a week for new schemes and for cards that need updating or retiring.

## Documentation

- `docs/product.md` — what the directory is, who it is for, what a scheme card must contain, and how freshness works.
- `docs/design.md` — the live visual system.
- `docs/automation.md` — weekly source re-fetch job and the weekly content pass.
- `docs/tools.md` — `tools/shots.mjs` for consistent UI screenshots (phone 3×, light/dark).

## Build

The build uses Python 3 and the standard library only.

```bash
python3 scripts/build.py
```

Output is written to `dist/`. Preview it locally:

```bash
python3 -m http.server 43123 --directory dist
```

Then open `http://127.0.0.1:43123/`.

Checks:

```bash
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
python3 kit/generate_docs.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/check_analytics_dist.py
```

## Preview

- **Live site:** [bantuan.sarawak.news](https://bantuan.sarawak.news) updates only when changes merge to `main` (GitHub Pages).
- **Pull requests:** CI runs tests and the build; it does not publish a preview URL.
- **Local:** Run `python3 scripts/build.py`, then serve `dist/` (for example `cd dist && python3 -m http.server 8080`) and open http://localhost:8080.
- **Branch preview:** Check out a PR branch before building to preview that branch locally.
- **Fastest UI check:** Before merge or deploy, use a local preview (`python3 scripts/build.py`, then serve `dist/`). That only works on a machine with the repo checked out (for example a laptop). Hosted PR preview URLs are not set up; they would be for viewing a branch without a local checkout.

## Data

- `data/site.json` — titles, the check date, audience groups, about copy
- `data/schemes.json` — state schemes, amounts, official URLs
- `data/allowed-sources.json` — closed set of allowed source labels (`links[].label`)
- `scripts/validate.py` — fails when a scheme source label is missing or not allowlisted
- `scripts/build.py` — turns that JSON into `dist/`. It also refuses unofficial URLs and a short list of rejected phrases
- `tests/test_build.py` — checks the built pages, including claims that must stay unpublished
- `docs/federal-assistance-backlog.md` — federal schemes taken out of the directory, with the fields needed to add them back
- `site/style.css` and `site/app.js` — visual design, dark mode and the menu
- `site/social-card.png` — Open Graph image, 1200×630

`scripts/render_social_card.py` can redraw the card when Pillow and Geist are installed. The site build only copies the PNG.

## GitHub Pages

<!-- BEGIN GENERATED: hosting -->
| Field | Value |
| --- | --- |
| `hostname` | `bantuan.sarawak.news` |
| `target` | GitHub Pages |
<!-- END GENERATED: hosting -->

`.github/workflows/build.yml` runs the tests, checks generated docs, builds `dist/`, and deploys that folder with GitHub Pages. `dist/CNAME` matches the hostname above.

## Analytics

<!-- BEGIN GENERATED: analytics -->
| Field | Value |
| --- | --- |
| `ga4_measurement_id` | `G-PYSEQGMJLC` |
| `cf_beacon_token` | `bfba3801f65a489185b168a7446c7a62` |
| `internal_cookie` | `sn_internal` |
| `hosts` | `bantuan.sarawak.news`, `www.bantuan.sarawak.news` |
<!-- END GENERATED: analytics -->

The build emits one kit `data-sn-analytics-loader` script in `<head>` (production hosts only). `?internal=1` sets the shared `sn_internal` cookie so gtag sends `traffic_type: 'internal'` and the CF beacon is skipped; the loader also honours legacy `ga_internal`. CI runs `scripts/check_analytics_dist.py`. Do not reuse tokens from ai.sarawak.news or other sites. See `docs/design.md` (Analytics). Header, Contact, back-to-top, nav marks, and the loader are vendored from hub `kit/` at `kit/PIN` (`python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"`). Share image URLs use a content hash query string from `kit/python/asset_urls.py`.

## Before the public hostname works

These are not done in this repository:

1. **Custom domain.** On the `sarawak.news` zone, point `bantuan.sarawak.news` at GitHub Pages and set that hostname as the Pages custom domain. The published `CNAME` file is the Pages side of that setup. This project does not change DNS or the Cloudflare zone.
2. **Favicon.** The current mark is a provisional 🫶 emoji.

## What the directory leaves out

A scheme with no direct official page is left out. So is a payment that was not on the page checked. A scheme that is wholly past due is removed. Federal schemes are not in the published directory. The ones removed are in `docs/federal-assistance-backlog.md`.
