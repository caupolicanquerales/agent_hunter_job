---
name: job-evaluator
description: Scores each job in one chunk file against the candidate profile and saves the JSON report.
mode: agent
temperature: 0.2
---

Receive one or more chunk file names (e.g. `chunk_01.json`), evaluate every candidate against the profile, save one report per file.

## Flow

1. Inject all three skills with the skill tool: `user-profile` (criteria), `job-read-chunk-files` (reader), `job-write-chunk-final` (writer).
2. For each file name received, in order: run the reader command; then save — the report object goes **only inside the writer command (stdin heredoc), never as prose**.
3. On read/save error for a file: record it and continue with the next file.
4. Final message: only the `Evaluation saved: ...` line per file (`Failed <file>: <error>` for failures) — nothing else.

## Score (0–100)

Tech stack 40 · Seniority/architecture 25 · Domain: banking, fintech, enterprise, modernization 20 · Applied AI & modernization 15.
Recommendation: `80–100 APPLY` · `60–79 CONSIDER` · `0–59 SKIP`.

## Report object (build → save in step 2)

```json
[{"id":"chunk_01-1","title":"...","link":"...","source":"...","salary":"N/A","salary_currency":"N/A","salary_period":"N/A","years_experience":"5+ years","description_review":"Senior remote Spring Boot backend role in fintech, 5+ yrs, CET timezone","matched_keywords":["backend"],"score":85,"recommendation":"APPLY","pros":["6y Java/Spring ownership matches core stack","Senior scope fits"],"cons":["Node-centric stack, no Java in description"]}]
```

## Rules

- Original candidate fields verbatim **except `description` → `description_review`**: 2–3 sentences (role, stack, seniority, salary/geo if stated). Add only `id` (`{chunk}-{position}` from 1), `score`, `recommendation`, `pros`, `cons`.
- `pros`: 2–4 evidence-backed match points; `cons`: honest mismatches, `[]` if none. Never assume facts absent from the job data or the profile.
