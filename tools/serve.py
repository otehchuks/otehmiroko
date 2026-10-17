#!/usr/bin/env python3
"""
Oteh Miroko Aluminum — local preview server
===========================================

    python3 tools/serve.py            # http://localhost:8080
    python3 tools/serve.py --port 9000 --host 0.0.0.0

Why not `python3 -m http.server`?
  * **Range requests.** The standard handler answers every video request with
    a whole-file 200, so the workshop film cannot be scrubbed. This server
    replies `206 Partial Content`, which is what browsers ask for when you
    drag a video timeline.
  * **Branded 404.** Unknown paths serve `404.html`, exactly like Netlify /
    Vercel will in production, so the not-found page can be checked locally.
  * **Sane caching.** HTML is `no-store` (always fresh while editing), while
    images/CSS/JS get a short max-age so reloads are fast without going stale.
  * **Correct MIME types** for .mp4/.webm/.svg/.ico, which the stdlib guesses
    badly or not at all on some systems.

It is a preview tool only — the deployed site is still plain static files.
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import re
import sys
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/webm", ".webm")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/x-icon", ".ico")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("font/woff2", ".woff2")

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)$")


class PreviewHandler(SimpleHTTPRequestHandler):
    server_version = "OtehMirokoPreview/1.0"

    def end_headers(self) -> None:
        path = self.path.split("?")[0].lower()
        if path.endswith(("/", ".html")):
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "public, max-age=60")
        super().end_headers()

    # -- branded 404 ------------------------------------------------------
    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code == HTTPStatus.NOT_FOUND:
            page = ROOT / "404.html"
            if page.exists():
                body = page.read_bytes()
                self.send_response(HTTPStatus.NOT_FOUND, "Not Found")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)

    # -- Range support (video scrubbing) ----------------------------------
    def send_head(self):
        path = self.translate_path(self.path)
        rng = self.headers.get("Range")
        if not rng or os.path.isdir(path):
            return super().send_head()

        match = RANGE_RE.match(rng.strip())
        if not match:
            return super().send_head()

        try:
            size = os.path.getsize(path)
        except OSError:
            return super().send_head()

        start_s, end_s = match.groups()
        if start_s == "" and end_s == "":
            return super().send_head()
        if start_s == "":                     # suffix range: last N bytes
            length = min(int(end_s), size)
            start, end = size - length, size - 1
        else:
            start = int(start_s)
            end = min(int(end_s), size - 1) if end_s else size - 1
        if start >= size or start > end:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None

        f = open(path, "rb")
        f.seek(start)
        self._range_remaining = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self._range_remaining))
        self.end_headers()
        return f

    def copyfile(self, source, outputfile) -> None:
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)
        self._range_remaining = None

    # -- quieter logs -----------------------------------------------------
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="0.0.0.0",
                    help="0.0.0.0 so sandbox previews and phones on the LAN can reach it")
    args = ap.parse_args()

    handler = partial(PreviewHandler, directory=str(ROOT))
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"Oteh Miroko Aluminum — preview on http://localhost:{args.port}")
        print(f"serving {ROOT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
