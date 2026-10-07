#!/usr/bin/env python3
"""Reads a chunk_*.json candidate file from the reports/ folder and returns the parsed object for the agent."""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OPENCODE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
PROJECT_DIR = os.path.dirname(OPENCODE_DIR)
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")

CHUNK_PREFIX = "chunk_"
CHUNK_SUFFIX = ".json"


def resolve_chunk_path(file_name):
    """Resolve a bare chunk file name against the pre-established reports/ root."""
    if not file_name or not file_name.strip():
        raise ValueError("File name is required, example: chunk_01.json")
    safe_name = os.path.basename(file_name.strip())
    if not (safe_name.startswith(CHUNK_PREFIX) and safe_name.endswith(CHUNK_SUFFIX)):
        raise ValueError(f"Expected a name like chunk_01.json, got: {file_name}")
    chunk_path = os.path.join(REPORTS_DIR, safe_name)
    if not os.path.isfile(chunk_path):
        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")
    return chunk_path


def read_chunk(file_name):
    """Return the parsed chunk object: {chunk, candidate_count, candidates}."""
    chunk_path = resolve_chunk_path(file_name)
    with open(chunk_path, "r", encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {chunk_path}: {error}") from error

    if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
        raise ValueError(f"Invalid chunk structure in {chunk_path}: expected an object with a 'candidates' list")
    if payload.get("candidate_count") != len(payload["candidates"]):
        raise ValueError(
            f"candidate_count ({payload.get('candidate_count')}) does not match "
            f"{len(payload['candidates'])} candidates in {chunk_path}"
        )
    return payload


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 reader_chunk_opportunities.py chunk_01.json", file=sys.stderr)
        sys.exit(2)
    try:
        chunk = read_chunk(sys.argv[1])
    except (ValueError, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    json.dump(chunk, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
