from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from pipeline.orchestrator import run_pipeline_for_student


class handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        try:
            result = run_pipeline_for_student(payload)
        except Exception as exc:  # pragma: no cover - runtime protection for deployment
            self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json(result, status=200)

    def do_GET(self) -> None:
        self._send_json({"error": "Method not allowed"}, status=405)

    def _send_json(self, payload: dict, status: int) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
