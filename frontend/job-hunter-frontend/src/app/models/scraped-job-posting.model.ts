import { JobModel } from './job.model';

/**
 * Row returned by SEARCH_QUERY in server/mcp-server/job_ingestion.py
 * (table scraped_job_postings, plus the computed similarity column).
 */
export interface ScrapedJobPosting {
  id: string;
  eval_id: string;
  external_job_id: string;
  title: string;
  link: string | null;
  source: string;
  salary: string | null;
  salary_currency: string | null;
  salary_period: string | null;
  years_experience: string | null;
  description_review: string | null;
  matched_keywords: string[] | null;
  score: number | null;
  recommendation: string | null;
  pros: string[] | null;
  cons: string[] | null;
  evaluated_at: string;
  similarity: number | null;
  raw_payload?: Record<string, unknown> | null;
}

/** Response body of GET /api/jobs/search (see server/backend-server/handle_search.py). */
export interface JobSearchResponse {
  query: string;
  source: string | null;
  total_results: number;
  results: ScrapedJobPosting[];
}

/**
 * Maps a database row to the dashboard model.
 * The table has no company, location, remote flag or salary bounds, so those
 * fields take defaults until the search query returns them.
 */
export function toJobModel(row: ScrapedJobPosting): JobModel {
  const payload = row.raw_payload ?? {};
  return {
    ...row,
    source_portal: row.source,
    company: String(payload['company'] ?? ''),
    location: String(payload['location'] ?? ''),
    is_remote: Boolean(payload['is_remote'] ?? false),
    clean_description: row.description_review ?? '',
    required_skills: row.matched_keywords ?? [],
    raw_payload: row.raw_payload ?? {},
    match_score: row.similarity ?? undefined,
    scraped_at: row.evaluated_at,
  };
}
