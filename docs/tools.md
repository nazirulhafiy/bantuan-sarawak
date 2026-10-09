# Tools

## `tools/shots.mjs`

Shared, site-agnostic screenshot CLI (same `tools/shots.mjs` bytes across sister repos). Site-specific defaults live in **`tools/shots.config.json`** beside the script.

Install once under `tools/`:

```bash
cd tools && npm install
```

Run from the repo root:

```bash
node tools/shots.mjs [options]
```

Uses **playwright-core** with system Chrome/Chromium (`CHROME_PATH` overrides). Default output directory is `shots/` (gitignored).

### Config (`tools/shots.config.json`)

| Field | Purpose |
|--------|---------|
| `defaultUrl` | Used when `--url` is omitted |
| `outDir` | Default `--out` directory |
| `defaults.devices`, `defaults.themes`, `defaults.crop`, `defaults.pad` | Defaults for flags below |
| `crop.minAspect` / `maxAspect` | Crop frame height vs full viewport width (roughly square; max ~1.3× wide) |
| `theme.*` | `localStorage` key, `data-theme` attribute, supported themes |
| `readySelector`, `settleMs` | Optional wait after load |

Override config path with **`--config <path>`** (default: `tools/shots.config.json`).

### Capture options

```bash
node tools/shots.mjs [--url <https-url|file|dir>] [--out <dir>] [--name <slug>] \
  [--crop <selector>] [--no-crop] [--clip x,y,w,h] [--pad <n>] \
  [--themes light,dark] [--devices phone,desktop] [--desktop-scale <n>] \
  [--full-page] [--config <path>]
```

- **`--crop` / `--no-crop`:** Crop to the first matching element (default from config, e.g. `.scheme-head`). `--no-crop` ignores the configured default; use **`--full-page`** for an uncropped full-page PNG instead of the first viewport.
- **`--clip`:** Explicit region in CSS px (overrides `--crop`).
- **phone:** 390×844 viewport, `deviceScaleFactor` 3 (~1170px-wide PNG, no downscaling).
- **desktop:** 1280×900; optional **`--desktop-scale`** (default 1).
- **Theme:** applied before first paint via config (`localStorage` + `html[data-theme]`); motion disabled; `document.fonts.ready`; logs computed `body` background.

Output: `<out>/<name>-<device>-<theme>.png` (`<name>` from `--name`, config, or URL slug).

### Compare

```bash
node tools/shots.mjs --compare <beforeUrl> <afterUrl> [--out <dir>] [same options]
```

Writes `-before`, `-after`, and side-by-side `-compare` PNGs per theme/device; prints differing pixel count.

### Example (live site, config defaults)

```bash
node tools/shots.mjs --url https://bantuan.sarawak.news --out shots
```

With `shots.config.json` defaults (`phone`, `light`+`dark`, crop `.scheme-head`), this matches the project screenshot rule: 3× phone, cropped, both themes.
