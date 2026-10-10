---
name: job-write-chunk-final
description: Executes final_chunk_reporter.py to save the job-evaluator JSON report into results/ for one chunk file.
---

**Trigger:** orchestrator holds the chunk file name + the `job-evaluator` JSON report. Never save by hand.

```bash
python3 .opencode/skills/job-write-chunk-final/scripts/final_chunk_reporter.py <chunk_file_name> <<'JSON'
<evaluation json>
JSON
```

Pass the JSON on **stdin via a heredoc, never inline on the command line**: inline JSON holds `;`, `|`, quotes and braces that shell parsers split into fake sub-commands, which forces an approval prompt on every file. This is a single command (the heredoc adds no other sub-command).

**Output:** `results/<chunk>_evaluation.json` (verbatim, auto-created) + console `Evaluation saved: <path> (N jobs evaluated)`. Exit: `0` OK · `1` bad JSON/name · `2` missing arg.

Report the path and job count; on failure report the error, don't claim it was saved. No trigger for reading or evaluating chunks.

**Approvals cannot be declared in a `SKILL.md`:** no-ask is configured in `.vscode/settings.json` (`chat.tools.terminal.enableAutoApprove` + `chat.tools.terminal.autoApprove`) for VS Code and in `opencode.json` (`permission.bash`) for opencode.
