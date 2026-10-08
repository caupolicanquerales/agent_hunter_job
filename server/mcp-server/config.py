import os
from datetime import timedelta

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "3000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:secretpassword@localhost:5432/jobs_db"
)

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
MAX_RESULTS_LIMIT = 100
APIFY_WAIT_DURATION = timedelta(minutes=10)

MAX_SKILL_KEYWORDS = 100
MAX_ACTOR_IDS = 20
FALLBACK_KEYWORDS = [
    "Java",
    "Spring Boot",
    "Angular",
    "TypeScript",
    "Docker",
    "PostgreSQL",
    "Python",
    "AWS",
]
DEFAULT_ACTOR_IDS = {
    "linkedin": "curious_coder~linkedin-jobs-scraper",
    "indeed": "misceres~indeed-scraper",
    "general": "webscrap18~job-scraper",
}
