#!/usr/bin/env python3
"""Manage HTTP response headers for the backend handler.

Owns the CORS policy and the response-header boilerplate (JSON responses
and preflight OPTIONS). ``backend_server.py`` only decides status codes,
routes and payloads.
"""
import json
import os
from http.server import BaseHTTPRequestHandler
from typing import Any

CORS_ALLOW_ORIGIN_HEADER = "Access-Control-Allow-Origin"

_ALLOWED_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4200,http://127.0.0.1:4200",
    ).split(",")
    if origin.strip()
]

_CORS_COMMON_HEADERS = (
    ("Vary", "Origin"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "Content-Type, Accept"),
    ("Access-Control-Max-Age", "86400"),
)


def _resolve_cors_origin(handler: BaseHTTPRequestHandler) -> str | None:
    if "*" in _ALLOWED_CORS_ORIGINS:
        return "*"
    origin = handler.headers.get("Origin")
    return origin if origin and origin in _ALLOWED_CORS_ORIGINS else None


def _send_cors_headers(handler: BaseHTTPRequestHandler) -> None:
    for name, value in _CORS_COMMON_HEADERS:
        handler.send_header(name, value)
    allowed_origin = _resolve_cors_origin(handler)
    if allowed_origin:
        handler.send_header(CORS_ALLOW_ORIGIN_HEADER, allowed_origin)


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    _send_cors_headers(handler)
    handler.end_headers()
    handler.wfile.write(body)


def send_options_response(handler: BaseHTTPRequestHandler) -> None:
    handler.send_response(204)
    handler.send_header("Content-Length", "0")
    _send_cors_headers(handler)
    handler.end_headers()