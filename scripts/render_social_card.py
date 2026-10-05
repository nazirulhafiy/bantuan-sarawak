#!/usr/bin/env python3
"""Regenerate site/social-card.png. Requires Pillow and Geist. The build does not."""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as error:
    raise SystemExit("Pillow is required to regenerate the social card.") from error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "social-card.png"
SUBTITLE = "Each scheme links to its source."

W, H = 1200, 630
MARGIN_X = 56
RED = (203, 29, 37)
YELLOW = (243, 195, 38)
BLACK = (0, 0, 0)
INK = (0, 0, 0)
MUTED = (166, 168, 173)
WHITE = (255, 255, 255)


def find_geist() -> Path:
    roots: list[Path] = []
    if os.environ.get("GEIST_FONTS"):
        roots.append(Path(os.environ["GEIST_FONTS"]))
    roots.append(ROOT / "node_modules" / "geist" / "dist" / "fonts")
    roots.extend(Path(p) for p in glob.glob(os.path.expanduser("~/.bun/install/cache/geist@*/dist/fonts")))
    for root in roots:
        regular = root / "geist-sans" / "Geist-Regular.ttf"
        if regular.is_file():
            return root
    raise SystemExit(
        "Geist fonts not found. Install with `npm i geist` in the repo root, "
        "or set GEIST_FONTS to a directory containing geist-sans/Geist-*.ttf. "
        "CI does not regenerate the card; site/social-card.png is the source of truth."
    )


def load_fonts(geist: Path) -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    sans = geist / "geist-sans"
    brand = ImageFont.truetype(sans / "Geist-SemiBold.ttf", 22)
    title = ImageFont.truetype(sans / "Geist-SemiBold.ttf", 52)
    body = ImageFont.truetype(sans / "Geist-Regular.ttf", 24)
    return brand, title, body


def draw_bar(draw: ImageDraw.ImageDraw) -> None:
    y0, y1 = 568, 576
    draw.rectangle((MARGIN_X, y0, 418, y1), fill=RED)
    draw.rectangle((418, y0, 780, y1), fill=YELLOW)
    draw.rectangle((780, y0, 1143, y1), fill=BLACK)


def main() -> None:
    geist = find_geist()
    brand, title, body = load_fonts(geist)

    image = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(image)

    draw.text((MARGIN_X, 76), "Bantuan.Sarawak.News", font=brand, fill=INK)

    y = 188
    for line in ("Sarawak government assistance,", "in one directory."):
        draw.text((MARGIN_X, y), line, font=title, fill=INK)
        y += 86

    draw.text((MARGIN_X, 364), SUBTITLE, font=body, fill=MUTED)
    draw_bar(draw)

    image.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
