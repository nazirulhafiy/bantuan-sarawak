# Bantuan Sarawak

Independent directory of Sarawak government assistance, for [bantuan.sarawak.news](https://bantuan.sarawak.news/).

This is not a news feed and not a government website. It lists state and federal schemes, with the amount and the official page each figure came from. The figures were checked on 4 October 2026. If a ringgit amount was not on an official page, it is not shown.

Applications are made on the official pages linked from each scheme.

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
python3 -m unittest discover -s tests -v
```

## Data

- `data/site.json` — titles, the “what changed” list, audience groups, about copy
- `data/schemes.json` — schemes, State or Federal, amounts, official URLs
- `site/style.css` and `site/app.js` — visual design and the dark-mode, menu, and State/Federal filter
- `site/social-card.png` — Open Graph image, 1200×630

`scripts/render_social_card.py` can redraw the card when Pillow and Noto Sans are installed. The site build only copies the PNG.

## GitHub Pages

`.github/workflows/build.yml` runs the tests, builds `dist/`, and deploys that folder with GitHub Pages. `dist/CNAME` is `bantuan.sarawak.news`.

## Before the public hostname works

These are not done in this repository:

1. **Custom domain.** On the `sarawak.news` zone, point `bantuan.sarawak.news` at GitHub Pages and set that hostname as the Pages custom domain. The published `CNAME` file is the Pages side of that setup. This project does not change DNS or the Cloudflare zone.
2. **Cloudflare Web Analytics.** Create a new Web Analytics site for `bantuan.sarawak.news`. Put its token in `CLOUDFLARE_WEB_ANALYTICS_TOKEN` in `scripts/build.py`. An empty token means the beacon is left out. Do not reuse the token from ai.sarawak.news.
3. **Favicon.** The current mark is a provisional 🫶 emoji.

## What the directory leaves out

Names and payment figures that were not on an official page in the 4 October 2026 check are omitted. That includes the HDRAS monthly repayment, which UKAS names as a scheme but which is not given as a ringgit amount on the HDC page.
