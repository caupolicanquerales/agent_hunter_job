---
name: job-write-chunk-final
description: Executes final_chunk_reporter.py to save the job-evaluator JSON report into results/ for one chunk file.
---

**Trigger:** orchestrator holds the chunk file name + the `job-evaluator` JSON report. Never save by hand.

```bash
python3 .opencode/skills/job-write-chunk-final/scripts/final_chunk_reporter.py <chunk_file_name> '<evaluation json>'  # or pipe the JSON on stdin
```

**Output:** `results/<chunk>_evaluation.json` (verbatim, auto-created) + console `Evaluation saved: <path> (N jobs evaluated)`. Exit: `0` OK · `1` bad JSON/name · `2` missing arg.

Report the path and job count; on failure report the error, don't claim it was saved. No trigger for reading or evaluating chunks.
