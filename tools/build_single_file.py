#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — single-file build
========================================

Bundles the homepage into ONE .html file: CSS inlined into a <style> block,
JavaScript inlined at the end of <body>, and homepage images swapped for base64
data URIs. Supporting Insights and legal pages remain separate static files, so
links to those pages require the full site folder to be deployed alongside it.

    python3 tools/build_single_file.py

Output: single-file.html at the project root.

Why this exists
---------------
- Sandboxed preview panes and email attachments can't resolve relative asset
  paths, so the multi-file site renders unstyled there. This build always
  renders, because it has no external dependencies at all.
- It's handy for an offline visual demo of the homepage; supporting-page links work
  when the adjacent `insights/`, `privacy.html` and `terms.html` files are present.

Trade-offs, deliberately accepted
---------------------------------
- Larger first load: base64 inflates bytes by ~33% and the browser cannot cache
  assets separately, so the multi-file version is always the one to deploy.
- The lightbox uses the 640w thumbnails rather than the 1200w originals, to keep
  this file to a sensible size. The deployed site uses the full-size images.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "index.html"
OUT = ROOT / "single-file.html"


# A standalone file is meant to be emailable/offline-demoable, so images are
# re-encoded leaner than the deployed originals. Set LEAN = False to embed the
# exact files the live site serves (roughly 3x larger output).
LEAN = True
LEAN_MAX_W = {"hero-facade.jpg": 960, "workshop-precision.jpg": 720}
LEAN_DEFAULT_W = 640
LEAN_QUALITY = 58
_LEAN_CACHE = ROOT / ".cache" / "single-file"


def lean_copy(path: Path) -> Path:
    """Return a compressed stand-in for `path`, generated once per run."""
    try:
        from PIL import Image
    except ImportError:                                  # pragma: no cover
        print("  ! Pillow not installed — embedding full-size images")
        return path

    _LEAN_CACHE.mkdir(parents=True, exist_ok=True)
    dest = _LEAN_CACHE / path.name
    if dest.exists() and dest.stat().st_mtime >= path.stat().st_mtime:
        return dest

    img = Image.open(path).convert("RGB")
    max_w = LEAN_MAX_W.get(path.name, LEAN_DEFAULT_W)
    if img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
    img.save(dest, "JPEG", quality=LEAN_QUALITY, optimize=True, progressive=True, subsampling=2)
    return dest


def data_uri(rel_path: str) -> str:
    """Read a project-relative image and return a base64 data URI."""
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(f"missing asset referenced by index.html: {rel_path}")
    if LEAN and path.suffix.lower() in {".jpg", ".jpeg"}:
        # The hero ships a dedicated 960w variant; prefer it over the 1920w file.
        light = ROOT / "images" / "hero-facade-960.jpg"
        if path.name == "hero-facade.jpg" and light.exists():
            path = light
        path = lean_copy(path)
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".svg": "image/svg+xml",
        ".webp": "image/webp", ".avif": "image/avif",
    }[path.suffix.lower()]
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def main() -> None:
    html = SRC_HTML.read_text(encoding="utf-8")
    inlined: list[str] = []

    # ---- 1. Inline the stylesheet -------------------------------------------
    css = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")
    css = css.replace("</style", "<\\/style")           # paranoia: never break out
    # NB: replacements go through a lambda so that backslashes inside the
    # inlined CSS/JS (regex and unicode escapes) are treated as literals —
    # a plain string replacement would make re.sub try to parse them.
    html, n = re.subn(
        r'<link rel="stylesheet" href="css/styles\.css">',
        lambda _m: '<style>\n' + css + '\n</style>',
        html,
    )
    assert n == 1, "stylesheet <link> not found — did index.html change?"
    inlined.append("css/styles.css")

    # ---- 2. Inline the script ----------------------------------------------
    js = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
    js = js.replace("</script", "<\\/script")
    html, n = re.subn(
        r'<script src="js/main\.js" defer></script>',
        lambda _m: '<script>\n' + js + '\n</script>',
        html,
    )
    assert n == 1, "script tag not found — did index.html change?"
    inlined.append("js/main.js")

    # ---- 3. Inline <img> images and drop srcset/sizes ------------------------
    def inline_img(match: re.Match) -> str:
        tag = match.group(0)
        src = re.search(r'\ssrc="([^"]+)"', tag)
        if not src:
            return tag
        uri = data_uri(src.group(1))
        tag = tag.replace(src.group(0), f' src="{uri}"')
        # A data URI has no intrinsic candidates left, so remove the offer
        tag = re.sub(r'\s+srcset="[^"]*"', "", tag)
        tag = re.sub(r'\s+sizes="[^"]*"', "", tag)
        inlined.append(src.group(1))
        return tag

    html = re.sub(r"<img\b[^>]*>", inline_img, html)

    # ---- 4. De-duplicate the lightbox targets -------------------------------
    # Each gallery <a> points at the full-size image, which the <img> next to it
    # already covers as a thumbnail. Embedding both would inline every project
    # photo twice, so the href is dropped: js/main.js falls back to the
    # thumbnail's own src, and role/tabindex keep the control keyboard-operable.
    def drop_href(match: re.Match) -> str:
        tag = match.group(0)
        tag = re.sub(r'href="images/project-[a-z-]+\.jpg"', 'role="button" tabindex="0"', tag)
        return tag

    html, n_links = re.subn(
        r'<a class="gallery__link" href="images/project-[a-z-]+\.jpg"[^>]*>',
        drop_href, html,
    )
    print(f"  lightbox links de-duplicated: {n_links}")

    # ---- 5. Inline the remaining direct references --------------------------
    for attr in ("apple-touch-icon",):
        html = re.sub(
            rf'(<link rel="{attr}" href=")([^"]+)(")',
            lambda m: m.group(1) + data_uri(m.group(2)) + m.group(3),
            html,
        )

    # ---- 6. Note the build in the source, and write --------------------------
    html = html.replace(
        "<!DOCTYPE html>",
        "<!DOCTYPE html>\n<!--\n"
        "  Oteh Miroko Aluminum — GENERATED SINGLE-FILE HOMEPAGE\n"
        "  Homepage CSS, JavaScript and images are inlined as data URIs.\n"
        "  Insights and legal pages remain separate; publish the full site folder\n"
        "  alongside this file for those routes to work.\n"
        "  Generated by tools/build_single_file.py — edit source files, not this one.\n"
        "  Deploy the multi-file version for caching and full-resolution images.\n-->",
        1,
    )

    OUT.write_text(html, encoding="utf-8")

    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}  ({size_kb:,.0f} KB)")
    print(f"inlined {len(inlined)} assets "
          f"({len(set(inlined))} unique): {', '.join(sorted(set(inlined)))}")


if __name__ == "__main__":
    main()
