#!/usr/bin/env python3
"""Persist one chunk's job-evaluator report and ingest it into pgvector.

The evaluation JSON is read from an explicit file argument (never stdin, which
parallel evaluators share), written to ``results/<chunk>_evaluation.json``
atomically, then upserted through the MCP ``store_job_postings`` tool. Database
ingestion is serialized across processes and retried, so parallel reporters
neither saturate the connection pool nor deadlock on row locks.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import IO, Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms have no flock
    fcntl = None

SCRIPT_DIR = Path(__file__).resolve().parent
OPENCODE_DIR = SCRIPT_DIR.parents[2]
PROJECT_DIR = OPENCODE_DIR.parent
RESULTS_DIR = PROJECT_DIR / "results"

MCP_CLIENT_DIR = PROJECT_DIR / "server" / "mcp-server"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:3000/sse")
MCP_TOOL_NAME = "store_job_postings"

INGESTION_LOCK_FILE = RESULTS_DIR / ".reporter.lock"
INGESTION_LOCK_TIMEOUT_SECONDS = float(
    os.getenv("REPORTER_DB_LOCK_TIMEOUT_SECONDS", "180")
)
INGESTION_RETRIES = max(1, int(os.getenv("REPORTER_DB_RETRIES", "3")))
INGESTION_RETRY_BASE_SECONDS = 0.5
INGESTION_RETRY_MAX_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.25

USAGE = """\
Usage: python3 final_chunk_reporter.py <chunk_file_name> <report_json_file>
  <chunk_file_name>   e.g. chunk_01.json
  <report_json_file>  file holding the evaluation JSON array (never stdin:
                      parallel evaluators share standard input)"""


class ReporterError(RuntimeError):
    """User-facing failure: invalid input, missing report file or write error."""


def evaluation_path(chunk_file_name: str) -> Path:
    """Map ``chunk_01.json`` to ``results/chunk_01_evaluation.json``."""
    if not chunk_file_name or not chunk_file_name.strip():
        raise ReporterError("File name is required, example: chunk_01.json")
    name = Path(chunk_file_name.strip()).name
    if Path(name).suffix != ".json":
        raise ReporterError(f"Expected a .json file name, got: {chunk_file_name}")
    return RESULTS_DIR / f"{Path(name).stem}_evaluation.json"


def parse_evaluation(payload: str) -> list[dict[str, Any]]:
    """Parse and validate the agent report: a non-empty JSON array of jobs."""
    try:
        evaluation = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ReporterError(f"Invalid evaluation JSON: {error}") from error
    if not isinstance(evaluation, list) or not evaluation:
        raise ReporterError("Evaluation must be a non-empty JSON array of jobs")
    for position, item in enumerate(evaluation, start=1):
        if not isinstance(item, dict) or "score" not in item or "recommendation" not in item:
            raise ReporterError(
                f"Item {position} must be an object with 'score' and 'recommendation'"
            )
    return evaluation


def read_report(report_path: str) -> tuple[Path, list[dict[str, Any]]]:
    """Read and validate the explicit report file; return its path and content."""
    if not report_path or not report_path.strip():
        raise ReporterError("Report JSON file path is required")
    path = Path(report_path.strip()).expanduser()
    if not path.is_file():
        raise ReporterError(f"Report file not found: {path}")
    payload = _read_text(path)
    if not payload.strip():
        raise ReporterError(f"Report file is empty: {path}")
    return path, parse_evaluation(payload)


def save_evaluation(chunk_file_name: str, evaluation: list[dict[str, Any]]) -> Path:
    """Atomically write the evaluation to ``results/<chunk>_evaluation.json``."""
    path = evaluation_path(chunk_file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(path, evaluation)
    return path


def remove_report_file(path: Path) -> None:
    """Best-effort cleanup of the per-chunk report file once it is persisted."""
    with contextlib.suppress(OSError):
        path.unlink()


def load_mcp_client() -> ModuleType:
    """Import ``server/mcp-server/mcp_sse_client.py`` as a regular module."""
    client_dir = str(MCP_CLIENT_DIR)
    if client_dir not in sys.path:
        sys.path.insert(0, client_dir)
    import mcp_sse_client  # noqa: PLC0415 - sys.path is prepared just above

    return mcp_sse_client


def store_in_database(evaluation: list[dict[str, Any]]) -> dict[str, Any]:
    """Ingest evaluations under a cross-process lock with bounded retries."""
    last_error: Exception | None = None
    for attempt in range(1, INGESTION_RETRIES + 1):
        try:
            with _ingestion_lock():
                return _store_once(evaluation)
        except TimeoutError:
            raise
        except Exception as error:  # noqa: BLE001 - retried, then degraded to a warning
            last_error = error
            if attempt < INGESTION_RETRIES:
                _sleep_backoff(attempt)
    assert last_error is not None  # the loop runs at least once
    raise last_error


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        print(USAGE, file=sys.stderr)
        return 2

    chunk_file_name, report_arg = arguments
    try:
        report_path, evaluation = read_report(report_arg)
        evaluation_file = save_evaluation(chunk_file_name, evaluation)
    except (ReporterError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Evaluation saved: {evaluation_file} ({len(evaluation)} jobs evaluated)")
    remove_report_file(report_path)
    _report_database_store(evaluation)
    return 0


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ReporterError(f"Cannot read report file {path}: {error}") from error


def _atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically: temp file in the same dir, fsync, then os.replace."""
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)
        raise
    _fsync_directory(path.parent)


def _fsync_directory(directory: Path) -> None:
    with contextlib.suppress(OSError):
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


@contextlib.contextmanager
def _ingestion_lock() -> Iterator[None]:
    """Serialize database ingestion across parallel reporter processes."""
    if fcntl is None:
        yield
        return
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with INGESTION_LOCK_FILE.open("a+", encoding="utf-8") as handle:
        _acquire_lock(handle)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _acquire_lock(handle: IO[str]) -> None:
    deadline = time.monotonic() + INGESTION_LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    "Could not acquire the ingestion lock within "
                    f"{INGESTION_LOCK_TIMEOUT_SECONDS}s"
                ) from None
            time.sleep(LOCK_POLL_SECONDS)


def _sleep_backoff(attempt: int) -> None:
    delay = min(INGESTION_RETRY_BASE_SECONDS * 2 ** (attempt - 1), INGESTION_RETRY_MAX_SECONDS)
    time.sleep(delay)


def _store_once(evaluation: list[dict[str, Any]]) -> dict[str, Any]:
    """Send the evaluations to the MCP tool once and return its parsed payload."""
    mcp_client = load_mcp_client()
    client = mcp_client.McpSseClient(MCP_SERVER_URL)
    try:
        client.connect()
        result = client.call_tool(MCP_TOOL_NAME, {"postings": evaluation})
    finally:
        client.close()
    if isinstance(result, dict) and result.get("isError"):
        raise RuntimeError(_extract_tool_text(result) or "MCP tool reported an error")
    text = _extract_tool_text(result)
    return json.loads(text) if text else {}


def _extract_tool_text(result: Any) -> str:
    blocks = result.get("content") if isinstance(result, dict) else None
    return "\n".join(
        block.get("text", "")
        for block in blocks or []
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()


def _report_database_store(evaluation: list[dict[str, Any]]) -> None:
    """Best-effort ingestion: never fail the run once the file is persisted."""
    try:
        result = store_in_database(evaluation)
    except Exception as error:  # noqa: BLE001 - DB sync must not break the file step
        print(
            "Warning: evaluations saved to file but not stored in the database: "
            f"{error}",
            file=sys.stderr,
        )
        return
    print(
        f"Database store: {result.get('new_jobs_stored', 0)} new, "
        f"{result.get('jobs_updated', 0)} updated"
    )


if __name__ == "__main__":
    sys.exit(main())
