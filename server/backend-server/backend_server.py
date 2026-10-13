#!/usr/bin/env python3
"""HTTP controller that exposes job search to the Angular frontend.

MCP access lives in ``load_mcp_client``, header management in
``handle_header`` and search handling in ``handle_search``; this file only
routes requests. Stdlib only: no extra dependencies.
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from handle_header import send_json, send_options_response
from handle_search import handle_get_search, handle_post_search
from load_mcp_client import MCP_SERVER_URL

BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "3100"))

HEALTH_PATH = "/health"
SEARCH_PATH = "/api/jobs/search"


class JobSearchHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "JobSearchBackend/1.0"

    def do_OPTIONS(self) -> None:
        send_options_response(self)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == HEALTH_PATH:
            send_json(self, 200, {"status": "ok"})
            return
        if path == SEARCH_PATH:
            handle_get_search(self, self.path)
            return
        send_json(self, 404, {"error": "not found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != SEARCH_PATH:
            send_json(self, 404, {"error": "not found"})
            return
        handle_post_search(self)


def main() -> None:
    httpd = ThreadingHTTPServer((BACKEND_HOST, BACKEND_PORT), JobSearchHandler)
    print(
        f"backend-server listening on http://{BACKEND_HOST}:{BACKEND_PORT} "
        f"(MCP: {MCP_SERVER_URL})"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()