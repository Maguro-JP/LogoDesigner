"""LogoDesigner のローカルサーバー。

localhost (127.0.0.1:8767) 専用。現在のディレクトリを配信し、
POST /api/logo?format=svg で logo_core から SVG を返す。
"""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from logo_core import LogoError, build_svg, validate_spec

HOST = "127.0.0.1"
PORT = 8767
MAX_BODY = 256 * 1024  # 256KB

HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, format, *args):  # noqa: A002 - 標準のシグネチャ
        pass

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802 - http.server の規約
        parsed = urlparse(self.path)
        if parsed.path != "/api/logo":
            self._send_json(404, {"error": "not found"})
            return

        query = parse_qs(parsed.query)
        if query.get("format", [""])[0] != "svg":
            self._send_json(400, {"error": "format=svg が必要です"})
            return

        length = self.headers.get("Content-Length")
        if length is None:
            self._send_json(400, {"error": "Content-Length が必要です"})
            return
        try:
            size = int(length)
        except ValueError:
            self._send_json(400, {"error": "Content-Length が不正です"})
            return
        if size > MAX_BODY:
            self._send_json(413, {"error": "リクエストが大きすぎます（上限 256KB）"})
            return
        if size < 0:
            self._send_json(400, {"error": "Content-Length が不正です"})
            return

        raw = self.rfile.read(size)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            self._send_json(400, {"error": f"JSON が不正です: {exc}"})
            return

        try:
            spec = validate_spec(data)
            svg = build_svg(spec)
        except LogoError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        body = svg.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="logo.svg"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"LogoDesigner: http://{HOST}:{PORT}/", flush=True)
    print("終了するには Ctrl+C を押してください。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
