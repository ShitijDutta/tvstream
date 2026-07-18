#!/usr/bin/env python3
"""Tiny local HTTP server that tunes the TV box: GET /tune/<channel-number>.

The fauxmo virtual devices call this when Alexa hears "turn on <channel>".
Runs on 127.0.0.1 only — nothing is exposed beyond this machine.
"""

import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import tuner

CONFIG = json.loads((pathlib.Path(__file__).parent / "bridge_config.json").read_text(encoding="utf-8"))
_lock = threading.Lock()  # one tuning sequence at a time


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parts = self.path.strip("/").split("/")
        if parts == ["noop"]:
            return self._reply(200, "ok")
        if len(parts) == 2 and parts[0] == "tune" and parts[1].isdigit():
            try:
                with _lock:
                    tuner.tune(parts[1])
                return self._reply(200, f"tuned {parts[1]}")
            except Exception as exc:
                return self._reply(500, f"error: {exc}")
        return self._reply(404, "unknown path; use /tune/<number>")

    def _reply(self, code, text):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    port = CONFIG["tuner_port"]
    print(f"tuner server listening on http://127.0.0.1:{port} "
          f"(box {CONFIG['box_ip']})")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
