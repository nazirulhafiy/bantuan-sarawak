#!/usr/bin/env python3
"""Regenerate site/social-card.png. Requires Pillow. The build does not."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as error:
    raise SystemExit("Pillow is required to regenerate the social card.") from error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "social-card.png"
REGULAR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

RED = (210, 38, 48)
YELLOW = (247, 201, 72)
BLACK = (17, 17, 17)
INK = (17, 24, 39)
MUTED = (107, 114, 128)
WHITE = (255, 255, 255)


def main() -> None:
    image = Image.new("RGB", (1200, 630), WHITE)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 16, 630), fill=RED)
    bold = ImageFont.truetype(BOLD, 28)
    title = ImageFont.truetype(BOLD, 72)
    body = ImageFont.truetype(REGULAR, 28)
    small = ImageFont.truetype(BOLD, 26)

    draw.text((88, 78), "BANTUAN.SARAWAK.NEWS", font=bold, fill=RED)
    draw.rectangle((88, 128, 176, 136), fill=RED)
    draw.rectangle((176, 128, 264, 136), fill=YELLOW)
    draw.rectangle((264, 128, 352, 136), fill=BLACK)

    y = 196
    for line in ("Sarawak government", "assistance, in one", "directory."):
        draw.text((88, y), line, font=title, fill=INK)
        y += 84

    draw.text((88, 500), "State schemes  ·  Checked 4 October 2026", font=body, fill=MUTED)
    draw.text((88, 556), "bantuan.sarawak.news", font=small, fill=BLACK)
    image.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
