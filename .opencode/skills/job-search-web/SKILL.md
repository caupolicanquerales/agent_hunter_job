---
name: job-search-web
description: Executes the fetch script that pulls fresh job vacancies from public web sources into the reports folder. Use when the orchestrator orders a job search on the web.
---

# Job Search Web

Runs one script that fetches job offers from the configured portals. Never scrape manually or paste raw listings into the conversation.

**Trigger** (EN/ES) when the orchestrator orders a job search: "search for jobs", "find remote roles", "fetch/refresh vacancies", "list job opportunities", "buscar empleos", "mostrar vacantes", "ver oportunidades laborales".

## Run

From the project root (`agent_hunter_job`):

```bash
python3 .opencode/skills/job-search-web/scripts/fetch_jobs.py
```

## Output

- `reports/job_opportunities.js` → `export const JOB_OPPORTUNITIES = {...}` grouped by portal; downstream steps read it.
- `.opencode/opportunities/raw_jobs_YYYY-MM-DD.json` → raw pre-filtered list.

Report only the job count and any fetch errors. No trigger for general web browsing, document/file search, or lookups unrelated to job vacancies.
