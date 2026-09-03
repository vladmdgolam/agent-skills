# Data Sources Reference

## WakaTime

### Authentication & Config

The `wakatime_fetch.py` script reads the API key automatically from `~/.wakatime.cfg` — no manual setup needed. This file is created by any WakaTime IDE plugin (Cursor, VS Code, etc.) when first installed.

To inspect the config:
```bash
cat ~/.wakatime.cfg   # shows [settings] api_key = waka_xxxx...
```

To set the key manually: visit [wakatime.com/settings/api-key](https://wakatime.com/settings/api-key), copy your key, then paste it into `~/.wakatime.cfg` under `[settings]`:
```ini
[settings]
api_key = waka_xxxx...
```

### Multi-Project Discovery (Default Workflow)

WakaTime often tracks sub-directories as separate projects. A monorepo at `my-monorepo/` may have WakaTime projects named `my-monorepo`, `frontend`, `api-service`, `shared-utils`, etc. Querying only the root project name misses significant hours.

**Default approach — always do this:**

1. Run `wakatime_fetch.py` **without** `--project` first to get the full project list:
   ```bash
   python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02
   # Returns: { "projects": [{"project": "my-monorepo", "hours": 9.2}, {"project": "frontend", "hours": 5.0}, ...] }
   ```

2. Filter the `projects` list for names matching the root directory basename OR any sub-repo/sub-directory basename.

3. Fetch intervals for **each** matching project name:
   ```bash
   python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project my-monorepo
   python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project frontend
   python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project api-service
   ```

4. Combine all intervals into a single list for reconciliation. The merge algorithm handles overlaps.

**Why this matters:** In practice, querying only the root project name captured 9h out of 26.5h total — missing 66% of actual WakaTime data that was tracked under sub-directory names.

### Behavior & Limitations

WakaTime tracks active keystrokes only — it always produces lower hour counts than the git estimate. When a developer does heavy Claude Code or Codex usage (prompting, reviewing AI output, researching), those intervals are not captured by WakaTime because no IDE keystrokes are generated. This creates a large gap between WakaTime hours and actual working effort.

WakaTime's `/durations` API returns per-file intervals pre-merged with a 60-second tolerance. These are already `[start_epoch, end_epoch]` pairs in UTC epoch floats, ready for the reconciliation step.

---

## Claude Code Data Sources

`claude_messages.py` reads from two sources and merges them:

### Source 1: `~/.claude/history.jsonl` (primary)

One entry per submitted prompt. Relevant fields:
- `project`: absolute path string of the project directory
- `timestamp`: Unix timestamp in **milliseconds**

Filter by: `project == abs_path`

### Source 2: `~/.claude/projects/<encoded>/*.jsonl` (session files)

These are per-session conversation files. Each entry has:
- `cwd`: absolute path string of the project directory
- `type`: `"user"` or `"assistant"`
- `timestamp`: ISO 8601 string

Filter for prompt counting: `type == "user"` AND `message.content` is NOT a `list[tool_result]` (those are tool outputs, not user prompts).

**Use these for sessions that predate `history.jsonl`** — older Claude Code versions did not write to history.

**Encoded dir name format:** `/Users/foo/bar` → `-Users-foo-bar` (leading `/` becomes `-`, all other `/` become `-`).

### Matching Preference

Always prefer `--project-path /abs/path` over `--filter name` for accurate matching. The `--filter` flag does a substring match on the project name and may pick up unrelated projects with similar names.

### Output

Two timestamp arrays, both UTC epoch floats:
- `timestamps` — user prompts only (same filter as above). Use for prompt-count metrics.
- `activity_timestamps` — **every** `type == "user"` or `type == "assistant"` entry, including `tool_result` entries and assistant replies. Use this one for session/interval reconciliation, not `timestamps`.

Why the split matters: a `tool_result` entry fires every time a tool call completes, and `assistant` entries fire on every reply/reasoning step — both are real evidence the agent was actively working, even though neither is a "prompt." A session with one prompt at 14:00 and the next at 14:45 looks like a 0-duration point using `timestamps` alone; `activity_timestamps` will usually contain dozens of entries across that same 45 minutes if the agent was actually running tools the whole time. Confirmed on a real project (Aug 2026): a single isolated Codex prompt with the next prompt 50 minutes later turned out to have 1,343 tool-call/reasoning events in between, with the largest actual idle gap being 36 seconds — i.e. the "0-duration" session was actually ~50 minutes of continuous work.

Also includes `alternate_paths` when the provided path yields 0 results (see [folder-move-detection.md](./folder-move-detection.md)).

---

## Codex CLI Data Sources

`codex_messages.py` reads from `~/.codex/sessions/YYYY/MM/DD/rollup-*.jsonl`.

### File Structure

Each `.jsonl` file contains newline-delimited JSON entries of different types:

| Entry type | Relevant fields | Purpose |
|---|---|---|
| `session_meta` | `payload.cwd`, `payload.id` | Project directory + session UUID — **can recur mid-file**: long-lived/resumed Codex sessions carry on for days and may re-emit `session_meta`, sometimes for a different `cwd`. Don't assume it's set once at the top of the file. |
| `event_msg` with `payload.type == "user_message"` | `payload.message` (string), `payload.text_elements`, `payload.images` | Actual user prompts — this is `timestamps` |
| `response_item` (`reasoning`, `custom_tool_call`, `custom_tool_call_output`, `message`) | `timestamp` | Agent execution steps — tool calls, patches, replies |
| `event_msg` with `payload.type` in `agent_message`, `patch_apply_end`, `token_count`, etc. | `timestamp` | More agent-execution markers |
| `turn_context` | `cwd`, `model` | Turn boundaries |

**All of the above (any type, as long as `cwd` matches) count as activity — this is `activity_timestamps`.** A single rollout file can be extremely dense: one real-world session produced 74k+ timestamped events across ~6 weeks of on-and-off use.

### Matching

Filter by `session_meta.payload.cwd == abs_path` (or the alternate path if a folder move is detected). Because `session_meta` can recur with a different `cwd` inside one file (see above), the scanner tracks `cwd` continuously through the file rather than checking it once — a file that starts on an unrelated project and later switches to the target `cwd` (e.g. after a `codex resume` in a different directory) is still picked up correctly for the matching stretch.

### Output

Same split as `claude_messages.py`:
- `timestamps` — `user_message` events only. Prompt-count metric.
- `activity_timestamps` — every timestamped line while `cwd` matches, regardless of type. Reconciliation input.

Plus `alternate_paths` if applicable.

---

## Cursor IDE Data Sources

`cursor_messages.py` reads from Cursor's SQLite databases (`.vscdb` files) using two sources.

### Source 1: Global Storage `cursorDiskKV` (primary)

Location (macOS): `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
Location (Windows): `%APPDATA%/Cursor/User/globalStorage/state.vscdb`
Location (Linux): `~/.config/Cursor/User/globalStorage/state.vscdb`

The `cursorDiskKV` table contains key-value pairs:

| Key pattern | Value contents | Purpose |
|---|---|---|
| `composerData:{sessionId}` | JSON with `workspaceUri`, `createdAt`, `updatedAt` | Session metadata — `workspaceUri` maps to project path |
| `bubbleId:{sessionId}:{messageId}` | JSON with `type`, `timingInfo`, `createdAt`, etc. | Per-message data — `type=1` = user message |

**Timestamp extraction priority chain** (per bubble):
1. `createdAt` — ISO 8601 string (new format, >= Sept 2025)
2. `timingInfo.clientStartTime` — Unix ms
3. `timingInfo.clientRpcSendTime` — Unix ms (old format, assistant only)
4. `timingInfo.clientSettleTime` — Unix ms (old format)
5. `timingInfo.clientEndTime` — Unix ms
6. `timestamp` — Unix ms (legacy plain field)

**Project matching:** The `workspaceUri` field in `composerData:{sessionId}` is a `file://` URI (e.g., `file:///Users/alice/code/my-project`). The script converts this to an absolute path and compares against `--project-path`.

### Source 2: Workspace Storage `ItemTable` (fallback)

Location (macOS): `~/Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb`
Location (Windows): `%APPDATA%/Cursor/User/workspaceStorage/*/state.vscdb`
Location (Linux): `~/.config/Cursor/User/workspaceStorage/*/state.vscdb`

Each workspace directory also contains a `workspace.json` file with a `folder` field (a `file://` URI) that maps the workspace to its project directory.

The `ItemTable` key-value store contains:

| Key | Value contents | Granularity |
|---|---|---|
| `composer.composerData` | JSON with `allComposers` array, each having `composerId`, `createdAt`, `lastUpdatedAt` | Session-level only |
| `workbench.panel.aichat.view.aichat.chatdata` | Legacy chat format with `chatSessions` → `messages` (has `role`, `timestamp`) | Per-message |
| `workbench.panel.chat.view.chat.chatdata` | Legacy chat format (alternate key, same structure) | Per-message |

**Use these for**: older Cursor versions that don't have `cursorDiskKV` in global storage, or when the global storage database is unavailable.

### Deduplication

The script collects from global storage first, then falls back to workspace storage, deduplicating by rounded epoch timestamp (same approach as `claude_messages.py`).

### Output

Same split as `claude_messages.py` and `codex_messages.py`:
- `timestamps` — `type=1` (user) bubbles / `role=="user"` legacy messages only. Prompt-count metric.
- `activity_timestamps` — every bubble/message regardless of type or role. Reconciliation input. (`composer.composerData`'s `createdAt`/`lastUpdatedAt` have no role field, so they count toward both.)

Plus `daily` counts, `sessions_found`, `alternate_paths` for folder-move detection, and a `sources` breakdown showing how many messages came from `global_storage` vs `workspace_storage`.
