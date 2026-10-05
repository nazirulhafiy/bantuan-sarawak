#!/usr/bin/env python3
"""Regenerate site/social-card.png in the approved Design Bot layout.

Matches the live AI.Sarawak.News card: white ground, black site name,
two-line black headline, one gray subtitle, full-width Sarawak flag bar.
No left red bar, no short stripe under the name, no date, no URL.
Requires Pillow and the Geist variable font.
"""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as error:
    raise SystemExit("Pillow is required to regenerate the social card.") from error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "social-card.png"
GEIST = "/usr/share/fonts/truetype/sand-box/google/Geist/Geist-VariableFont_wght.ttf"

SITE_NAME = "Bantuan.Sarawak.News"
HEADLINE = ("Sarawak government assistance,", "in one directory.")
SUBTITLE = "Each scheme links to its source."

WHITE = (255, 255, 255)
INK = (0, 0, 0)
GRAY = (78, 82, 91)
RED = (203, 29, 37)
YELLOW = (243, 195, 38)
BLACK = (0, 0, 0)


def font(size: int, weight: int) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(GEIST, size)
    face.set_variation_by_axes([weight])
    return face


def main() -> None:
    image = Image.new("RGB", (1200, 630), WHITE)
    draw = ImageDraw.Draw(image)

    draw.text((56, 58), SITE_NAME, font=font(32, 800), fill=INK)
    draw.text((56, 160), HEADLINE[0], font=font(64, 900), fill=INK)
    draw.text((56, 244), HEADLINE[1], font=font(64, 900), fill=INK)
    draw.text((56, 348), SUBTITLE, font=font(32, 400), fill=GRAY)

    x0, x1, y0, y1 = 56, 1142, 568, 576
    seg = (x1 - x0) // 3
    draw.rectangle((x0, y0, x0 + seg, y1), fill=RED)
    draw.rectangle((x0 + seg, y0, x0 + 2 * seg, y1), fill=YELLOW)
    draw.rectangle((x0 + 2 * seg, y0, x1, y1), fill=BLACK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
