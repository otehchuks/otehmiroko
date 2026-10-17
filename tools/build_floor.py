#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — showcase floor build
===========================================

Generates the framed "showcase floor" tiles used by the Vision section: each
tile is a dark blueprint card with the real photograph cover-cropped inside it,
so the section reads as a set of mounted drawings rather than a photo dump.

    python3 tools/build_floor.py

The point of the section is honesty: the photographs are labelled as our work,
the video is the client's own footage, and nothing claims a project we did not
do. When the client supplies their own site photographs, drop them into
images/ and re-run this script.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_assets import INK_800, INK_900, SILVER_400, font, cover_resize, save_jpeg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
FLOOR = IMG / "floor"
FLOOR.mkdir(parents=True, exist_ok=True)

# (source photo, output name, caption kicker)
TILES = [
    ("project-kitchen-profile.jpg", "floor-kitchen.jpg", "KITCHEN · ALUMINIUM PROFILES"),
    ("project-shopfront.jpg", "floor-shopfront.jpg", "SHOPFRONT · CURTAIN WALL"),
    ("project-lekki-villa.jpg", "floor-villa.jpg", "RESIDENCE · SLIDING WINDOWS"),
    ("project-balustrade.jpg", "floor-balustrade.jpg", "STAIR · GLASS RAILING"),
    ("project-office-partition.jpg", "floor-partition.jpg", "OFFICE · GLASS PARTITION"),
    ("workshop-precision.jpg", "floor-workshop.jpg", "WORKSHOP · CUTTING & ASSEMBLY"),
]


def frame(src: Path, out: Path, kicker: str, size=(900, 1125)) -> None:
    """A mounted print: charcoal mount, thin silver rule, caption strip."""
    w, h = size
    mount = 46
    photo = cover_resize(Image.open(src).convert("RGB"), (w - 2 * mount, h - 2 * mount))

    card = Image.new("RGB", (w, h), INK_900)
    d = ImageDraw.Draw(card)
    card.paste(photo, (mount, mount))
    d.rectangle([mount - 1, mount - 1, w - mount, h - mount], outline=(245, 246, 247), width=2)

    # Caption strip inside the mount
    f = font(sys.modules["make_assets"].FONT_MONO, 17)
    d.text((mount, h - mount - 26), kicker, font=f, fill=SILVER_400)
    save_jpeg(card, out, quality=80, sharpen=False)


def hero() -> None:
    """Wide banner still for the video block (the poster frame)."""
    src = Image.open(IMG / "project-factory-glazing.jpg").convert("RGB")
    wide = cover_resize(src, (1600, 1000))
    # Darken toward the bottom-left so the headline stays readable over it
    scrim = Image.new("RGBA", wide.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(wide.height):
        a = int(200 * (y / wide.height) ** 1.3)
        sd.line([(0, y), (wide.width, y)], fill=INK_900 + (a,))
    wide = Image.alpha_composite(wide.convert("RGBA"), scrim).convert("RGB")
    save_jpeg(wide, FLOOR / "showcase-cover.jpg", quality=76, sharpen=False)


if __name__ == "__main__":
    print("Building showcase floor tiles")
    for src, name, kicker in TILES:
        frame(IMG / src, FLOOR / name, kicker)
    hero()
    print("Done.")
