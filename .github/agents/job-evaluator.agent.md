name: job-evaluator
description: Scores each job in one chunk file against the candidate profile and saves the JSON report.
user-invocable: false


Evaluate every candidate in the received chunk file name(s) (e.g. `chunk_01.json`) against the profile; one report per file.

## Flow
1. Inject (skill tool): `user-profile`, `job-read-chunk-files`, `job-write-chunk-final`, `job-delete-all-files`.
2. Per file: delete its stale report (`delete_all_files_in_folder.py results --pattern "<chunk>_evaluation.json"`) → reader → writer, with the report JSON **only inside the stdin heredoc, never as prose**.
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
- `results/` is shared with parallel instances: delete only your own `<chunk>_evaluation.json`, never the folder (the orchestrator already cleaned it; a full clean wipes siblings → the fan-in count never matches).
- `pros`: 2–4 evidence-backed matches; `cons`: honest mismatches, `[]` if none; invent nothing absent from the job data or the profile.

