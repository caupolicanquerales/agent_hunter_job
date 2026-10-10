---
name: job-read-chunk-files
description: Executes reader_chunk_opportunities.py to load one chunk_*.json from reports/ when a sub agent sends the file name to read.
---

# Job Read Chunk Files

**Trigger:** a sub agent sends a file name to read (`chunk_01.json`, "read chunk_01.json", "leer chunk_01.json", ...). Never read chunk files by hand.

## Run

Run exactly this **single command from the project root** (`agent_hunter_job`) — one bare file name, no `cd`, no absolute path, no `2>&1`, no pipes, no extra flags:

```bash
python3 .opencode/skills/job-read-chunk-files/scripts/reader_chunk_opportunities.py <chunk_file_name>
```

The script resolves `reports/` from its own location, so it never needs `cd` or an absolute path. Execute it immediately and never ask the user to approve it. Every variant (absolute path, `cd`, `2>&1`, `| head`, `cat`) is a different command line and forces a fresh approval prompt — never improvise it.

## Output

- stdout: only the parsed object `{chunk, candidate_count, candidates}` (candidates include all job fields + `matched_keywords`).
- Root pre-established (`reports/`): pass only the file name, never a path.
- Exit codes: `0` OK, `1` file/structure error (stderr), `2` missing argument.

Return the object as received or the error verbatim; on failure don't claim the file was read. No trigger for other files or candidate analysis.

**Approvals cannot be declared in a `SKILL.md`:** no-ask is configured in `.vscode/settings.json` (`chat.tools.terminal.enableAutoApprove` + `chat.tools.terminal.autoApprove`) for VS Code and in `opencode.json` (`permission.bash`) for opencode.
