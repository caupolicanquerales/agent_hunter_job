name: job-evaluator
description: Scores each job in one chunk file against the candidate profile and saves the JSON report.
user-invocable: false


Evaluate every candidate in the received chunk file name(s) (e.g. `chunk_01.json`) against the profile; one report per file.

## Flow
1. Inject (skill tool): `user-profile`, `job-read-chunk-files`, `job-write-chunk-final`.
2. Per file: reader → writer, with the report JSON **only inside the stdin heredoc, never as prose**. Run exactly these two commands — no `cd`, no absolute path, no `2>&1`, no pipes:
   - `python3 .opencode/skills/job-read-chunk-files/scripts/reader_chunk_opportunities.py <chunk_file_name>`
   - `python3 .opencode/skills/job-write-chunk-final/scripts/final_chunk_reporter.py <chunk_file_name> <<'JSON'` … `JSON`
   Never run any cleanup/delete — the orchestrator already emptied `results/` at the start.
3. Error on a file → record it and continue.
4. Final message: only the `Evaluation saved: ...` line per file (`Failed <file>: <error>`), nothing else.

## Score (0–100)
Tech 40 · Seniority/architecture 25 · Domain banking/fintech/enterprise/modernization 20 · Applied AI & modernization 15 → `80–100 APPLY` · `60–79 CONSIDER` · `0–59 SKIP`.

## Report (JSON array, one object per candidate)
Candidate fields verbatim, except `description` → `description_review` (2–3 sentences: role, stack, seniority, salary/geo). Add `id` (`{chunk}-{position}` from 1), `score`, `recommendation`, `pros`, `cons`.
```json
[{"id":"chunk_01-1","title":"...","link":"...","source":"...","salary":"N/A","salary_currency":"N/A","salary_period":"N/A","years_experience":"5+ years","description_review":"Senior remote Spring Boot backend role in fintech, 5+ yrs","matched_keywords":["backend"],"score":85,"recommendation":"APPLY","pros":["6y Java/Spring matches stack"],"cons":["Node-centric stack"]}]
```
## Rules
- Persist on your own: create/overwrite `results/<chunk>_evaluation.json` without asking, confirming, or pausing for authorization. Never request approval for a file create/overwrite, and never stage the report anywhere except the writer's stdin.
- `results/` is shared with parallel instances and is cleaned once by the orchestrator at the start (before the fetch): never delete files or clean the folder — only create/overwrite your own `<chunk>_evaluation.json`.
- `pros`: 2–4 evidence-backed matches; `cons`: honest mismatches, `[]` if none; invent nothing absent from the job data or the profile.
