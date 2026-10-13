---
name: job-write-chunk-final
description: Executes final_chunk_reporter.py to save the job-evaluator JSON report into results/ for one chunk file.
---

**Trigger:** orchestrator holds the chunk file name + the `job-evaluator` JSON report. Never save by hand.

First write the report to a dedicated file with the write tool, then pass that path as an **explicit file argument** (never stdin: parallel evaluators in the same session share standard input, and a heredoc corrupts under concurrency). Redirect stdout/stderr to your per-chunk scratch files so parallel instances never share the terminal stream (`<chunk>` = the file name without `.json`):

```bash
python3 .opencode/skills/job-write-chunk-final/scripts/final_chunk_reporter.py <chunk_file_name> <report_json_file> > results/.<chunk>.writer.log 2> results/.<chunk>.writer.err
```

- `<chunk_file_name>`: e.g. `chunk_01.json`.
- `<report_json_file>`: file holding the evaluation JSON array, e.g. `reports/chunk_01_report.json`. One file per chunk, so parallel evaluators never collide.

The script reads that file, writes `results/<chunk>_evaluation.json` **atomically** (temp file + `fsync` + `os.replace`, so a concurrent reader never sees a half-written file), deletes the report file, then upserts the jobs into pgvector. Database ingestion is serialized across processes with an advisory file lock (`results/.reporter.lock`) plus bounded retries, so parallel reporters cannot saturate the connection pool or deadlock on row locks.

**Output:** `results/<chunk>_evaluation.json` (verbatim, auto-created) + `Evaluation saved: <path> (N jobs evaluated)` written to `results/.<chunk>.writer.log` (read it back), then the jobs are upserted into pgvector by calling the MCP tool `store_job_postings` over SSE (`Database store: X new, Y updated`). Exit: `0` OK · `1` bad JSON/name/report file · `2` missing arg. A database failure only prints a `Warning:` (in the `.writer.err` file) and keeps exit `0`, because the file is the source of truth.

The MCP endpoint defaults to `http://127.0.0.1:3000/sse` and is overridable with `MCP_SERVER_URL`; `MCP_TIMEOUT_SECONDS` (default `30`) bounds the handshake. `REPORTER_DB_LOCK_TIMEOUT_SECONDS` (default `180`) bounds the ingestion lock and `REPORTER_DB_RETRIES` (default `3`) bounds the retries. Requires the `jobs-mcp-server` stack (see `job-launch-mcp-server`).

Report the path and job count; on failure report the error, don't claim it was saved. No trigger for reading or evaluating chunks.

**Approvals cannot be declared in a `SKILL.md`:** no-ask is configured in `.vscode/settings.json` (`chat.tools.terminal.enableAutoApprove` + `chat.tools.terminal.autoApprove`) for VS Code and in `opencode.json` (`permission.bash`) for opencode.
