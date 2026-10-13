---
name: job-evaluator
description: Scores each job in one chunk file against the candidate profile and saves the JSON report.
mode: subagent
temperature: 0.2
permission:
  "*": allow
  read: allow
  edit: allow
  bash: allow
  glob: allow
  grep: allow
  list: allow
  skill: allow
  task: allow
  webfetch: allow
  websearch: allow
  external_directory:
    "*": allow
---

Evaluate every candidate in the received chunk file name(s) (e.g. `chunk_01.json`) against the profile; one report per file.

## Flow
1. Inject (skill tool): `user-profile`, `job-read-chunk-files`, `job-write-chunk-final`.
2. Per file: reader → writer, each command **isolated** — parallel instances share one terminal, so never print command output to it. Redirect stdout/stderr to per-chunk files (`<chunk>` = the chunk file name without `.json`) and read them back; no `cd`, no `&`, no pipes. Write the report JSON to `reports/<chunk>_report.json` (write tool) and pass it as an explicit argument (never stdin/heredoc):
   - `python3 .opencode/skills/job-read-chunk-files/scripts/reader_chunk_opportunities.py <chunk_file_name> > reports/.<chunk>.reader.json 2> reports/.<chunk>.reader.err`, then read `reports/.<chunk>.reader.json`.
   - `python3 .opencode/skills/job-write-chunk-final/scripts/final_chunk_reporter.py <chunk_file_name> reports/<chunk>_report.json > results/.<chunk>.writer.log 2> results/.<chunk>.writer.err`, then read `results/.<chunk>.writer.log`.
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
- Persist on your own: create/overwrite `results/<chunk>_evaluation.json` without asking, confirming, or pausing for authorization. Never request approval for a file create/overwrite, and stage the report only in its per-chunk file `reports/<chunk>_report.json` (passed to the writer), never via stdin.
- Isolation: keep every command's stdout/stderr in this instance's `.reader`/`.writer` files; never print command output to the shared terminal (only the final status line goes to the parent).
- `results/` is shared with parallel instances and is cleaned once by the orchestrator at the start (before the fetch): never delete files or clean the folder — only create/overwrite your own `<chunk>_evaluation.json`.
- `pros`: 2–4 evidence-backed matches; `cons`: honest mismatches, `[]` if none; invent nothing absent from the job data or the profile.
