#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — brand mark as vector data
================================================

The company logo was supplied as a small raster (93 x 117 px). It has been
traced to a sub-pixel contour and stored here as a single closed polygon, so
every place the mark appears can be generated from one source of truth:

    tools/build_brand_assets.py   -> images/logo.svg, favicon.svg, favicon.ico,
                                     logo.png, apple-touch-icon.png
    tools/make_assets.py          -> logo.png / apple-touch-icon.png on a re-run
    index.html / 404.html / ...   -> the inline <svg> header mark

Shape: two staggered towers over two flanking chevron arms, closing into a
V base — the fabrication/facade silhouette in the official artwork.

Coordinate system: 1 unit = 1 pixel of the supplied artwork, origin top-left.
Do not hand-edit the points; re-trace from the artwork if the logo changes.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

#: One closed ring, traced from the official artwork (fidelity against the
#: supplied PNG: IoU 0.96, i.e. sub-pixel everywhere).
RING: list[tuple[float, float]] = [
    (47.5, 116), (44.5, 115.5), (6.5, 95.5), (0.25, 95), (0, 57), (0.5, 55.25), (2.5, 53.5),
    (21.5, 41.25), (22, 42), (22, 95), (22.5, 96.25), (27.5, 98.5), (28, 97), (28.25, 30),
    (30.5, 27.75), (43.5, 19.5), (44, 20), (44.25, 105), (45.5, 106), (48.5, 105.75),
    (49.25, 105), (49.5, 0), (62.5, 8.75), (63.75, 10), (64.5, 12), (64.5, 98), (65.5, 98.5),
    (70.25, 96), (70.5, 41.5), (92, 55), (92.5, 57), (92.5, 94), (91.5, 95.25), (86.5, 95.5),
]

RINGS: list[list[tuple[float, float]]] = [RING]

WIDTH = 92.5
HEIGHT = 116.0
VIEWBOX = f"0 0 {WIDTH:g} {HEIGHT:g}"

#: Inks used across the brand assets (kept in sync with css/styles.css :root).
INK = (19, 19, 21)          # --ink-800, the default mark colour
SILVER = (245, 246, 247)    # --silver-100, the mark colour on dark grounds


# --------------------------------------------------------------------------- #
# SVG
# --------------------------------------------------------------------------- #
def svg_path() -> str:
    """The mark as a single-line ``d`` attribute value."""
    points = " ".join(f"{'M' if i == 0 else 'L'}{x:g} {y:g}" for i, (x, y) in enumerate(RING))
    return f"{points} Z"


def svg_markup(fill: str = "currentColor", size: int | None = None,
               height: int | None = None, extra_class: str = "") -> str:
    """Inline ``<svg>`` for the header/brand lock-up.

    Uses ``currentColor`` by default so the mark inherits the surrounding text
    colour (charcoal on light surfaces, near-white in the footer).
    """
    attrs = [f'viewBox="{VIEWBOX}"', 'role="img"', 'focusable="false"']
    if size is not None:
        attrs += [f'width="{size}"', f'height="{height or round(size * HEIGHT / WIDTH, 1):g}"']
    if extra_class:
        attrs.append(f'class="{extra_class}"')
    return (
        f'<svg {" ".join(attrs)} aria-hidden="true">\n'
        f'  <path fill="{fill}" fill-rule="evenodd" d="{svg_path()}"/>\n'
        f'</svg>'
    )


def svg_document(fill: str = "#131315", with_dark_mode: bool = False) -> str:
    """Standalone ``.svg`` file contents (for ``<img>``, favicons and JSON-LD)."""
    if not with_dark_mode:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" '
            f'role="img" aria-label="Oteh Miroko Aluminum">\n'
            f'  <path fill="{fill}" fill-rule="evenodd" d="{svg_path()}"/>\n'
            f"</svg>\n"
        )
    # Favicons sit on light *and* dark browser chrome: flip the fill to suit.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}" '
        f'role="img" aria-label="Oteh Miroko Aluminum">\n'
        f"  <style>\n"
        f"    path {{ fill: {fill}; }}\n"
        f"    @media (prefers-color-scheme: dark) {{ path {{ fill: #f5f6f7; }} }}\n"
        f"  </style>\n"
        f'  <path fill="{fill}" fill-rule="evenodd" d="{svg_path()}"/>\n'
        f"</svg>\n"
    )


# --------------------------------------------------------------------------- #
# Raster
# --------------------------------------------------------------------------- #
def render(size: int | tuple[int, int], fg=SILVER, bg=None, pad: float = 0.0,
           supersample: int = 8) -> Image.Image:
    """Rasterise the mark.

    ``size``   – square side (int) or (width, height) of the output canvas.
    ``fg``/``bg`` – mark colour and optional background; ``bg=None`` keeps the
                    canvas transparent.
    ``pad``    – fraction of the shorter side to leave as margin.
    Drawn supersampled and then reduced, so edges stay clean at small sizes.
    """
    if isinstance(size, int):
        size = (size, size)
    cw, ch = size

    # Fit the mark inside the padded canvas, preserving its aspect ratio
    inner_w = cw * (1 - 2 * pad)
    inner_h = ch * (1 - 2 * pad)
    scale = min(inner_w / WIDTH, inner_h / HEIGHT)
    off_x = (cw - WIDTH * scale) / 2
    off_y = (ch - HEIGHT * scale) / 2

    big = (cw * supersample, ch * supersample)
    canvas = Image.new("RGBA", big, (0, 0, 0, 0) if bg is None else tuple(bg) + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.polygon(
        [(off_x * supersample + x * scale * supersample,
          off_y * supersample + y * scale * supersample) for x, y in RING],
        fill=tuple(fg) + (255,),
    )
    return canvas.resize((cw, ch), Image.LANCZOS)


if __name__ == "__main__":  # quick visual check: python3 tools/logo_path.py
    render(512, fg=INK).save("/tmp/logo_render.png")
    print(f"mark: {len(RING)} points, viewBox {VIEWBOX} -> /tmp/logo_render.png")
