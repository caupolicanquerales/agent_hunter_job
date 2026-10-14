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

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = int(os.getenv("SEARCH_DEFAULT_LIMIT", "20"))
MAX_PAGE_SIZE = int(os.getenv("SEARCH_MAX_LIMIT", "100"))


@dataclass(frozen=True)
class SearchRequest:
    """Immutable search parameters extracted from a GET or POST request."""

    query: str | None = None
    page: int | str | None = None
    page_size: int | str | None = None
    limit: int | str | None = None
    source: str | None = None


def handle_get_search(handler: BaseHTTPRequestHandler, path: str) -> None:
    params = parse_qs(urlparse(path).query)
    request = SearchRequest(
        query=_first(params, "query"),
        page=_first(params, "page"),
        page_size=_first(params, "page_size"),
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
        page=payload.get("page"),
        page_size=payload.get("page_size"),
        limit=payload.get("limit"),
        source=payload.get("source"),
    )
    perform_search(handler, request)


def perform_search(handler: BaseHTTPRequestHandler, request: SearchRequest) -> None:
    if not request.query or not str(request.query).strip():
        send_json(handler, 400, {"error": "query is required"})
        return
    try:
        resolved_page = coerce_page(request.page)
        resolved_page_size = coerce_page_size(request.page_size, request.limit)
    except ValueError as error:
        send_json(handler, 400, {"error": str(error)})
        return
    resolved_query = str(request.query).strip()
    resolved_source = str(request.source).strip() if request.source else None
    offset = (resolved_page - 1) * resolved_page_size
    try:
        payload = search_job_postings(
            resolved_query, resolved_page_size, resolved_source, offset
        )
    except Exception as error:  # noqa: BLE001 - surface MCP failures as 502
        send_json(handler, 502, {"error": f"MCP search failed: {error}"})
        return
    results = payload.get("results", [])
    total_results = payload.get("total_results", len(results))
    total_pages = _total_pages(total_results, resolved_page_size)
    send_json(
        handler,
        200,
        {
            "query": resolved_query,
            "source": resolved_source,
            "total_results": total_results,
            "page": resolved_page,
            "page_size": resolved_page_size,
            "total_pages": total_pages,
            "has_next_page": resolved_page < total_pages,
            "has_previous_page": resolved_page > 1,
            "results": results,
        },
    )


def coerce_page(raw_page: Any) -> int:
    if raw_page is None or raw_page == "":
        return DEFAULT_PAGE
    try:
        page = int(raw_page)
    except (TypeError, ValueError) as error:
        raise ValueError("page must be an integer") from error
    return max(1, page)


def coerce_page_size(raw_page_size: Any, raw_limit: Any = None) -> int:
    raw_value = raw_page_size if raw_page_size not in (None, "") else raw_limit
    if raw_value is None or raw_value == "":
        return DEFAULT_PAGE_SIZE
    try:
        page_size = int(raw_value)
    except (TypeError, ValueError) as error:
        raise ValueError("page_size must be an integer") from error
    return max(1, min(page_size, MAX_PAGE_SIZE))


def _total_pages(total_results: int, page_size: int) -> int:
    if total_results <= 0:
        return 0
    return (total_results + page_size - 1) // page_size


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