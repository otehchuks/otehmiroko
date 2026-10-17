#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — brand asset build
========================================

Writes every logo/icon file the site references, from the one vector source of
truth in ``tools/logo_path.py``:

    python3 tools/build_brand_assets.py

Outputs (all deterministic — re-running produces byte-identical files):

    images/logo.svg              the mark, charcoal, transparent ground
    images/favicon.svg           same, but flips to white in dark browser UI
    images/favicon.ico           16 + 32 + 48 px, for older browsers/bookmarks
    images/logo.png              512 px transparent — JSON-LD + Apple/OG fallback
    images/apple-touch-icon.png  180 px, white mark on the brand ink ground
                                 (iOS ignores transparency, so it gets a ground)

It also synchronises the pages themselves, so the inline header mark and the
icon <link> tags can never drift away from the vector source:

    index.html, 404.html, insights/*.html, privacy.html, terms.html
        <span class="brand__mark">  -> regenerated from logo_path.RING
        <link rel="icon">           -> favicon.ico + favicon.svg + apple-touch
        <meta name="theme-color">   -> the brand ink

Existing content between those anchors is replaced, never appended, so the
script is idempotent: running it twice changes nothing the second time.

The palettes here mirror ``css/styles.css`` section 01.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logo_path import INK, SILVER, render, svg_document, svg_path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)

# Brand ink / silver, matching the design tokens
INK_800 = (19, 19, 21)
SILVER_100 = (245, 246, 247)
INK_800_HEX = "#131315"

PAGES = [
    "index.html", "404.html", "privacy.html", "terms.html",
    "insights/index.html", "insights/glass-specification.html",
    "insights/window-maintenance.html", "insights/window-cost-factors.html",
]


def inline_mark(indent: str, height: int = 42) -> str:
    """The header lock-up mark: currentColor so it inherits the text colour."""
    width = round(height * 92.5 / 116, 1)
    return (
        f"{indent}<!-- Brand mark — generated from tools/logo_path.py; "
        f"run tools/build_brand_assets.py to refresh -->\n"
        f'{indent}<span class="brand__mark" aria-hidden="true">\n'
        f'{indent}  <svg viewBox="0 0 92.5 116" width="{width:g}" height="{height}" '
        f'role="img" focusable="false">\n'
        f'{indent}    <path fill="currentColor" fill-rule="evenodd" d="{svg_path()}"/>\n'
        f"{indent}  </svg>\n"
        f"{indent}</span>\n"
    )


def sync_pages() -> list[tuple[str, str]]:
    """Rewrite the brand mark, icon links and theme colour in every page."""
    done: list[tuple[str, str]] = []
    for rel in PAGES:
        path = ROOT / rel
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        before = html
        depth = "../" if rel.startswith("insights/") else ""

        # 1. Header brand mark -------------------------------------------------
        #    Strip every previous version first (generated blocks *and* the
        #    hand-drawn placeholder mark), so the result never depends on what
        #    was there before.
        html = re.sub(
            r"[ \t]*<!-- (?:Brand mark|Inline SVG logo)[^\n]*-->\n[ \t]*<span class=\"brand__mark\".*?</span>\n",
            "", html, flags=re.S)
        html = re.sub(r"[ \t]*<span class=\"brand__mark\".*?</span>\n", "", html, flags=re.S)

        anchor = re.search(r'^([ \t]*)<a class="brand"[^>]*>\n', html, re.M)
        if anchor:
            mark = inline_mark(anchor.group(1) + "  ")
            html = html[:anchor.end()] + mark + html[anchor.end():]

        # 1b. Footer mark (only pages with a full footer brand block) --------
        footer = re.search(r'<div class="footer__brand">\n', html)
        if footer:
            indent = re.search(r'^([ \t]*)\S', html[footer.end():], re.M).group(1)
            foot_mark = (
                f"{indent}<!-- Brand mark — generated from tools/logo_path.py -->\n"
                f'{indent}<svg class="footer__mark" viewBox="0 0 92.5 116" width="30" height="38" '
                f'role="img" aria-hidden="true"><path fill="currentColor" fill-rule="evenodd" '
                f'd="{svg_path()}"/></svg>\n'
            )
            existing = re.search(
                r'[ \t]*<!-- Brand mark[^\n]*-->\n[ \t]*<svg class="footer__mark".*?</svg>\n',
                html, re.S)
            if existing:
                html = html[:existing.start()] + foot_mark + html[existing.end():]
            else:
                html = html[:footer.end()] + foot_mark + html[footer.end():]

        # 2. Icon links --------------------------------------------------------
        icon_block = (
            "<!-- Icons — generated by tools/build_brand_assets.py -->\n"
            f'<link rel="icon" href="{depth}images/favicon.ico" sizes="any">\n'
            f'<link rel="icon" href="{depth}images/favicon.svg" type="image/svg+xml">\n'
            f'<link rel="apple-touch-icon" href="{depth}images/apple-touch-icon.png">'
        )
        # Drop any old favicon comment, then replace the whole run of icon links
        html = re.sub(r"[ \t]*<!-- (?:Favicon|Icons)[^\n]*?-->\n", "", html)
        html, n_icons = re.subn(
            r'(?:[ \t]*<link rel="(?:icon|apple-touch-icon)"[^>]*>\n?)+',
            icon_block + "\n", html, count=1)
        if not n_icons:  # page had no icon links at all — place them after <title>
            html = re.sub(r"(<title>[^<]*</title>\n)", r"\1" + icon_block.replace("\\", "\\") + "\n",
                          html, count=1)

        # 3. theme-color -------------------------------------------------------
        html = re.sub(r'(<meta name="theme-color" content=")[^"]*(">)',
                      rf'\g<1>{INK_800_HEX}\g<2>', html)

        if html != before:
            path.write_text(html, encoding="utf-8")
            done.append((rel, "brand mark + icons"))
    return done


def main() -> None:
    written: list[tuple[str, str]] = []

    svg = IMG / "logo.svg"
    svg.write_text(svg_document("#131315"), encoding="utf-8")
    written.append(("images/logo.svg", "vector, charcoal"))

    fav_svg = IMG / "favicon.svg"
    fav_svg.write_text(svg_document("#131315", with_dark_mode=True), encoding="utf-8")
    written.append(("images/favicon.svg", "vector, light/dark aware"))

    logo_png = IMG / "logo.png"
    render(512, fg=INK_800, pad=0.06).save(logo_png, "PNG", optimize=True)
    written.append(("images/logo.png", "512x512, transparent"))

    touch = IMG / "apple-touch-icon.png"
    render(180, fg=SILVER_100, bg=INK_800, pad=0.14).save(touch, "PNG", optimize=True)
    written.append(("images/apple-touch-icon.png", "180x180, ink ground"))

    ico = IMG / "favicon.ico"
    render(64, fg=INK_800, pad=0.05).save(
        ico, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(("images/favicon.ico", "16/32/48"))

    width = max(len(name) for name, _ in written)
    for name, note in written:
        print(f"  {name.ljust(width)}  {note}")

    print("\nSynchronising pages")
    pages = sync_pages()
    if pages:
        for name, note in pages:
            print(f"  {name.ljust(width)}  {note}")
    else:
        print("  (already up to date)")


if __name__ == "__main__":
    print("Building brand marks from tools/logo_path.py")
    main()
    print("Done.")
