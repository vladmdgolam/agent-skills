# Folder Move Detection Reference

## What It Is

`claude_messages.py`, `codex_messages.py`, and `cursor_messages.py` all include automatic detection of cases where a project directory has been renamed or moved. When a script finds 0 results for the provided path, it scans all known history for project names that partially match the provided path and returns candidate old locations in an `alternate_paths` field.

This is important because:
- Developers frequently rename or reorganize project directories.
- Claude Code, Codex, and Cursor sessions are indexed by absolute path, so a moved project appears as a completely different project in the history.
- Without this detection, moved projects would silently show 0 AI session hours.

---

## How Detection Works

### Claude Code (`claude_messages.py`)

Two scans are performed:

1. **`history.jsonl` scan:** All `project` field values are collected. Any path where the final directory component matches the queried project name (case-insensitive) is treated as a candidate.

2. **Session file `cwd` scan:** All `~/.claude/projects/<encoded>/` directories are checked. The `cwd` from the first `type=="user"` entry in each session file is collected. Same name-match logic applies.

The union of both scans, excluding the originally queried path, is returned as `alternate_paths`.

### Codex CLI (`codex_messages.py`)

All `~/.codex/sessions/YYYY/MM/DD/rollup-*.jsonl` files are scanned. The `payload.cwd` from each `session_meta` entry is collected. Any path where the final directory component matches the queried project name is treated as a candidate and returned in `alternate_paths`.

### Cursor IDE (`cursor_messages.py`)

Two scans are performed:

1. **Workspace storage scan:** All `workspace.json` files under the platform-specific Cursor `workspaceStorage/*/` directory are read. The `folder` field (a `file://` URI) is converted to an absolute path. Any path where the final directory component matches the queried project name is treated as a candidate.

2. **Global storage scan:** The `cursorDiskKV` table in the platform-specific Cursor `globalStorage/state.vscdb` is queried for `composerData:*` entries. The `workspaceUri` from each entry is compared using the same name-match logic.

Platform-specific Cursor base paths: macOS: `~/Library/Application Support/Cursor/User/`, Windows: `%APPDATA%/Cursor/User/`, Linux: `~/.config/Cursor/User/`.

The union of both scans, excluding the originally queried path, is returned as `alternate_paths`.

---

## What the `alternate_paths` Output Looks Like

```json
{
  "timestamps": [],
  "prompt_count": 0,
  "alternate_paths": [
    "/Users/foo/archive/my-project",
    "/Users/foo/old-name"
  ]
}
```

A non-empty `alternate_paths` with an empty `timestamps` list is the trigger condition.

---

## Workflow When `alternate_paths` Is Present

When `claude_messages.py`, `codex_messages.py`, or `cursor_messages.py` return 0 results and `alternate_paths` is non-empty:

1. **Pause and ask the user:**
   > "No Claude/Codex history found at `/current/path`, but found sessions for `project-name` at `/old/path`. Was this project moved? Should I include that history too?"

2. **If the user confirms:** Re-run the script with `--project-path /old/path`.

3. **Merge the results:** Combine `timestamps` arrays from both the new path run and the old path run. Sort the merged array before passing to the reconciliation step.

   ```python
   merged_timestamps = sorted(
       new_path_result["timestamps"] + old_path_result["timestamps"]
   )
   ```

4. **Log both paths** in the Markdown report's Methodology section so the user understands what was included.

---

## Edge Cases

| Situation | Handling |
|---|---|
| Project moved multiple times | `alternate_paths` may list multiple old locations. Ask user which to include; merge all confirmed ones. |
| Two different projects happen to share a directory name | Present all candidates to the user and let them decide which (if any) to include. |
| `alternate_paths` is empty and 0 results | No history exists for this tool. Note it in the report but do not block generation. |
| Current path has some sessions, old path has more | Merge both regardless; the reconciliation deduplication handles overlapping timestamps. |
