---
name: job-read-chunk-files
description: Executes reader_chunk_opportunities.py to load one chunk_*.json from reports/ when a sub agent sends the file name to read.
---

# Job Read Chunk Files

**Trigger:** a sub agent sends a file name to read (`chunk_01.json`, "read chunk_01.json", "leer chunk_01.json", ...). Never read chunk files by hand.

## Run

From the project root (`agent_hunter_job`):

```bash
python3 .opencode/skills/job-read-chunk-files/scripts/reader_chunk_opportunities.py <chunk_file_name>
```

## Output

- stdout: only the parsed object `{chunk, candidate_count, candidates}` (candidates include all job fields + `matched_keywords`).
- Root pre-established (`reports/`): pass only the file name, never a path.
- Exit codes: `0` OK, `1` file/structure error (stderr), `2` missing argument.

Return the object as received or the error verbatim; on failure don't claim the file was read. No trigger for other files or candidate analysis.
