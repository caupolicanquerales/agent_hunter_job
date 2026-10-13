CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS scraped_job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- job identity
    eval_id VARCHAR(50) NOT NULL,
    external_job_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    link TEXT,
    source VARCHAR(255) NOT NULL,

    -- compensation and experience
    salary VARCHAR(255),
    salary_currency VARCHAR(16),
    salary_period VARCHAR(32),
    years_experience VARCHAR(64),

    -- evaluation content
    description_review TEXT,
    matched_keywords TEXT[],
    score SMALLINT CHECK (score BETWEEN 0 AND 100),
    recommendation VARCHAR(20),
    pros TEXT[],
    cons TEXT[],

    -- raw evaluation document as received
    raw_payload JSONB,

    -- Updated to 384 dimensions for sentence-transformers all-MiniLM-L6-v2
    embedding vector(384),

    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_source_job UNIQUE (external_job_id, source)
);

-- Index for HNSW fast approximate vector search
CREATE INDEX IF NOT EXISTS idx_jobs_embedding_hnsw
ON scraped_job_postings USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_jobs_recommendation
ON scraped_job_postings (recommendation);

CREATE INDEX IF NOT EXISTS idx_jobs_score
ON scraped_job_postings (score DESC);
