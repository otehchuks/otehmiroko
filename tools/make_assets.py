#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — image asset pipeline
===========================================

Reproducible build for everything in /images. Run it whenever you replace the
placeholder photography so the site keeps its optimised, responsive sizes:

    python3 tools/make_assets.py

What it does
------------
1. Re-encodes the supplied photography to web weights and generates the
   responsive variants the HTML references via srcset:
       images/hero-facade.jpg          1920w  (desktop hero)
       images/hero-facade-960.jpg       960w  (phone hero)
       images/project-*.jpg            1200w  (lightbox)
       images/thumbs/project-*.jpg      640w  (grid thumbnails)
2. Renders the remaining slots as on-brand "technical drawing" placeholder
   tiles so the layout is complete before the client supplies real photography.
   Each tile is drawn as a CAD-style sheet: blueprint ground, line art,
   dimension lines and a REPLACE label.
3. Produces social/favicon assets: og-cover.jpg, apple-touch-icon.png, logo.png.

Everything is deterministic (seeded RNG) so re-running produces identical files.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Brand geometry lives in one place so raster icons match the inline SVG mark
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo_path import render  # noqa: E402

# --------------------------------------------------------------------------- #
# Paths & brand constants (kept in sync with css/styles.css :root)
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
THUMBS = IMG / "thumbs"
THUMBS.mkdir(parents=True, exist_ok=True)

INK_900 = (5, 5, 6)         # --ink-900: charcoal, darkest
INK_800 = (19, 19, 21)      # --ink-800: primary dark surface
INK_700 = (38, 38, 43)      # --ink-700: raised dark surface
INK_500 = (77, 77, 85)      # --ink-500: accent / brand mark
INK_300 = (154, 154, 163)   # --ink-300: accents on dark grounds
SILVER_100 = (245, 246, 247)
SILVER_200 = (232, 233, 236)
SILVER_300 = (217, 218, 222)
SILVER_400 = (195, 197, 203)
SILVER_900 = (92, 95, 102)
WHITE = (255, 255, 255)
WATER = (214, 216, 219)
PARK = (223, 228, 221)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_REG = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"



# --------------------------------------------------------------------------- #
# Small drawing helpers
# --------------------------------------------------------------------------- #
def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def tracked_text(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, tracking=0):
    """Draw text with letter-spacing (PIL has no native tracking)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def grid_overlay(base: Image.Image, step: int = 48, alpha: int = 14):
    """Blueprint grid: fine lines both ways, drawn on an alpha layer."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = base.size
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(255, 255, 255, alpha), width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(255, 255, 255, alpha), width=1)
    base.alpha_composite(layer)


def blueprint_ground(size: tuple[int, int], top=INK_800, bottom=INK_700) -> Image.Image:
    """Vertical gradient ground + grid + vignette — the CAD sheet look."""
    w, h = size
    grad = Image.new("RGB", (1, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        gd.point((0, y), fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    base = grad.resize((w, h)).convert("RGBA")
    grid_overlay(base, step=max(28, w // 26), alpha=13)

    # Soft radial highlight in the upper-left, as if lit from a workshop window
    glow = Image.new("L", (w, h), 0)
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([-w * 0.25, -h * 0.45, w * 0.75, h * 0.65], fill=54)
    glow = glow.filter(ImageFilter.GaussianBlur(w // 8))
    base.alpha_composite(Image.merge("RGBA", (
        Image.new("L", (w, h), 120), Image.new("L", (w, h), 170),
        Image.new("L", (w, h), 210), glow)))
    return base


def dimension_line(draw, x1, y1, x2, y2, colour, tick=14, width=1, vertical_ticks=True):
    """Architectural dimension line: main line, end ticks, small arrow heads."""
    draw.line([(x1, y1), (x2, y2)], fill=colour, width=width)
    if vertical_ticks:
        for (x, y) in ((x1, y1), (x2, y2)):
            draw.line([(x, y - tick / 2), (x, y + tick / 2)], fill=colour, width=width)
    else:
        for (x, y) in ((x1, y1), (x2, y2)):
            draw.line([(x - tick / 2, y), (x + tick / 2, y)], fill=colour, width=width)


def label_block(img: Image.Image, title: str, kicker: str, *, dark=True, align="left"):
    """Sheet-style caption strip across the bottom of a placeholder tile."""
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    strip_h = int(h * 0.20)
    y0 = h - strip_h

    d.rectangle([0, y0, w, h], fill=(5, 5, 6, 214))
    d.line([(0, y0), (w, y0)], fill=(77, 77, 85, 255), width=max(2, h // 320))

    f_kick = font(FONT_BOLD, max(13, int(h * 0.024)))
    f_title = font(FONT_BOLD, max(20, int(h * 0.045)))
    f_mono = font(FONT_MONO, max(11, int(h * 0.020)))

    pad = int(w * 0.045)
    kicker_colour = INK_300
    title_colour = WHITE
    meta_colour = SILVER_400

    tracked_text(d, (pad, y0 + strip_h * 0.20), kicker.upper(), f_kick, kicker_colour, tracking=2)
    d.text((pad, y0 + strip_h * 0.44), title, font=f_title, fill=title_colour)

    meta = "PLACEHOLDER — REPLACE WITH SITE PHOTOGRAPHY"
    mw = d.textlength(meta, font=f_mono)
    d.text((w - pad - mw, y0 + strip_h * 0.72), meta, font=f_mono, fill=meta_colour)

    # Corner registration ticks, classic drawing-sheet detail
    t = 26
    for (cx, cy, dx, dy) in ((pad, pad, 1, 1), (w - pad, pad, -1, 1),
                             (pad, y0 - int(h * 0.03), 1, -1), (w - pad, y0 - int(h * 0.03), -1, -1)):
        d.line([(cx, cy), (cx + dx * t, cy)], fill=(154, 154, 163, 150), width=2)
        d.line([(cx, cy), (cx, cy + dy * t)], fill=(154, 154, 163, 150), width=2)
    return img


# --------------------------------------------------------------------------- #
# Placeholder sheets
# --------------------------------------------------------------------------- #
def tile_casement_with_netting() -> Image.Image:
    """A casement window elevation with insect mesh — for the netting project."""
    W, H = 1200, 900
    base = blueprint_ground((W, H))
    d = ImageDraw.Draw(base, "RGBA")
    line = (245, 246, 247, 235)

    # Frame
    fx0, fy0, fx1, fy1 = int(W * 0.24), int(H * 0.16), int(W * 0.76), int(H * 0.60)
    lw = 7
    d.rectangle([fx0, fy0, fx1, fy1], outline=line, width=lw)
    d.rectangle([fx0 + lw, fy0 + lw, fx1 - lw, fy1 - lw], outline=(154, 154, 163, 150), width=2)

    # Two sashes: centre mullion
    mx = (fx0 + fx1) // 2
    d.line([(mx, fy0), (mx, fy1)], fill=line, width=lw)
    for x in (fx0 + (mx - fx0) // 2, mx + (mx - fx0) // 2):
        d.line([(x, fy0 + 8), (x, fy1 - 8)], fill=(211, 213, 217, 150), width=3)

    # Insect mesh: cross-hatch confined to the left sash
    mesh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mesh)
    step = 13
    for i in range(-1200, 1200, step):
        md.line([(fx0 + 10 + i, fy0 + 10), (fx0 + 10 + i + 700, fy1 - 10)], fill=(154, 154, 163, 70), width=1)
        md.line([(fx0 + 10 + i, fy1 - 10), (fx0 + 10 + i + 700, fy0 + 10)], fill=(154, 154, 163, 70), width=1)
    base.alpha_composite(mesh.crop((0, 0, W, H)))

    # Swing arcs, as on a shop drawing
    r = (mx - fx0) - 18
    d.arc([fx0 + 8, fy0 + 8, fx0 + 8 + 2 * r, fy0 + 8 + 2 * r], start=270, end=360,
          fill=(77, 77, 85, 220), width=3)
    d.arc([fx1 - 8 - 2 * r, fy0 + 8, fx1 - 8, fy0 + 8 + 2 * r], start=180, end=270,
          fill=(77, 77, 85, 220), width=3)

    # Dimension line under the frame
    dimension_line(d, fx0, fy1 + 70, fx1, fy1 + 70, (195, 197, 203, 235), tick=16, width=2)
    f = font(FONT_MONO, 22)
    d.text(((fx0 + fx1) / 2 - 46, fy1 + 44), "1800 mm", font=f, fill=(217, 218, 222, 240))

    label_block(base, "Insect netting, Magodo bungalow", "Elevation · 1:20")
    return base.convert("RGB")


def tile_glass_samples() -> Image.Image:
    """Three glass sample squares with different hatch fills (blog: glass types)."""
    W, H = 800, 560
    base = blueprint_ground((W, H))
    d = ImageDraw.Draw(base, "RGBA")

    cards = [("6 mm clear", "none"), ("10 mm tinted", "dots"), ("13.5 laminated", "double")]
    cw, ch = 168, 300
    gap = 34
    total = len(cards) * cw + (len(cards) - 1) * gap
    x0 = (W - total) // 2
    y0 = 116

    for i, (name, fill) in enumerate(cards):
        x = x0 + i * (cw + gap)
        # Glass pane
        d.rectangle([x, y0, x + cw, y0 + ch], fill=(255, 255, 255, 26), outline=(245, 246, 247, 235), width=5)
        d.polygon([(x + 4, y0 + ch - 4), (x + 4, y0 + 4), (x + 62, y0 + 4),
                   (x + cw - 4, y0 + ch - 62), (x + cw - 4, y0 + ch - 4)],
                  fill=(255, 255, 255, 20))  # reflection wedge

        if fill == "dots":
            for yy in range(y0 + 14, y0 + ch - 10, 16):
                for xx in range(x + 14, x + cw - 10, 16):
                    d.ellipse([xx, yy, xx + 3, yy + 3], fill=(154, 154, 163, 120))
        elif fill == "double":
            d.line([(x + 4, y0 + 4), (x + cw - 4, y0 + 4)], fill=(77, 77, 85, 255), width=4)
            d.line([(x + 4, y0 + ch - 4), (x + cw - 4, y0 + ch - 4)], fill=(77, 77, 85, 255), width=4)
            d.line([(x + cw // 2, y0 + 4), (x + cw // 2, y0 + ch - 4)],
                   fill=(154, 154, 163, 90), width=2)

        f = font(FONT_BOLD, 19)
        tw = d.textlength(name, font=f)
        d.text((x + (cw - tw) / 2, y0 + ch + 22), name, font=f, fill=(217, 218, 222, 240))

    label_block(base, "Glass sample board", "Specification · 6–13.5 mm", align="left")
    return base.convert("RGB")


def tile_slider_detail() -> Image.Image:
    """Slider track / roller detail with a callout — for the maintenance post."""
    W, H = 800, 560
    base = blueprint_ground((W, H))
    d = ImageDraw.Draw(base, "RGBA")
    line = (245, 246, 247, 235)

    # Two sashes in section, bottom track under them
    d.rectangle([120, 150, 400, 360], outline=line, width=6)
    d.rectangle([360, 185, 640, 395], outline=(211, 213, 217, 220), width=6)
    d.line([(90, 396), (710, 396)], fill=line, width=10)
    d.line([(90, 418), (710, 418)], fill=(154, 154, 163, 150), width=4)

    # Roller detail, magnified circle
    cx, cy, r = 500, 380, 96
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(77, 77, 85, 235), width=4)
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(154, 154, 163, 170))
    d.arc([cx - 34, cy - 34, cx + 34, cy + 34], start=0, end=300, fill=(245, 246, 247, 230), width=5)
    d.line([(cx - r - 6, cy - r + 26), (cx - 22, cy - 22)], fill=(77, 77, 85, 200), width=2)
    d.line([(cx + r + 6, cy - r + 26), (cx + 22, cy - 22)], fill=(77, 77, 85, 200), width=2)

    dimension_line(d, 120, 460, 400, 460, (195, 197, 203, 235), tick=14, width=2)
    dimension_line(d, 90, 118, 710, 118, (195, 197, 203, 235), tick=14, width=2, vertical_ticks=False)
    f = font(FONT_MONO, 20)
    d.text((236, 434), "SASH", font=f, fill=(217, 218, 222, 235))
    d.text((322, 92), "TRACK LENGTH", font=f, fill=(217, 218, 222, 235))

    label_block(base, "Slider track & roller detail", "Detail · 1:5")
    return base.convert("RGB")


def tile_cost_factors() -> Image.Image:
    """Elevation + dimension lines + a small cost-driver bar chart."""
    W, H = 800, 560
    base = blueprint_ground((W, H))
    d = ImageDraw.Draw(base, "RGBA")
    line = (245, 246, 247, 235)

    # Window elevation
    fx0, fy0, fx1, fy1 = 96, 120, 400, 396
    d.rectangle([fx0, fy0, fx1, fy1], outline=line, width=6)
    d.line([(fx0, (fy0 + fy1) // 2), (fx1, (fy0 + fy1) // 2)], fill=line, width=5)
    d.line([((fx0 + fx1) // 2, fy0), ((fx0 + fx1) // 2, fy1)], fill=(211, 213, 217, 200), width=4)

    dimension_line(d, fx0, fy1 + 54, fx1, fy1 + 54, (195, 197, 203, 230), tick=14, width=2)
    dimension_line(d, fx0 - 54, fy0, fx0 - 54, fy1, (195, 197, 203, 230), tick=14, width=2, vertical_ticks=False)

    # Bar chart: the five cost levers
    bars = [("PROFILE", 0.92), ("GLAZING", 0.72), ("FINISH", 0.55), ("QTY", 0.38), ("ACCESS", 0.24)]
    bx, by, bw = 470, 396, 210
    f = font(FONT_MONO, 16)
    for i, (name, val) in enumerate(bars):
        y = by - i * 46
        d.rectangle([bx, y - 16, bx + bw, y - 2], fill=(255, 255, 255, 22))
        d.rectangle([bx, y - 16, bx + int(bw * val), y - 2], fill=(77, 77, 85, 220))
        d.text((bx, y - 40), name, font=f, fill=(195, 197, 203, 235))

    label_block(base, "What drives the cost", "Cost study · notes")
    return base.convert("RGB")


def tile_street_map() -> Image.Image:
    """Monochrome street-map poster for the contact section (no third-party tiles).

    Drawn in the brand greys: grey blocks, white roads with grey casings, a
    water band and one charcoal pin. Roads are painted *over* the block ground,
    which is what makes it read as a street grid rather than wallpaper.
    """
    W, H = 1200, 800
    rnd = random.Random(11)

    BLOCK = (230, 231, 235)
    BLOCK_DARK = (221, 222, 227)
    ROAD = (255, 255, 255)
    CASING = (205, 207, 212)
    WATER = (220, 225, 232)
    PARK = (226, 231, 224)
    INK = (19, 19, 21)

    img = Image.new("RGB", (W, H), BLOCK)
    d = ImageDraw.Draw(img, "RGBA")

    # Building footprints inside the blocks — small tonal variation only
    for _ in range(260):
        x, y = rnd.randrange(0, W), rnd.randrange(0, H)
        w, h = rnd.randrange(18, 64), rnd.randrange(18, 64)
        d.rectangle([x, y, x + w, y + h], fill=BLOCK_DARK + (255,))

    # Water channel sweeping across the lower third, then parks
    d.line([(0, 655), (260, 612), (520, 646), (780, 578), (1040, 606), (1200, 570)],
           fill=WATER + (255,), width=96, joint="curve")
    for _ in range(10):
        x, y = rnd.randrange(0, W - 130), rnd.randrange(0, H - 130)
        d.rounded_rectangle([x, y, x + rnd.randrange(70, 150), y + rnd.randrange(70, 130)],
                            radius=10, fill=PARK + (255,))

    # Street grid: casings first, then the white road surface on top
    def street(points, width):
        d.line(points, fill=CASING + (255,), width=width + 4, joint="curve")
        d.line(points, fill=ROAD + (255,), width=width, joint="curve")

    for x in range(34, W, 118):
        street([(x, 0), (x, H)], 14)
    for y in range(52, H, 104):
        street([(0, y), (W, y)], 12)
    for x in range(-40, W, 236):
        street([(x, 0), (x + 96, H)], 18)
    street([(0, 300), (W, 208)], 22)

    # Faint graticule so it reads as a map, not wallpaper
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=INK + (6,), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=INK + (6,), width=1)

    # Cross-hair through the pin, halo, then the pin itself
    px, py = 690, 330
    d.line([(px, 0), (px, H)], fill=INK + (30,), width=2)
    d.line([(0, py), (W, py)], fill=INK + (30,), width=2)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([px - 92, py - 92, px + 92, py + 92], fill=INK + (24,))
    img = Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([px - 19, py - 19, px + 19, py + 19], fill=INK)
    d.polygon([(px - 15, py + 12), (px + 15, py + 12), (px, py + 44)], fill=INK)
    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(245, 246, 247))

    return img


def save_jpeg(img: Image.Image, path: Path, quality: int, sharpen=True, box=None, blur=0.0):
    """Optionally cover-crop to `box`, sharpen for downscale, then encode.

    4:2:0 chroma subsampling + progressive + optimize keeps payloads small;
    a light unsharp mask restores the micro-contrast lost when downscaling.
    """
    img = img.convert("RGB")
    if box:
        img = cover_resize(img, box)
    if blur:
        # Deliberate pre-blur on the hero only: the CSS scrim sits at 72–92%
        # opacity, so softening high-frequency detail is invisible on screen but
        # roughly halves the payload of a detail-dense facade shot.
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=58, threshold=4))
    img.save(path, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=2)
    kb = path.stat().st_size / 1024
    print(f"  {path.relative_to(ROOT).as_posix():<48} {img.width}x{img.height}  {kb:7.1f} KB")


def cover_resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale to fill `size` then centre-crop (CSS object-fit: cover, baked in)."""
    tw, th = size
    scale = max(tw / img.width, th / img.height)
    resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))),
                         Image.LANCZOS)
    left = (resized.width - tw) // 2
    top = (resized.height - th) // 2
    return resized.crop((left, top, left + tw, top + th))


HERO = "hero-facade.jpg"
GALLERY = [
    "project-lekki-villa.jpg",
    "project-office-partition.jpg",
    "project-shopfront.jpg",
    "project-balustrade.jpg",
    "project-factory-glazing.jpg",
    "project-kitchen-profile.jpg",
    "project-hospital-glazing.jpg",
    "project-warehouse-doors.jpg",
]


def optimise_photos():
    print("\n[1/3] Optimising supplied photography")

    hero = Image.open(IMG / HERO)
    save_jpeg(hero, IMG / HERO, quality=70, box=(1920, 1280), blur=1.4)
    save_jpeg(hero, IMG / "hero-facade-960.jpg", quality=70, box=(960, 640), blur=0.8)

    # Social card (OpenGraph wants 1200x630) — branded, not a photo crop
    save_jpeg(social_card(), IMG / "og-cover.jpg", quality=82, sharpen=False)

    workshop = Image.open(IMG / "workshop-precision.jpg")
    save_jpeg(workshop, IMG / "workshop-precision.jpg", quality=78, box=(900, 1125))

    for name in GALLERY:
        src = Image.open(IMG / name)
        save_jpeg(src, IMG / name, quality=78, box=(1200, 900))      # lightbox size
        save_jpeg(src, THUMBS / name, quality=76, box=(640, 480))    # grid size


# --------------------------------------------------------------------------- #
# Brand marks
# --------------------------------------------------------------------------- #
def brand_marks():
    print("\n[2/3] Building brand marks")
    # One vector source of truth (tools/logo_path.py) so the raster icons match
    # the inline SVG mark in the pages exactly. tools/build_brand_assets.py
    # writes the same files plus logo.svg / favicon.svg / favicon.ico.
    def mark(size: int) -> Image.Image:
        """White mark on the brand ink ground — used for iOS home screens."""
        return render(size, fg=SILVER_100, bg=INK_800, pad=0.14).convert("RGB")

    mark(180).save(IMG / "apple-touch-icon.png", "PNG", optimize=True)
    print(f"  images/apple-touch-icon.png                              180x180")
    render(512, fg=INK_800, pad=0.06).save(IMG / "logo.png", "PNG", optimize=True)
    print(f"  images/logo.png                                          512x512")


def social_card() -> Image.Image:
    """Branded Open Graph card: the mark + wordmark on the ink ground.

    A stock façade photo says nothing about the company at link-preview size;
    the mark and wordmark are instantly recognisable in a WhatsApp or LinkedIn
    share card, and it stays on-brand with no photo licensing questions.
    """
    W, H = 1200, 630
    base = Image.new("RGBA", (W, H), INK_900 + (255,))

    # Soft light from the top-left, so the flat ink ground has depth
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-W * 0.3, -H * 0.7, W * 0.85, H * 0.9], fill=38)
    glow = glow.filter(ImageFilter.GaussianBlur(W // 7))
    base.alpha_composite(Image.merge("RGBA", (
        Image.new("L", (W, H), 150), Image.new("L", (W, H), 150),
        Image.new("L", (W, H), 158), glow)))
    grid_overlay(base, step=56, alpha=8)

    d = ImageDraw.Draw(base, "RGBA")
    pad = 110

    # The mark, drawn from the same vector data as the site header
    mark = render(int(H * 0.60), fg=SILVER_100, pad=0.0)
    base.alpha_composite(mark, (pad, (H - mark.height) // 2 - 6))

    # Wordmark: shrink the type until the line fits the space left of the edge
    x = pad + mark.width + 76
    avail = W - pad - x
    size = 84
    while size > 40:
        f = font(FONT_BOLD, size)
        if d.textlength("OTEH MIROKO", font=f) + 11 * 1.5 <= avail:
            break
        size -= 2

    tracked_text(d, (x, 236 - size // 2), "OTEH MIROKO", font(FONT_BOLD, size),
                 WHITE, tracking=1.5)
    tracked_text(d, (x + 3, 236 + size // 2 + 16), "ALUMINUM",
                 font(FONT_BOLD, 32), INK_300, tracking=12)
    rule_y = 236 + size // 2 + 84
    d.line([(x + 3, rule_y), (x + 3 + 380, rule_y)], fill=INK_300 + (140,), width=2)
    tracked_text(d, (x + 3, rule_y + 26), "WINDOWS · DOORS · GLASS",
                 font(FONT_MONO, 20), SILVER_400, tracking=3)

    # Footer rule and location line
    d.line([(pad, H - 92), (W - pad, H - 92)], fill=(255, 255, 255, 28), width=2)
    tracked_text(d, (pad, H - 66), "13 BERNARD OROGWU STREET · ABAKALIKI · EBONYI STATE",
                 font(FONT_MONO, 18), SILVER_400, tracking=1.5)

    # Registration corner tick — the same drawing-sheet detail as the tiles
    d.line([(60, 60), (104, 60)], fill=INK_300 + (120,), width=3)
    d.line([(60, 60), (60, 104)], fill=INK_300 + (120,), width=3)
    return base.convert("RGB")


def placeholders():
    print("\n[3/3] Rendering technical-drawing placeholders")
    tiles = {
        "project-netting.jpg": tile_casement_with_netting,
        "blog-glass-types.jpg": tile_glass_samples,
        "blog-maintenance.jpg": tile_slider_detail,
        "blog-cost-factors.jpg": tile_cost_factors,
        "map-poster.jpg": tile_street_map,
    }
    for name, builder in tiles.items():
        img = builder()
        full = (1200, 900) if name.startswith("project-") else \
               (1080, 720) if name == "map-poster.jpg" else (800, 560)
        save_jpeg(img, IMG / name, quality=80, sharpen=False, box=full)
        if name.startswith("project-"):
            save_jpeg(img, THUMBS / name, quality=76, sharpen=False, box=(640, 480))


if __name__ == "__main__":
    optimise_photos()
    brand_marks()
    placeholders()
    total = sum(f.stat().st_size for f in IMG.rglob("*.jpg")) / 1024
    print(f"\nDone. Total JPG payload in /images: {total:.0f} KB")
