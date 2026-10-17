#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — product photography pipeline
===================================================

Turns the phone photographs the company sent into web-ready product images.

    python3 tools/build_products.py

Input:   images/products/src/*.jpg   (originals, straight off WhatsApp)
Output:  images/products/<slug>.jpg         max 1200 px on the long edge
         images/products/thumbs/<slug>.jpg  max  640 px (what the grid loads)

Two things happen on the way through:

1. **Camera watermark removal.** Several originals carry a "SPARK 30C · 27mm
   f/1.6 …" bar burned into the bottom edge (one also has an "On this day"
   sticker). Those bars are cropped off — see WATERMARK_PX below. Each value is
   the measured height of the bar, with a couple of px of slack.
2. **Normalisation.** EXIF is read so portrait shots stay upright, then a light
   autocontrast + unsharp mask lifts phone-camera flatness without inventing
   detail. Everything is re-encoded progressive with metadata stripped.

Re-running is deterministic: same inputs, same bytes out.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "products" / "src"
OUT = ROOT / "images" / "products"
THUMBS = OUT / "thumbs"

FULL_MAX = 1200      # long edge of the lightbox image
THUMB_MAX = 640      # long edge of the grid image
QUALITY = 80

#: Source file -> (output slug, bottom pixels to crop as a watermark)
#: A 0 crop means the frame is clean. The values below are measured, not guessed:
#: count rows up from the bottom that are >60 % near-white (the SPARK bar and any
#: canvas around it), rounded up a little so the grey rule goes with it. This is
#: what keeps "SPARK 30C / 27mm f/1.6 …" and the "On this day" sticker out of the
#: product images — re-measure if new photos come in with a different bar.
CATALOGUE: list[tuple[str, str, int]] = [
    # --- windows -----------------------------------------------------------
    ("IMG-20261007-WA0009.jpg", "win-white-casement", 165),
    ("IMG-20261007-WA0011.jpg", "win-grey-casement", 62),
    ("IMG-20261007-WA0010.jpg", "win-black-frames", 62),
    ("IMG-20261007-WA0019.jpg", "win-fixed-stack", 62),
    ("IMG-20261007-WA0016.jpg", "win-louvre-tall", 0),
    # --- doors -------------------------------------------------------------
    ("IMG-20261007-WA0007.jpg", "door-white-casement", 0),
    ("IMG-20261007-WA0014.jpg", "door-white-pull", 77),
    ("IMG-20261007-WA0015.jpg", "door-grey-casement", 77),
    ("IMG-20261007-WA0013.jpg", "door-grey-single", 62),
    ("IMG-20261007-WA0012.jpg", "door-frosted-panels", 77),
    # --- glass railings ----------------------------------------------------
    ("IMG-20261007-WA0004.jpg", "rail-stair-glass", 0),
    ("IMG-20261007-WA0005.jpg", "rail-landing-glass", 0),
    ("IMG-20261007-WA0008.jpg", "rail-stainless-gold", 0),
    ("IMG-20261015-WA0006.jpg", "rail-black-glass", 0),
    # --- shopfronts, partitions & cladding ---------------------------------
    ("IMG-20261007-WA0017.jpg", "shop-structural-glazing", 0),
    ("IMG-20261007-WA0006.jpg", "shop-acp-entrance", 77),
    ("IMG-20261007-WA0018.jpg", "clad-acp-door", 0),
    ("IMG-20261007-WA0003.jpg", "glass-shower-panel", 120),
]


def load(src: Path, crop_bottom: int) -> Image.Image:
    """Open upright, drop the watermark band, and square away the colour."""
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if crop_bottom:
        w, h = img.size
        img = img.crop((0, 0, w, max(1, h - crop_bottom)))
    img = ImageOps.autocontrast(img, cutoff=(0.4, 0.4))
    return img


def save(img: Image.Image, path: Path, max_edge: int, quality: int) -> Image.Image:
    """Downscale to `max_edge` (never up), sharpen lightly, write progressive JPEG."""
    w, h = img.size
    scale = min(1.0, max_edge / max(w, h))
    if scale < 1.0:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=3))
    img.save(path, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=2)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    THUMBS.mkdir(parents=True, exist_ok=True)

    missing = [s for s, _, _ in CATALOGUE if not (SRC / s).exists()]
    if missing:
        sys.exit(f"missing source files: {', '.join(missing)}")

    total = 0
    for source, slug, crop in CATALOGUE:
        img = load(SRC / source, crop)
        full = OUT / f"{slug}.jpg"
        thumb = THUMBS / f"{slug}.jpg"
        written = save(img, full, FULL_MAX, QUALITY)
        save(img, thumb, THUMB_MAX, QUALITY - 4)
        total += full.stat().st_size + thumb.stat().st_size
        kb = full.stat().st_size / 1024
        print(f"  {slug:24} {img.width:4}x{img.height:<4} -> {written.width}x{written.height}  {kb:6.1f} KB")

    print(f"\n{len(CATALOGUE)} products, {(total / 1024):.0f} KB of JPG payload")


if __name__ == "__main__":
    print("Building product images")
    main()
