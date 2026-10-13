import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_NAME,
    MAX_RESULTS_LIMIT,
    MCP_HOST,
    MCP_PORT,
    MCP_TRANSPORT,
)
from job_ingestion import (
    close_db_pool,
    encode_texts,
    get_db_pool,
    prepare_evaluations,
    search_jobs,
    store_evaluations,
)


@asynccontextmanager
async def lifespan(_server: FastMCP):
    try:
        yield {}
    finally:
        await close_db_pool()


mcp = FastMCP(
    "job-ingestion-gateway",
    host=MCP_HOST,
    port=MCP_PORT,
    lifespan=lifespan,
)


@mcp.tool()
async def store_job_postings(postings: list[dict[str, Any]]) -> str:
    """
    Embeds job evaluations with the local sentence-transformers model and
    upserts them into the pgvector table scraped_job_postings. Returns
    lightweight ingestion metadata only.

    postings: list of evaluated job objects, one per candidate, using the same
        shape written to results/<chunk>_evaluation.json. Recognized keys:
        id, title, link, source, salary, salary_currency, salary_period,
        years_experience, description_review, matched_keywords, score,
        recommendation, pros, cons.
    """
    if not postings:
        raise ValueError("postings must contain at least one entry")

    prepared_evaluations = prepare_evaluations(postings)

    embeddings: list[list[float]] = await asyncio.to_thread(
        encode_texts,
        [evaluation["embedding_text"] for evaluation in prepared_evaluations],
    )

    pool = await get_db_pool()
    new_ingested, jobs_updated = await store_evaluations(
        pool, prepared_evaluations, embeddings
    )

    return json.dumps(
        {
            "status": "success",
            "total_received": len(postings),
            "new_jobs_stored": new_ingested,
            "jobs_updated": jobs_updated,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedded_dimension": EMBEDDING_DIMENSIONS,
            "storage_reference": "table:scraped_job_postings",
        }
    )


@mcp.tool()
async def search_job_postings(
    query: str,
    limit: int = 5,
    source: str | None = None,
) -> str:
    """
    Runs a cosine-similarity search against scraped_job_postings using the
    pgvector HNSW index. Returns the closest evaluated jobs ranked by similarity.

    query: free-text search term embedded with the local model.
    limit: maximum number of jobs to return (clamped to MAX_RESULTS_LIMIT).
    source: optional source filter, matched case-insensitively.
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    result_limit = max(1, min(limit, MAX_RESULTS_LIMIT))
    requested_source = source.strip().lower() if source else None

    query_embedding = (await asyncio.to_thread(encode_texts, [query]))[0]

    pool = await get_db_pool()
    matches = await search_jobs(
        pool, query_embedding, result_limit, requested_source
    )

    return json.dumps(
        {
            "status": "success",
            "query": query,
            "source": requested_source,
            "total_results": len(matches),
            "results": matches,
        },
        default=str,
    )


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
