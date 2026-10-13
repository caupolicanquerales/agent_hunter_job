import os

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "3000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:secretpassword@localhost:5432/jobs_db"
)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
MAX_RESULTS_LIMIT = 100

MAX_SKILL_KEYWORDS = 100
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
