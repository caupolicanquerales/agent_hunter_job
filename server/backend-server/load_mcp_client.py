#!/usr/bin/env python3
"""Locate the shared MCP SSE client and call the job-search tool.

This module owns every MCP concern for the backend: discovering and
importing ``mcp_sse_client.py``, opening the SSE session and parsing the
tool payload. ``backend_server.py`` never touches MCP directly.
"""
import json
import os
import sys
from types import ModuleType
from typing import Any

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:3000/sse")
MCP_TOOL_NAME = "search_job_postings"

_MCP_CLIENT_FILE = "mcp_sse_client.py"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_MCP_CLIENT_DIR_CANDIDATES = [
    os.getenv("MCP_CLIENT_DIR", ""),
    _SCRIPT_DIR,
    os.path.join(_SCRIPT_DIR, "mcp-server"),
    os.path.join(_SCRIPT_DIR, "..", "mcp-server"),
]

_mcp_client_module: ModuleType | None = None


def _find_client_dir() -> str | None:
    for candidate in _MCP_CLIENT_DIR_CANDIDATES:
        if candidate and os.path.isfile(os.path.join(candidate, _MCP_CLIENT_FILE)):
            return os.path.abspath(candidate)
    return None


def load_mcp_client() -> ModuleType:
    """Import the shared ``mcp_sse_client.py`` module and return it."""
    global _mcp_client_module
    if _mcp_client_module is not None:
        return _mcp_client_module
    client_dir = _find_client_dir()
    if client_dir is None:
        raise RuntimeError(
            "mcp_sse_client.py not found; set MCP_CLIENT_DIR to its folder"
        )
    if client_dir not in sys.path:
        sys.path.insert(0, client_dir)
    import mcp_sse_client  # noqa: PLC0415 - import after sys.path setup

    _mcp_client_module = mcp_sse_client
    return _mcp_client_module


def _extract_tool_text(result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    texts = []
    for block in result.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            texts.append(str(block.get("text", "")))
    return "\n".join(texts).strip()


def search_job_postings(query: str, limit: int, source: str | None) -> dict[str, Any]:
    """Call the MCP search tool over SSE and return its parsed JSON payload."""
    client = load_mcp_client().McpSseClient(MCP_SERVER_URL)
    try:
        client.connect()
        result = client.call_tool(
            MCP_TOOL_NAME, {"query": query, "limit": limit, "source": source}
        )
    finally:
        client.close()
    if isinstance(result, dict) and result.get("isError"):
        raise RuntimeError(_extract_tool_text(result) or "MCP search failed")
    text = _extract_tool_text(result)
    return json.loads(text) if text else {}