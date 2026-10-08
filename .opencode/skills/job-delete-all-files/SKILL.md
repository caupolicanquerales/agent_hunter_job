---
name: job-delete-all-files
description: Executes delete_all_files_in_folder.py to clean generated files (chunks, evaluation reports) out of a project folder before a new run. Use when a skill or agent needs an empty output folder.
---

# Job Delete All Files

Empties stale generated files from one project folder so a new run starts clean. Deletes **files only** (never subdirectories), non-recursive, and only inside the project.

**Trigger** (EN/ES): "clean/empty the folder", "delete the generated files", "limpiar la carpeta", "borrar los archivos generados", "resetear resultados".

## Run

From the project root (`agent_hunter_job`):

```bash
python3 .opencode/skills/job-delete-all-files/scripts/delete_all_files_in_folder.py <folder> [--pattern <glob>] [--exclude <glob>]
```

- `<folder>` relative to the project root (`reports`, `results`) or an absolute path inside the project.
- `--pattern` repeatable → only matching file names are deleted (e.g. `chunk_*.json`); omit it to delete every file.
- `--exclude` repeatable → matching file names are always kept.

```bash
python3 .opencode/skills/job-delete-all-files/scripts/delete_all_files_in_folder.py reports --pattern "chunk_*.json"
python3 .opencode/skills/job-delete-all-files/scripts/delete_all_files_in_folder.py results
```

## Output

- `Removed N files from <path>` plus a `Removed: <names>` line (only when something was removed); a missing folder prints `Folder not found (nothing to remove): <path>` and exits `0`.
- Exit codes: `0` done / nothing to remove · `1` protected folder (project root, home, `/`) or path outside the project · `2` bad usage.
- Never clean `reports/` without `--pattern "chunk_*.json"` (or `--exclude job_opportunities.js`): that file is the input of `job-search-filter`.
- `results/` is shared by parallel `job-evaluator` instances: the orchestrator cleans it once before fan-out, instances only clean their own `<chunk>_evaluation.json`.
- Report the `Removed N files` line; on exit `1`/`2` report the error and stop. No trigger for deleting folders, files outside the project, or source code.
