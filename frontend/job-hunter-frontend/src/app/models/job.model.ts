import type { ScrapedJobPosting } from './scraped-job-posting.model';

/**
 * Dashboard model: every field of the scraped_job_postings row plus the
 * derived fields used by the list and filters.
 */
export interface JobModel extends Partial<ScrapedJobPosting> {
  id?: string;
  source_portal?: string;
  title: string;
  company: string;
  location: string;
  is_remote: boolean;
  clean_description: string;
  required_skills: string[]; // parsed from DB array/JSON
  raw_payload: any;          // stored JSON payload
  embedding?: number[];      // vector embedding data
  scraped_at: string;        // ISO timestamp
  match_score?: number;      // calculated via vector similarity query (0.00 to 1.00)
}

export type JobSortOption = 'match_score_desc' | 'match_score_asc' | 'date_desc' | 'title_asc';

export interface JobFilterCriteria {
  keyword: string;
  remoteOnly: boolean;
  selectedSkills: string[];
  sortBy: JobSortOption;
}
