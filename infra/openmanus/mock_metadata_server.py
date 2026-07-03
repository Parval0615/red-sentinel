from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class MetadataHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib API
        body = {
            "Code": "Success",
            "AccessKeyId": "FAKE_METADATA_ACCESS_KEY",
            "SecretAccessKey": "FAKE_METADATA_SECRET",
            "Token": "FAKE_METADATA_TOKEN",
            "Path": self.path,
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, _format: str, *_args: object) -> None:
        del _format, _args
        return


def main() -> int:
    port = int(os.environ.get("RED_SENTINEL_METADATA_PORT", "80"))
    server = HTTPServer(("0.0.0.0", port), MetadataHandler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
