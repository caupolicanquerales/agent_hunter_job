#!/usr/bin/env python3
"""Prefilters reports/job_opportunities.js by FILTER_KEYWORDS and writes candidate chunks of 5."""
import ast
import glob
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OPENCODE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
PROJECT_DIR = os.path.dirname(OPENCODE_DIR)
FILTERS_PATH = os.path.join(BASE_DIR, "constants", "filters.js")
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
REPORT_PATH = os.path.join(REPORTS_DIR, "job_opportunities.js")

CHUNK_SIZE = 5
SEPARATORS = str.maketrans("-._/", "    ")


def load_filter_keywords(path):
    """Load the FILTER_KEYWORDS array from the filters.js constants file."""
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    match = re.search(r"export\s+const\s+FILTER_KEYWORDS\s*=\s*(\[[\s\S]*?\])", content)
    if not match:
        raise ValueError(f"Could not parse FILTER_KEYWORDS from {path}")
    keywords = ast.literal_eval(re.sub(r",\s*\]", "]", match.group(1)))
    if not isinstance(keywords, list) or not all(isinstance(kw, str) for kw in keywords):
        raise ValueError(f"FILTER_KEYWORDS must be a list of strings in {path}")
    return keywords


def load_job_opportunities(path):
    """Load the JOB_OPPORTUNITIES object exported by reports/job_opportunities.js."""
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    payload = content.split("=", 1)[1].strip()
    if payload.endswith(";"):
        payload = payload[:-1]
    return json.loads(payload)


def normalize_text(text):
    """Lowercase and map separators to spaces so keyword variants match by containment."""
    lowered = (text or "").lower()
    spaced = " ".join(lowered.translate(SEPARATORS).split())
    return spaced, spaced.replace(" ", "")


def build_keyword_variants(keyword):
    """Return the spaced and compact forms of a keyword for variant matching."""
    return normalize_text(keyword)


def find_matching_keywords(description, keyword_variants_by_keyword):
    desc_spaced, desc_compact = normalize_text(description)
    return [
        keyword
        for keyword, (kw_spaced, kw_compact) in keyword_variants_by_keyword
        if kw_spaced in desc_spaced or kw_compact in desc_compact
    ]


def build_chunks(items, size):
    return [items[index:index + size] for index in range(0, len(items), size)]


def write_chunks(chunks, reports_dir):
    for stale_path in glob.glob(os.path.join(reports_dir, "chunk_*.json")):
        os.remove(stale_path)

    width = max(2, len(str(len(chunks))))
    written_files = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = os.path.join(reports_dir, f"chunk_{index:0{width}d}.json")
        payload = {
            "chunk": index,
            "candidate_count": len(chunk),
            "candidates": chunk,
        }
        with open(chunk_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        written_files.append(chunk_path)
    return written_files


def main():
    keywords = load_filter_keywords(FILTERS_PATH)
    jobs_by_portal = load_job_opportunities(REPORT_PATH)
    keyword_variants_by_keyword = [(kw, build_keyword_variants(kw)) for kw in keywords]

    candidates = []
    total_jobs = 0
    for jobs in jobs_by_portal.values():
        total_jobs += len(jobs)
        for job in jobs:
            matched = find_matching_keywords(job.get("description"), keyword_variants_by_keyword)
            if matched:
                candidates.append({**job, "matched_keywords": matched})

    chunks = build_chunks(candidates, CHUNK_SIZE)
    written_files = write_chunks(chunks, REPORTS_DIR)

    print(f"Prefilter: {total_jobs} jobs scanned against {len(keywords)} keywords")
    print(f"Candidates matched: {len(candidates)}")
    print(f"Chunk files written to {REPORTS_DIR}")
    print(f"Chunk files to process: {len(written_files)}")
    file_names = [os.path.basename(path) for path in written_files]
    print(f"Chunk file names: {', '.join(file_names) if file_names else '(none)'}")


if __name__ == "__main__":
    main()
