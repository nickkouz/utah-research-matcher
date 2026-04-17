from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from pipeline.orchestrator import run_pipeline_for_student


ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            path = "/frontend/index.html"
        elif path == "/form":
            path = "/frontend/form.html"
        elif path == "/results":
            path = "/frontend/results.html"

        file_path = (ROOT / path.lstrip("/")).resolve()
        if not str(file_path).startswith(str(ROOT)) or not file_path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/match":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            result = run_pipeline_for_student(payload)
        except Exception as exc:  # pragma: no cover - runtime protection for demo
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json(result, status=HTTPStatus.OK)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict, status: HTTPStatus) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Serving Utah Research Matcher at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
