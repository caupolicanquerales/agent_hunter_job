import asyncio
import json
from contextlib import asynccontextmanager

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
    fetch_from_scraper_api,
    get_db_pool,
    normalize_actor_ids,
    normalize_skill_keywords,
    prepare_jobs,
    store_jobs,
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
async def trigger_job_sync(
    search_term: str,
    location: str = "Remote",
    portal: str = "linkedin",
    max_results: int = 20,
    skills: list[str] | None = None,
    actor_ids: dict[str, str] | None = None,
) -> str:
    """
    Searches live job portals through Apify actors, embeds every posting with the
    local sentence-transformers model and upserts the result into the pgvector
    table scraped_job_postings. Returns lightweight execution metadata only.

    portal: key of the actor to run, matched case-insensitively; defaults to
        "linkedin" and must exist in actor_ids.
    skills: keywords matched against each posting; the matches are stored in
        required_skills and added to the embedded text. Pass the array from
        .opencode/skills/job-search-filter/constants/filters.js (FILTER_KEYWORDS)
        to stay in sync with the prefilter. When omitted, falls back to the
        built-in default list.
    actor_ids: map of portal name to Apify actor id (e.g. {"linkedin":
        "curious_coder~linkedin-jobs-scraper"}). When omitted, falls back to
        the built-in default map.
    """
    if not search_term.strip():
        raise ValueError("search_term must not be empty")
    result_limit = max(1, min(max_results, MAX_RESULTS_LIMIT))
    requested_portal = portal.strip().lower()
    actor_map = normalize_actor_ids(actor_ids)
    if requested_portal not in actor_map:
        raise ValueError(
            f"portal '{portal}' is not present in actor_ids; "
            f"available portals: {', '.join(sorted(actor_map))}"
        )
    actor_id = actor_map[requested_portal]
    skill_keywords = normalize_skill_keywords(skills)

    raw_jobs = await fetch_from_scraper_api(
        search_term, location, requested_portal, actor_id, result_limit
    )
    prepared_jobs = prepare_jobs(raw_jobs, skill_keywords)

    embeddings: list[list[float]] = []
    if prepared_jobs:
        embeddings = await asyncio.to_thread(
            encode_texts, [job["embedding_text"] for job in prepared_jobs]
        )

    pool = await get_db_pool()
    new_ingested, jobs_updated = await store_jobs(
        pool, requested_portal, prepared_jobs, embeddings
    )

    return json.dumps(
        {
            "status": "success",
            "portal": requested_portal,
            "actor_id": actor_id,
            "target_query": search_term,
            "location": location,
            "total_fetched": len(raw_jobs),
            "new_jobs_stored": new_ingested,
            "jobs_updated": jobs_updated,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedded_dimension": EMBEDDING_DIMENSIONS,
            "keywords_tracked": len(skill_keywords),
            "storage_reference": "table:scraped_job_postings",
        }
    )


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
