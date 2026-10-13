#!/usr/bin/env python3
"""Handle the ``/api/jobs/search`` request for the backend server.

Reads and validates the query parameters (GET) or the JSON body (POST),
delegates to the MCP search tool and shapes the JSON response. The HTTP
handler in ``backend_server.py`` only routes to this module.
"""
import json
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

from handle_header import send_json
from load_mcp_client import search_job_postings

DEFAULT_LIMIT = int(os.getenv("SEARCH_DEFAULT_LIMIT", "20"))
MAX_LIMIT = int(os.getenv("SEARCH_MAX_LIMIT", "100"))


@dataclass(frozen=True)
class SearchRequest:
    """Immutable search parameters extracted from a GET or POST request."""

    query: str | None = None
    limit: int | str | None = None
    source: str | None = None


def handle_get_search(handler: BaseHTTPRequestHandler, path: str) -> None:
    params = parse_qs(urlparse(path).query)
    request = SearchRequest(
        query=_first(params, "query"),
        limit=_first(params, "limit"),
        source=_first(params, "source"),
    )
    perform_search(handler, request)


def handle_post_search(handler: BaseHTTPRequestHandler) -> None:
    try:
        payload = _read_json_body(handler)
    except ValueError as error:
        send_json(handler, 400, {"error": str(error)})
        return
    request = SearchRequest(
        query=payload.get("query"),
        limit=payload.get("limit"),
        source=payload.get("source"),
    )
    perform_search(handler, request)


def perform_search(handler: BaseHTTPRequestHandler, request: SearchRequest) -> None:
    if not request.query or not str(request.query).strip():
        send_json(handler, 400, {"error": "query is required"})
        return
    try:
        resolved_limit = coerce_limit(request.limit)
    except ValueError as error:
        send_json(handler, 400, {"error": str(error)})
        return
    resolved_query = str(request.query).strip()
    resolved_source = str(request.source).strip() if request.source else None
    try:
        payload = search_job_postings(
            resolved_query, resolved_limit, resolved_source
        )
    except Exception as error:  # noqa: BLE001 - surface MCP failures as 502
        send_json(handler, 502, {"error": f"MCP search failed: {error}"})
        return
    results = payload.get("results", [])
    send_json(
        handler,
        200,
        {
            "query": resolved_query,
            "source": resolved_source,
            "total_results": payload.get("total_results", len(results)),
            "results": results,
        },
    )


def coerce_limit(raw_limit: Any) -> int:
    if raw_limit is None or raw_limit == "":
        return DEFAULT_LIMIT
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as error:
        raise ValueError("limit must be an integer") from error
    return max(1, min(limit, MAX_LIMIT))


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw_body = handler.rfile.read(length)
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON body: {error}") from error
    if not isinstance(body, dict):
        raise ValueError("JSON body must be an object")
    return body


def _first(params: dict[str, list[str]], key: str) -> str | None:
    values = params.get(key)
    return values[0] if values else None