# Tools

## `tools/shots.mjs`

Playwright-based screenshots for UI review and before/after comparison. Uses **playwright-core** with the system Chrome/Chromium binary (no bundled browser download).

Install once at the repo root:

```bash
npm install
```

### Capture

```bash
node tools/shots.mjs --url <https-url-or-dist-path> --out <output-dir> \
  [--crop <css-selector> | --clip x,y,w,h] \
  [--pad 24] \
  [--themes light,dark] \
  [--devices phone,desktop] \
  [--desktop-scale 2] \
  [--name slug]
```

- **phone:** 390×844 viewport, `deviceScaleFactor` 3 (~1170px-wide PNG, no downscaling).
- **desktop:** 1280×900, scale 1 (optional `--desktop-scale 2`).
- **Crop:** element box plus padding; clip width is the full viewport; height is capped at ~1.3× viewport width (taller elements are cropped from the top). Without crop, captures the first viewport.
- **Theme:** sets `localStorage` key `sarawak-theme` and `html[data-theme]` before first paint; disables transitions/animations; waits for `document.fonts.ready`; logs computed `body` background for light/dark confirmation.

Output files: `<name>-<device>-<theme>.png` (`<name>` from `--name` or derived from the URL).

### Compare

```bash
node tools/shots.mjs --compare <beforeUrl> <afterUrl> --out <dir> [same options]
```

Writes `-before`, `-after`, and a side-by-side `-compare` PNG per theme/device, and prints the differing pixel count over the overlapping region.

### Example (live site)

```bash
node tools/shots.mjs \
  --url https://bantuan.sarawak.news \
  --out ./shots \
  --crop '.scheme-head' \
  --themes light,dark \
  --devices phone
```
