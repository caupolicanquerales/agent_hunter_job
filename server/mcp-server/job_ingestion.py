import asyncio
import hashlib
import json
import re
from typing import Any

import asyncpg
from apify_client import ApifyClient
from sentence_transformers import SentenceTransformer

from config import (
    APIFY_TOKEN,
    APIFY_WAIT_DURATION,
    DATABASE_URL,
    DEFAULT_ACTOR_IDS,
    EMBEDDING_MODEL_NAME,
    FALLBACK_KEYWORDS,
    MAX_ACTOR_IDS,
    MAX_SKILL_KEYWORDS,
)

apify_client = ApifyClient(APIFY_TOKEN)

print(f"Loading local vector embedding model '{EMBEDDING_MODEL_NAME}'...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

_db_pool: asyncpg.Pool | None = None
_db_pool_lock = asyncio.Lock()

UPSERT_QUERY = """
    INSERT INTO scraped_job_postings
        (external_job_id, source_portal, title, company, location, is_remote,
         clean_description, required_skills, raw_payload, embedding)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector)
    ON CONFLICT (external_job_id, source_portal)
    DO UPDATE SET
        title = EXCLUDED.title,
        company = EXCLUDED.company,
        location = EXCLUDED.location,
        is_remote = EXCLUDED.is_remote,
        clean_description = EXCLUDED.clean_description,
        required_skills = EXCLUDED.required_skills,
        raw_payload = EXCLUDED.raw_payload,
        embedding = EXCLUDED.embedding,
        scraped_at = CURRENT_TIMESTAMP
    RETURNING (xmax = 0) AS is_insert;
"""


async def get_db_pool() -> asyncpg.Pool:
    global _db_pool
    if _db_pool is None:
        async with _db_pool_lock:
            if _db_pool is None:
                _db_pool = await asyncpg.create_pool(
                    DATABASE_URL, min_size=1, max_size=5
                )
    return _db_pool


async def close_db_pool() -> None:
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None


def sanitize_text(text: str) -> str:
    clean = re.sub(r"<[^>]*>?", "", text)
    return re.sub(r"\s+", " ", clean).strip()


def normalize_skill_keywords(skills: list[str] | None) -> list[str]:
    """
    Validate the keywords passed by the caller: strip blanks, drop duplicates
    (case-insensitive) and cap the size. Falls back to FALLBACK_KEYWORDS when
    the caller omits the parameter entirely.
    """
    if skills is None:
        return list(FALLBACK_KEYWORDS)

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_keyword in skills:
        keyword = raw_keyword.strip()
        if not keyword:
            continue
        dedupe_key = keyword.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(keyword)

    if not normalized:
        raise ValueError("skills must contain at least one non-empty keyword")
    if len(normalized) > MAX_SKILL_KEYWORDS:
        raise ValueError(
            f"skills accepts at most {MAX_SKILL_KEYWORDS} keywords, got {len(normalized)}"
        )
    return normalized


def normalize_actor_ids(actor_ids: dict[str, str] | None) -> dict[str, str]:
    """
    Validate the portal -> Apify actor id map passed by the caller: trim keys and
    values, reject blank entries and cap the size. Falls back to
    DEFAULT_ACTOR_IDS when the caller omits the parameter entirely.
    """
    if actor_ids is None:
        return dict(DEFAULT_ACTOR_IDS)
    if not actor_ids:
        raise ValueError("actor_ids must not be empty when provided")

    normalized: dict[str, str] = {}
    for raw_portal, raw_actor_id in actor_ids.items():
        portal_name = str(raw_portal).strip().lower()
        apify_actor_id = str(raw_actor_id).strip()
        if not portal_name or not apify_actor_id:
            raise ValueError(
                "actor_ids entries must have a non-empty portal name and actor id"
            )
        normalized[portal_name] = apify_actor_id

    if len(normalized) > MAX_ACTOR_IDS:
        raise ValueError(
            f"actor_ids accepts at most {MAX_ACTOR_IDS} entries, got {len(normalized)}"
        )
    return normalized


def extract_skills_by_regex(text: str, skill_keywords: list[str]) -> list[str]:
    return [
        keyword
        for keyword in skill_keywords
        if re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(keyword)}(?![A-Za-z0-9_])",
            text,
            re.I,
        )
    ]


def encode_texts(texts: list[str]) -> list[list[float]]:
    return embedder.encode(texts, show_progress_bar=False).tolist()


def prepare_jobs(
    raw_jobs: list[dict[str, Any]], skill_keywords: list[str]
) -> list[dict[str, Any]]:
    prepared_jobs = []
    for job in raw_jobs:
        clean_description = sanitize_text(job["description"])
        skills = extract_skills_by_regex(clean_description, skill_keywords)
        embedding_text = (
            f"Title: {job['title']} | Skills: {', '.join(skills)} "
            f"| Description: {clean_description}"
        )
        prepared_jobs.append(
            {
                "job": job,
                "clean_description": clean_description,
                "skills": skills,
                "embedding_text": embedding_text,
            }
        )
    return prepared_jobs


def build_external_job_id(item: dict[str, Any]) -> str:
    source = item.get("id") or item.get("jobId") or item.get("url")
    if not source:
        source = "|".join(
            str(item.get(key, ""))
            for key in ("title", "companyName", "company", "location")
        )
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()


def normalize_apify_item(
    item: dict[str, Any], fallback_location: str
) -> dict[str, Any]:
    item_location = item.get("location") or fallback_location
    is_remote = item.get("isRemote")
    if is_remote is None:
        is_remote = "remote" in str(item_location).lower()
    return {
        "external_job_id": build_external_job_id(item),
        "title": item.get("title") or "Unknown Title",
        "company": item.get("companyName")
        or item.get("company")
        or "Unknown Company",
        "location": item_location,
        "is_remote": bool(is_remote),
        "description": item.get("description") or item.get("text") or "",
        "raw_payload": item,
    }


def build_actor_input(portal: str, term: str, loc: str, limit: int) -> dict[str, Any]:
    # Every Apify actor exposes its own input schema. If a run fails validation,
    # compare these keys against the actor input form in the Apify Console.
    if portal == "linkedin":
        return {
            "searchString": term,
            "location": loc,
            "maxItems": limit,
            "parseCompanyDetails": False,
        }
    if portal == "indeed":
        return {
            "query": term,
            "location": loc,
            "resultsWanted": limit,
            "country": "us",
        }
    return {"searchString": term, "location": loc, "maxItems": limit}


async def fetch_from_scraper_api(
    term: str, loc: str, portal: str, actor_id: str, limit: int
) -> list[dict[str, Any]]:
    """
    Runs the resolved Apify actor for the requested portal and returns normalized
    postings. Failures raise so the MCP client sees the tool error instead of an
    empty run.
    """
    if not APIFY_TOKEN:
        raise RuntimeError(
            "APIFY_TOKEN is not configured. Set it in the environment (.env used by docker compose)."
        )

    run_input = build_actor_input(portal, term, loc, limit)

    print(f"Triggering Apify actor {actor_id} for '{term}' in '{loc}'...")
    try:
        run = await asyncio.to_thread(
            apify_client.actor(actor_id).call,
            run_input=run_input,
            max_items=limit,
            wait_duration=APIFY_WAIT_DURATION,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Apify actor '{actor_id}' failed for '{term}' in '{loc}': {exc}"
        ) from exc

    # apify-client >= 3 returns a Run model, not a dict.
    if run is None:
        raise RuntimeError(f"Apify actor '{actor_id}' returned no run object.")
    if run.status != "SUCCEEDED":
        detail = run.status_message or "no status message"
        raise RuntimeError(
            f"Apify actor '{actor_id}' ended with status '{run.status}': {detail}"
        )

    dataset_id = run.default_dataset_id
    if not dataset_id:
        raise RuntimeError(f"Apify actor '{actor_id}' returned no dataset id.")

    try:
        dataset_items = await asyncio.to_thread(
            lambda: apify_client.dataset(dataset_id).list_items(limit=limit).items
        )
    except Exception as exc:
        raise RuntimeError(
            f"Could not read Apify dataset '{dataset_id}': {exc}"
        ) from exc

    return [normalize_apify_item(item, loc) for item in dataset_items]


async def store_jobs(
    pool: asyncpg.Pool,
    portal: str,
    prepared_jobs: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> tuple[int, int]:
    new_ingested = 0
    jobs_updated = 0

    async with pool.acquire() as conn:
        for prepared_job, embedding in zip(prepared_jobs, embeddings):
            job = prepared_job["job"]
            result = await conn.fetchrow(
                UPSERT_QUERY,
                job["external_job_id"],
                portal,
                job["title"],
                job["company"],
                job["location"],
                job["is_remote"],
                prepared_job["clean_description"],
                prepared_job["skills"],
                json.dumps(job["raw_payload"]),
                json.dumps(embedding),
            )
            if result["is_insert"]:
                new_ingested += 1
            else:
                jobs_updated += 1

    return new_ingested, jobs_updated
