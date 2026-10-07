#!/usr/bin/env python3
"""Save the job-evaluator JSON report for one chunk into results/<chunk>_evaluation.json."""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OPENCODE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
PROJECT_DIR = os.path.dirname(OPENCODE_DIR)
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")


def resolve_evaluation_path(file_name):
    """Map the chunk file name (chunk_01.json) to results/chunk_01_evaluation.json."""
    if not file_name or not file_name.strip():
        raise ValueError("File name is required, example: chunk_01.json")
    safe_name = os.path.basename(file_name.strip())
    if not safe_name.endswith(".json"):
        raise ValueError(f"Expected a .json file name, got: {file_name}")
    stem = safe_name[:-len(".json")]
    return os.path.join(RESULTS_DIR, f"{stem}_evaluation.json")


def parse_evaluation(payload):
    """Parse and validate the agent report: a JSON array of evaluated jobs."""
    try:
        evaluation = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid evaluation JSON: {error}") from error
    if not isinstance(evaluation, list) or not evaluation:
        raise ValueError("Evaluation must be a non-empty JSON array of jobs")
    for position, item in enumerate(evaluation, start=1):
        if not isinstance(item, dict) or "score" not in item or "recommendation" not in item:
            raise ValueError(f"Item {position} must be an object with 'score' and 'recommendation'")
    return evaluation


def save_evaluation(file_name, payload):
    evaluation = parse_evaluation(payload)
    evaluation_path = resolve_evaluation_path(file_name)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(evaluation_path, "w", encoding="utf-8") as handle:
        json.dump(evaluation, handle, indent=2, ensure_ascii=False)
    return evaluation_path, len(evaluation)


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 final_chunk_reporter.py chunk_01.json '<evaluation json>' (or pipe the JSON on stdin)", file=sys.stderr)
        sys.exit(2)
    payload = sys.argv[2] if len(sys.argv) == 3 else sys.stdin.read()
    if not payload.strip():
        print("Error: no evaluation JSON received (argument or stdin)", file=sys.stderr)
        sys.exit(1)
    try:
        evaluation_path, job_count = save_evaluation(sys.argv[1], payload)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"Evaluation saved: {evaluation_path} ({job_count} jobs evaluated)")


if __name__ == "__main__":
    main()
