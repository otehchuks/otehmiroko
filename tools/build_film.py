#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — workshop film build
==========================================

Assembles ``images/floor/workshop-film.mp4`` — a short, silent, looping film
from the photography already in ``images/``.

    python3 tools/build_film.py

Why a generated film instead of a hand-placed video?
  * the client's own site footage replaces it with one file drop (same path,
    same poster), so the section is never an empty player in the meantime;
  * it is silent and captioned in type, so it works muted, autoplays
    gracefully and adds no audio-accessibility burden;
  * it is deterministic: re-running rebuilds the same cut.

Requirements: Pillow (see tools/make_assets.py) and ffmpeg on PATH.
Any ffmpeg binary works — e.g. ``pip install imageio-ffmpeg`` and pass
``--ffmpeg <path>``.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_assets import INK_900, SILVER_400, cover_resize, font  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
OUT = IMG / "floor" / "workshop-film.mp4"

W, H = 1280, 800
FPS = 25

# (photo, kicker, title) — each becomes one slow push-in
SCENES = [
    ("workshop-precision.jpg", "01 · WORKSHOP", "Measured, cut and assembled in-house"),
    ("project-kitchen-profile.jpg", "02 · PROFILES", "Aluminium cabinetry, glazed shutters"),
    ("project-lekki-villa.jpg", "03 · WINDOWS", "Sliding and casement systems"),
    ("project-balustrade.jpg", "04 · GLASS RAILS", "Frameless balustrades, certified glass"),
    ("project-office-partition.jpg", "05 · PARTITIONS", "Shop and office divisions in glass"),
    ("project-shopfront.jpg", "06 · SHOPFRONTS", "Curtain wall, entrances and glazing"),
]


def ken_burns(src: Path, seconds: float, zoom_from=1.0, zoom_to=1.12) -> list[Image.Image]:
    """A slow push-in on a cover-cropped frame, with a graded scrim + caption."""
    base = cover_resize(Image.open(src).convert("RGB"), (W, H))
    frames = max(2, int(seconds * FPS))
    out = []
    for i in range(frames):
        t = i / (frames - 1)
        z = zoom_from + (zoom_to - zoom_from) * t
        w, h = int(W / z), int(H / z)
        left, top = (W - w) // 2, (H - h) // 2
        frame = base.crop((left, top, left + w, top + h)).resize((W, H), Image.LANCZOS)
        out.append(frame)
    return out


def overlay(frame: Image.Image, kicker: str, title: str, alpha: float) -> Image.Image:
    """Bottom-left type block over a soft scrim, fading with `alpha`."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Gradient scrim, concentrated in the lower-left where the type sits
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        t = max(0.0, (y - H * 0.28) / (H * 0.72))
        sd.line([(0, y), (W, y)], fill=int(235 * t ** 1.1))
    for x in range(W):
        t = max(0.0, (W * 0.62 - x) / (W * 0.62))
        sd.line([(x, H - 260), (x, H)], fill=int(90 * t), width=1)
    scrim = scrim.filter(ImageFilter.GaussianBlur(20))
    layer = Image.composite(Image.new("RGBA", (W, H), INK_900 + (alpha_int(),)), layer, scrim.point(lambda v: v))

    d = ImageDraw.Draw(layer)
    a = alpha_int(alpha)
    d.text((96, H - 176), kicker, font=font(sys.modules["make_assets"].FONT_MONO, 24),
           fill=(216, 217, 220, a))
    d.text((94, H - 132), title, font=font(sys.modules["make_assets"].FONT_BOLD, 40),
           fill=(255, 255, 255, a))
    d.rectangle([96, H - 200, 96 + 74, H - 196], fill=(232, 163, 61, a))

    # Brand watermark, top-right
    d.text((W - 386, 58), "OTEH MIROKO ALUMINUM", font=font(sys.modules["make_assets"].FONT_BOLD, 18),
           fill=(255, 255, 255, int(a * 0.75)))
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def alpha_int(x: float = 1.0) -> int:
    return max(0, min(255, int(255 * x)))


def fade(frames: list[Image.Image], n: int, fade_in=True) -> list[Image.Image]:
    """Wrap a scene with n frames of black so cuts breathe."""
    out = list(frames)
    if fade_in:
        for i in range(n):
            black = Image.new("RGB", (W, H), INK_900)
            out.insert(0, Image.blend(black, frames[0], (i + 1) / (n + 1)))
    for i in range(n):
        black = Image.new("RGB", (W, H), INK_900)
        out.append(Image.blend(frames[-1], black, (i + 1) / (n + 1)))
    return out


def build(ffmpeg: str) -> None:
    assert ffmpeg, "ffmpeg not found — pass --ffmpeg /path/to/ffmpeg"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        n = 0
        for idx, (photo, kicker, title) in enumerate(SCENES):
            src = IMG / photo
            if not src.exists():
                print(f"  ! missing {photo}, skipping")
                continue
            frames = ken_burns(src, seconds=3.2, zoom_from=1.0, zoom_to=1.12)
            frames = [overlay(f, kicker, title, 1.0) for f in frames]
            frames = fade(frames, 8, fade_in=idx == 0)
            for f in frames:
                f.save(tmp / f"{n:05d}.jpg", "JPEG", quality=88)
                n += 1

        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(tmp / "%05d.jpg"),
            "-vf", "format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", "26",
            "-movflags", "+faststart", "-an",
            str(OUT),
        ]
        subprocess.run(cmd, check=True)
    kb = OUT.stat().st_size / 1024
    print(f"  {OUT.relative_to(ROOT).as_posix():<40} {W}x{H}  {n} frames  {kb:6.1f} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "")
    args = ap.parse_args()
    print("Building workshop film")
    build(args.ffmpeg)
    print("Done.")
