---
name: job-search-filter
description: Executes the prefilter script that turns reports/job_opportunities.js into chunk files of 5 candidate jobs each. Inject only after the orchestrator has notified the user that job_opportunities.js was created.
---

# Job Search Filter

Runs two scripts: clean the previous chunk files, then pre-filter the fetched job offers by keyword and split the selected candidates into small chunk files for a later agent analysis step. Never analyze or scrape candidates manually here.

**Trigger** (EN/ES) only after the orchestrator has notified the user that `reports/job_opportunities.js` was created (or, without a fetch in the turn, that the existing report will be used): "prefilter the jobs", "filter the opportunities", "create candidate chunks", "pre-filtrar oportunidades", "filtrar ofertas", "crear lotes de candidatos".

## Run

From the project root (`agent_hunter_job`), in this order:

```bash
python3 .opencode/skills/job-delete-all-files/scripts/delete_all_files_in_folder.py reports --pattern "chunk_*.json"
python3 .opencode/skills/job-search-filter/scripts/prefilter_job_opportunities.py
```

The first command (skill `job-delete-all-files`) removes the stale `reports/chunk_*.json` so only the new chunks remain; it never touches `job_opportunities.js`, which is the prefilter's input. Run both commands without asking to overwrite anything.

## Output

- `reports/chunk_01.json`, `reports/chunk_02.json`, ... → one file per chunk of up to 5 candidates; every candidate carries its original fields plus `matched_keywords`.
- The final console lines are:
  - `Chunk files to process: N` → the number of chunk files the orchestrator must process/report next.
  - `Chunk file names: chunk_01.json, chunk_02.json, ...` → **every file name to process, ready to use inside `reports/`; the next step must not search for file names.**

Keywords come from `constants/filters.js` (`FILTER_KEYWORDS`), matched by containment against each job description (case-insensitive, separator variants included). Stale `chunk_*.json` files are removed before writing and existing chunks are overwritten without confirmation — never ask the user to approve an overwrite.

Report the final `Chunk files to process: N` line together with the `Chunk file names: ...` line; if the script fails, report the error and do not claim completion. No trigger for general web browsing, manual scraping, or analysis of chunk contents.
