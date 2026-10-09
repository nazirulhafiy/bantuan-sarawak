#!/usr/bin/env node
/**
 * Capture consistent UI screenshots (phone 3×, desktop, light/dark).
 *
 * Usage:
 *   node tools/shots.mjs --url <https-url|file-path> --out <dir> [options]
 *   node tools/shots.mjs --compare <beforeUrl> <afterUrl> --out <dir> [options]
 *
 * Options:
 *   --crop <css-selector>     Crop to element (+ padding); width = viewport; height capped at 1.3× width
 *   --clip <x,y,w,h>          Explicit clip rectangle (CSS pixels)
 *   --pad <n>                 Padding around --crop (default 24)
 *   --themes light,dark       Comma-separated (default light,dark)
 *   --devices phone,desktop   Comma-separated (default phone)
 *   --desktop-scale <n>       deviceScaleFactor for desktop (default 1)
 *   --name <slug>             Base filename slug (default derived from URL)
 *
 * Requires: npm install (playwright-core) and Google Chrome or Chromium on PATH.
 */

import { chromium } from "playwright-core";
import { mkdir, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const THEME_STORAGE_KEY = "sarawak-theme";

const DEVICES = {
  phone: { width: 390, height: 844, deviceScaleFactor: 3 },
  desktop: { width: 1280, height: 900, deviceScaleFactor: 1 },
};

function parseArgs(argv) {
  const args = { pad: 24, themes: ["light", "dark"], devices: ["phone"], desktopScale: 1 };
  const rest = [...argv];
  while (rest.length) {
    const flag = rest.shift();
    switch (flag) {
      case "--url":
        args.url = rest.shift();
        break;
      case "--out":
        args.out = rest.shift();
        break;
      case "--crop":
        args.crop = rest.shift();
        break;
      case "--clip":
        args.clip = rest.shift();
        break;
      case "--pad":
        args.pad = Number(rest.shift());
        break;
      case "--themes":
        args.themes = rest.shift().split(",").map((t) => t.trim()).filter(Boolean);
        break;
      case "--devices":
        args.devices = rest.shift().split(",").map((d) => d.trim()).filter(Boolean);
        break;
      case "--desktop-scale":
        args.desktopScale = Number(rest.shift());
        break;
      case "--name":
        args.name = rest.shift();
        break;
      case "--compare":
        args.compare = [rest.shift(), rest.shift()];
        break;
      case "-h":
      case "--help":
        args.help = true;
        break;
      default:
        throw new Error(`Unknown argument: ${flag}`);
    }
  }
  return args;
}

function usage() {
  console.error(`Usage:
  node tools/shots.mjs --url <url|path> --out <dir> [options]
  node tools/shots.mjs --compare <beforeUrl> <afterUrl> --out <dir> [options]`);
  process.exit(1);
}

function resolveTargetUrl(input) {
  if (!input) throw new Error("Missing URL or path");
  if (/^https?:\/\//i.test(input)) return input;
  const abs = path.resolve(input);
  if (!existsSync(abs)) throw new Error(`Path not found: ${abs}`);
  return pathToFileURL(abs).href;
}

function pathToFileURL(absPath) {
  const resolved = path.resolve(absPath);
  const href = resolved.split(path.sep).join("/");
  return `file://${href.startsWith("/") ? "" : "/"}${href}`;
}

function deriveName(input, explicit) {
  if (explicit) return slugify(explicit);
  if (!input) return "shot";
  if (/^https?:\/\//i.test(input)) {
    try {
      const u = new URL(input);
      const host = u.hostname.replace(/\./g, "-");
      const seg = u.pathname.replace(/\/+/g, "-").replace(/^-|-$/g, "");
      return slugify(seg ? `${host}-${seg}` : host);
    } catch {
      return "shot";
    }
  }
  return slugify(path.basename(input, path.extname(input)) || "local");
}

function slugify(s) {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80) || "shot";
}

function themeInitScript() {
  return ({ themeKey, themeValue }) => {
    try {
      localStorage.setItem(themeKey, themeValue);
    } catch (_) {}
    const root = document.documentElement;
    if (themeValue === "dark") root.setAttribute("data-theme", "dark");
    else root.removeAttribute("data-theme");

    const style = document.createElement("style");
    style.id = "shots-no-motion";
    style.textContent = `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
        scroll-behavior: auto !important;
      }
    `;
    (document.head || root).appendChild(style);
  };
}

async function resolveChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/local/bin/google-chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const p of candidates) {
    if (existsSync(p)) return p;
  }
  return undefined;
}

async function launchBrowser() {
  const executablePath = await resolveChrome();
  return chromium.launch({
    headless: true,
    executablePath,
    args: ["--font-render-hinting=medium", "--disable-dev-shm-usage"],
  });
}

function deviceViewport(deviceKey, desktopScale) {
  const base = DEVICES[deviceKey];
  if (!base) throw new Error(`Unknown device: ${deviceKey}`);
  if (deviceKey === "desktop") {
    return { ...base, deviceScaleFactor: desktopScale };
  }
  return base;
}

async function computeClip(page, options) {
  const { crop, clip, pad } = options;
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("No viewport");

  if (clip) {
    const parts = clip.split(",").map((n) => Number(n.trim()));
    if (parts.length !== 4 || parts.some((n) => Number.isNaN(n))) {
      throw new Error("--clip expects x,y,width,height");
    }
    return { x: parts[0], y: parts[1], width: parts[2], height: parts[3] };
  }

  if (crop) {
    const box = await page.locator(crop).first().boundingBox();
    if (!box) throw new Error(`Crop selector not found or not visible: ${crop}`);
    const vw = viewport.width;
    const maxH = Math.round(vw * 1.3);
    const y = Math.max(0, box.y - pad);
    const contentH = box.height + pad * 2;
    const height = Math.min(contentH, maxH);
    return { x: 0, y, width: vw, height };
  }

  return null;
}

async function captureOne(browser, { url, theme, deviceKey, desktopScale, crop, clip, pad }) {
  const viewport = deviceViewport(deviceKey, desktopScale);
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: viewport.deviceScaleFactor,
  });
  const page = await context.newPage();

  await page.addInitScript(themeInitScript(), {
    themeKey: THEME_STORAGE_KEY,
    themeValue: theme,
  });

  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 120_000 });
    await page.evaluate(() => document.fonts.ready);

    const bodyBg = await page.evaluate(() => {
      const bg = getComputedStyle(document.body).backgroundColor;
      const htmlBg = getComputedStyle(document.documentElement).backgroundColor;
      return { body: bg, html: htmlBg, theme: document.documentElement.getAttribute("data-theme") || "light" };
    });
    console.log(
      `[${theme}/${deviceKey}] body background: ${bodyBg.body} (html: ${bodyBg.html}, data-theme: ${bodyBg.theme})`,
    );

    const clipRect = await computeClip(page, { crop, clip, pad });
    const screenshotOptions = {
      type: "png",
      animations: "disabled",
      caret: "hide",
      scale: "device",
      omitBackground: false,
    };
    if (clipRect) screenshotOptions.clip = clipRect;

    const buffer = await page.screenshot(screenshotOptions);
    const meta = await imageMetaFromPng(buffer);
    return { buffer, meta, clipRect };
  } finally {
    await context.close();
  }
}

async function imageMetaFromPng(buffer) {
  if (buffer[0] !== 0x89 || buffer.toString("ascii", 1, 4) !== "PNG") {
    throw new Error("Not a PNG buffer");
  }
  let offset = 8;
  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    if (type === "IHDR") {
      return {
        width: buffer.readUInt32BE(offset + 8),
        height: buffer.readUInt32BE(offset + 12),
      };
    }
    offset += 12 + length + 4;
  }
  throw new Error("PNG IHDR not found");
}

async function writeShot(outDir, baseName, deviceKey, theme, suffix, buffer) {
  const parts = [baseName, deviceKey, theme];
  if (suffix) parts.push(suffix);
  const filename = `${parts.join("-")}.png`;
  const filePath = path.join(outDir, filename);
  await writeFile(filePath, buffer);
  const meta = await imageMetaFromPng(buffer);
  return { filePath, ...meta };
}

async function buildCompareComposite(beforeBuf, afterBuf) {
  const browser = await launchBrowser();
  const page = await browser.newPage();
  try {
    const b64Before = beforeBuf.toString("base64");
    const b64After = afterBuf.toString("base64");
    const result = await page.evaluate(
      async ({ b64Before, b64After }) => {
        function loadImage(b64) {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = `data:image/png;base64,${b64}`;
          });
        }
        const [imgA, imgB] = await Promise.all([loadImage(b64Before), loadImage(b64After)]);
        const w = imgA.width + imgB.width;
        const h = Math.max(imgA.height, imgB.height);
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(imgA, 0, 0);
        ctx.drawImage(imgB, imgA.width, 0);

        const dataA = readPixels(imgA);
        const dataB = readPixels(imgB);
        const minW = Math.min(imgA.width, imgB.width);
        const minH = Math.min(imgA.height, imgB.height);
        let diffPixels = 0;
        for (let y = 0; y < minH; y++) {
          for (let x = 0; x < minW; x++) {
            const i = (y * imgA.width + x) * 4;
            const j = (y * imgB.width + x) * 4;
            if (
              dataA[i] !== dataB[j] ||
              dataA[i + 1] !== dataB[j + 1] ||
              dataA[i + 2] !== dataB[j + 2] ||
              dataA[i + 3] !== dataB[j + 3]
            ) {
              diffPixels++;
            }
          }
        }

        function readPixels(img) {
          const c = document.createElement("canvas");
          c.width = img.width;
          c.height = img.height;
          const cx = c.getContext("2d");
          cx.drawImage(img, 0, 0);
          return cx.getImageData(0, 0, img.width, img.height).data;
        }

        const out = canvas.toDataURL("image/png").split(",")[1];
        return { b64: out, diffPixels, width: w, height: h };
      },
      { b64Before, b64After },
    );
    return {
      buffer: Buffer.from(result.b64, "base64"),
      diffPixels: result.diffPixels,
      width: result.width,
      height: result.height,
    };
  } finally {
    await browser.close();
  }
}

async function runSingle(args) {
  const url = resolveTargetUrl(args.url);
  const outDir = path.resolve(args.out);
  await mkdir(outDir, { recursive: true });
  const baseName = deriveName(args.url, args.name);

  const browser = await launchBrowser();
  const written = [];

  try {
    for (const deviceKey of args.devices) {
      for (const theme of args.themes) {
        const { buffer } = await captureOne(browser, {
          url,
          theme,
          deviceKey,
          desktopScale: args.desktopScale,
          crop: args.crop,
          clip: args.clip,
          pad: args.pad,
        });
        const info = await writeShot(outDir, baseName, deviceKey, theme, null, buffer);
        written.push(info);
        console.log(`${info.filePath} (${info.width}×${info.height})`);
      }
    }
  } finally {
    await browser.close();
  }
  return written;
}

async function runCompare(args) {
  const [beforeRaw, afterRaw] = args.compare;
  const beforeUrl = resolveTargetUrl(beforeRaw);
  const afterUrl = resolveTargetUrl(afterRaw);
  const outDir = path.resolve(args.out);
  await mkdir(outDir, { recursive: true });
  const baseName = deriveName(beforeRaw, args.name);

  const browser = await launchBrowser();

  try {
    for (const deviceKey of args.devices) {
      for (const theme of args.themes) {
        const before = await captureOne(browser, {
          url: beforeUrl,
          theme,
          deviceKey,
          desktopScale: args.desktopScale,
          crop: args.crop,
          clip: args.clip,
          pad: args.pad,
        });
        const after = await captureOne(browser, {
          url: afterUrl,
          theme,
          deviceKey,
          desktopScale: args.desktopScale,
          crop: args.crop,
          clip: args.clip,
          pad: args.pad,
        });

        const beforeInfo = await writeShot(outDir, baseName, deviceKey, theme, "before", before.buffer);
        const afterInfo = await writeShot(outDir, baseName, deviceKey, theme, "after", after.buffer);
        console.log(`${beforeInfo.filePath} (${beforeInfo.width}×${beforeInfo.height})`);
        console.log(`${afterInfo.filePath} (${afterInfo.width}×${afterInfo.height})`);

        const composite = await buildCompareComposite(before.buffer, after.buffer);
        const compareInfo = await writeShot(outDir, baseName, deviceKey, theme, "compare", composite.buffer);
        console.log(
          `${compareInfo.filePath} (${compareInfo.width}×${compareInfo.height}) — ${composite.diffPixels} differing pixels (overlap)`,
        );
      }
    }
  } finally {
    await browser.close();
  }
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (err) {
    console.error(err.message);
    usage();
  }

  if (args.help) usage();
  if (!args.out) {
    console.error("--out is required");
    usage();
  }

  if (args.compare) {
    if (args.compare.length !== 2 || !args.compare[0] || !args.compare[1]) {
      console.error("--compare requires two URLs or paths");
      usage();
    }
    await runCompare(args);
    return;
  }

  if (!args.url) {
    console.error("--url is required (or use --compare)");
    usage();
  }

  await runSingle(args);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
