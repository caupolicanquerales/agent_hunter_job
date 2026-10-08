CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS scraped_job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_job_id VARCHAR(255) NOT NULL,
    source_portal VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    is_remote BOOLEAN DEFAULT FALSE,
    salary_min NUMERIC(12, 2),
    salary_max NUMERIC(12, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    clean_description TEXT NOT NULL,
    required_skills TEXT[],
    raw_payload JSONB,
    
    -- Updated to 384 dimensions for sentence-transformers all-MiniLM-L6-v2
    embedding vector(384), 
    
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_portal_job UNIQUE (external_job_id, source_portal)
);

-- Index for HNSW fast approximate vector search
CREATE INDEX IF NOT EXISTS idx_jobs_embedding_hnsw 
ON scraped_job_postings USING hnsw (embedding vector_cosine_ops);