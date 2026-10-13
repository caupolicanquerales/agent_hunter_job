#!/usr/bin/env python3
"""Minimal synchronous MCP client over the SSE transport (stdlib only).

Lets host-side scripts call tools exposed by the FastMCP server without
installing the `mcp` Python package. See final_chunk_reporter.py.
"""
import http.client
import json
import os
import time
from urllib.parse import urlparse

# Protocol revision is pinned here; bump it together with the FastMCP server.
MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_TIMEOUT_SECONDS = float(os.getenv("MCP_TIMEOUT_SECONDS", "30"))


class McpConnectionError(RuntimeError):
    """Raised when the SSE stream drops, times out or the server is unreachable."""


class McpSseClient:
    """MCP client speaking JSON-RPC over the Server-Sent Events transport."""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __init__(self, url, timeout=MCP_TIMEOUT_SECONDS):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError(f"Invalid MCP server url: {url}")
        self._host = parsed.hostname
        self._port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._sse_path = parsed.path or "/sse"
        self._timeout = timeout
        self._sse_conn = None
        self._sse_resp = None
        self._post_conn = None
        self._message_path = None
        self._next_id = 0

    def connect(self):
        try:
            self._sse_conn = http.client.HTTPConnection(
                self._host, self._port, timeout=self._timeout
            )
            self._sse_conn.request(
                "GET", self._sse_path, headers={"Accept": "text/event-stream"}
            )
            self._sse_resp = self._sse_conn.getresponse()
        except (OSError, http.client.HTTPException) as error:
            raise McpConnectionError(f"Cannot reach MCP server: {error}") from error
        if self._sse_resp.status != 200:
            raise McpConnectionError(
                f"MCP SSE handshake failed with status {self._sse_resp.status}"
            )
        self._message_path = self._read_endpoint()
        self._post_conn = http.client.HTTPConnection(
            self._host, self._port, timeout=self._timeout
        )
        self._initialize()

    def close(self):
        for conn in (self._post_conn, self._sse_conn):
            try:
                if conn is not None:
                    conn.close()
            except OSError:
                pass

    def call_tool(self, name, arguments):
        response = self._request(
            "tools/call", {"name": name, "arguments": arguments}
        )
        if "error" in response:
            raise RuntimeError(str(response["error"]))
        return response["result"]

    def _initialize(self):
        response = self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "mcp-sse-client", "version": "1.0"},
            },
        )
        if "error" in response:
            raise RuntimeError(str(response["error"]))
        self._notify("notifications/initialized")

    def _request(self, method, params):
        self._next_id += 1
        request_id = self._next_id
        self._post(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        return self._wait_for_response(request_id)

    def _notify(self, method):
        self._post({"jsonrpc": "2.0", "method": method})

    def _post(self, message):
        body = json.dumps(message)
        try:
            self._post_conn.request(
                "POST",
                self._message_path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            response = self._post_conn.getresponse()
            response.read()
        except (OSError, http.client.HTTPException) as error:
            raise McpConnectionError(f"MCP message POST failed: {error}") from error
        if response.status not in (200, 202):
            raise McpConnectionError(
                f"MCP message POST failed with status {response.status}"
            )

    def _read_endpoint(self):
        for event_name, data in self._iter_sse_events():
            if event_name == "endpoint":
                parsed = urlparse(data.strip())
                if parsed.scheme:
                    path = parsed.path
                    return path + (f"?{parsed.query}" if parsed.query else "")
                return data.strip()
        raise RuntimeError("MCP server did not send an SSE endpoint event")

    def _wait_for_response(self, request_id):
        deadline = time.monotonic() + self._timeout
        for event_name, data in self._iter_sse_events():
            if event_name == "message":
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    message = None
                if isinstance(message, dict) and message.get("id") == request_id:
                    return message
            if time.monotonic() > deadline:
                raise McpConnectionError(
                    f"No response to request {request_id} within {self._timeout}s"
                )
        raise McpConnectionError("SSE stream ended before a response arrived")

    def _iter_sse_events(self):
        event_name = ""
        data_lines = []
        while True:
            try:
                raw_line = self._sse_resp.readline()
            except (OSError, http.client.HTTPException) as error:
                raise McpConnectionError(f"SSE stream failed: {error}") from error
            if not raw_line:
                raise McpConnectionError("SSE stream closed unexpectedly")
            line = raw_line.decode("utf-8").rstrip("\r\n")
            if line == "":
                if data_lines:
                    yield event_name or "message", "\n".join(data_lines)
                event_name = ""
                data_lines = []
                continue
            if line.startswith(":"):
                continue
            field, _, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if field == "event":
                event_name = value
            elif field == "data":
                data_lines.append(value)
