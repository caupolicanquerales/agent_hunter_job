---
name: job-delete-all-files
description: Executes delete_all_files_in_folder.py to clean generated files (chunks, evaluation reports) out of a project folder before a new run. Use when a skill or agent needs an empty output folder.
---

# Job Delete All Files

Empties stale generated files from one project folder so a new run starts clean. Files only, non-recursive, inside the project — never subdirectories or source code.

**Trigger** (EN/ES): "clean/empty the folder", "delete the generated files", "limpiar la carpeta", "borrar los archivos generados", "resetear resultados".

## Run

```bash
python3 .opencode/skills/job-delete-all-files/scripts/delete_all_files_in_folder.py <folder> [--pattern <glob>] [--exclude <glob>]
```

`<folder>` = `reports`/`results` (or absolute, inside the project); run from the project root (`agent_hunter_job`). `--pattern` repeatable → deletes matching names only (omit → all; e.g. `chunk_*.json`); `--exclude` repeatable → always kept. E.g. `... results` · `... reports --pattern "chunk_*.json"`.

## Output

`Removed N files from <path>` (+ `Removed: <names>` if any); missing folder → `Folder not found (nothing to remove): <path>` exit `0`; protected/outside path exit `1`; bad usage exit `2`. Report the line; on `1`/`2` report the error and stop.

- Clean `reports/` only right before a fetch (`job-search-web` recreates `job_opportunities.js`); never clean it while reusing the existing report, or the prefilter loses its input.
- `results/` is shared by parallel `job-evaluator` instances: the orchestrator cleans it once at the start (step 3); each instance only writes its own `<chunk>_evaluation.json`.
