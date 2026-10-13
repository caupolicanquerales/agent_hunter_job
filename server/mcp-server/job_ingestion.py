import asyncio
import hashlib
import json
import re
from typing import Any

import asyncpg
from sentence_transformers import SentenceTransformer

from config import DATABASE_URL, EMBEDDING_MODEL_NAME

print(f"Loading local vector embedding model '{EMBEDDING_MODEL_NAME}'...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

_db_pool: asyncpg.Pool | None = None
_db_pool_lock = asyncio.Lock()

UPSERT_QUERY = """
    INSERT INTO scraped_job_postings
        (eval_id, external_job_id, title, link, source, salary, salary_currency,
         salary_period, years_experience, description_review, matched_keywords,
         score, recommendation, pros, cons, raw_payload, embedding)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            $16, $17::vector)
    ON CONFLICT (external_job_id, source)
    DO UPDATE SET
        eval_id = EXCLUDED.eval_id,
        title = EXCLUDED.title,
        link = EXCLUDED.link,
        salary = EXCLUDED.salary,
        salary_currency = EXCLUDED.salary_currency,
        salary_period = EXCLUDED.salary_period,
        years_experience = EXCLUDED.years_experience,
        description_review = EXCLUDED.description_review,
        matched_keywords = EXCLUDED.matched_keywords,
        score = EXCLUDED.score,
        recommendation = EXCLUDED.recommendation,
        pros = EXCLUDED.pros,
        cons = EXCLUDED.cons,
        raw_payload = EXCLUDED.raw_payload,
        embedding = EXCLUDED.embedding,
        evaluated_at = CURRENT_TIMESTAMP;
"""

EXISTS_QUERY = """
    SELECT EXISTS (
        SELECT 1 FROM scraped_job_postings
        WHERE external_job_id = $1 AND source = $2
    );
"""

SEARCH_QUERY = """
    SELECT
        id,
        eval_id,
        external_job_id,
        title,
        link,
        source,
        salary,
        salary_currency,
        salary_period,
        years_experience,
        description_review,
        matched_keywords,
        score,
        recommendation,
        pros,
        cons,
        evaluated_at,
        1 - (embedding <=> $1::vector) AS similarity
    FROM scraped_job_postings
    WHERE ($2::text IS NULL OR source = $2)
    ORDER BY embedding <=> $1::vector
    LIMIT $3;
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


def encode_texts(texts: list[str]) -> list[list[float]]:
    return embedder.encode(texts, show_progress_bar=False).tolist()


def build_external_job_id(item: dict[str, Any]) -> str:
    source = item.get("link") or item.get("url")
    if not source:
        source = "|".join(
            str(item.get(key, "")) for key in ("title", "source", "link")
        )
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()


def coerce_score(raw_score: Any) -> int | None:
    if raw_score is None:
        return None
    try:
        score = int(raw_score)
    except (TypeError, ValueError):
        return None
    return max(0, min(score, 100))


def build_embedding_text(item: dict[str, Any]) -> str:
    keywords = ", ".join(item.get("matched_keywords") or [])
    pros = " ; ".join(item.get("pros") or [])
    cons = " ; ".join(item.get("cons") or [])
    return (
        f"Title: {item.get('title', '')} | Source: {item.get('source', '')} "
        f"| Keywords: {keywords} "
        f"| Review: {sanitize_text(item.get('description_review') or '')} "
        f"| Pros: {pros} | Cons: {cons}"
    )


def normalize_evaluation(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "eval_id": str(item.get("id") or ""),
        "external_job_id": build_external_job_id(item),
        "title": item.get("title") or "Unknown Title",
        "link": item.get("link"),
        "source": item.get("source") or "unknown",
        "salary": item.get("salary"),
        "salary_currency": item.get("salary_currency"),
        "salary_period": item.get("salary_period"),
        "years_experience": item.get("years_experience"),
        "description_review": item.get("description_review") or "",
        "matched_keywords": item.get("matched_keywords") or [],
        "score": coerce_score(item.get("score")),
        "recommendation": item.get("recommendation") or "SKIP",
        "pros": item.get("pros") or [],
        "cons": item.get("cons") or [],
        "raw_payload": item,
        "embedding_text": build_embedding_text(item),
    }


def prepare_evaluations(
    evaluations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [normalize_evaluation(evaluation) for evaluation in evaluations]


async def store_evaluations(
    pool: asyncpg.Pool,
    prepared_evaluations: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> tuple[int, int]:
    new_ingested = 0
    jobs_updated = 0

    async with pool.acquire() as conn:
        for prepared, embedding in zip(prepared_evaluations, embeddings):
            async with conn.transaction():
                already_exists = await conn.fetchval(
                    EXISTS_QUERY,
                    prepared["external_job_id"],
                    prepared["source"],
                )
                await conn.execute(
                    UPSERT_QUERY,
                    prepared["eval_id"],
                    prepared["external_job_id"],
                    prepared["title"],
                    prepared["link"],
                    prepared["source"],
                    prepared["salary"],
                    prepared["salary_currency"],
                    prepared["salary_period"],
                    prepared["years_experience"],
                    prepared["description_review"],
                    prepared["matched_keywords"],
                    prepared["score"],
                    prepared["recommendation"],
                    prepared["pros"],
                    prepared["cons"],
                    json.dumps(prepared["raw_payload"]),
                    json.dumps(embedding),
                )
            if already_exists:
                jobs_updated += 1
            else:
                new_ingested += 1

    return new_ingested, jobs_updated


async def search_jobs(
    pool: asyncpg.Pool,
    query_embedding: list[float],
    limit: int,
    source: str | None = None,
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            SEARCH_QUERY,
            json.dumps(query_embedding),
            source,
            limit,
        )
    return [dict(row) for row in rows]
