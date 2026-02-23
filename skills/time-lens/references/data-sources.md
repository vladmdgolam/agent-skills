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

### Always Pass `--project`

Without `--project`, the script returns all-account daily totals, which mix multiple projects worked on the same days. Always pass `--project <wakatime-project-name>` to get per-project data.

Example:
```bash
python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project my-project
```

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

Filter: `type == "user"` AND `message.content` is NOT a `list[tool_result]` (those are tool outputs, not user prompts).

**Use these for sessions that predate `history.jsonl`** — older Claude Code versions did not write to history.

**Encoded dir name format:** `/Users/foo/bar` → `-Users-foo-bar` (leading `/` becomes `-`, all other `/` become `-`).

### Matching Preference

Always prefer `--project-path /abs/path` over `--filter name` for accurate matching. The `--filter` flag does a substring match on the project name and may pick up unrelated projects with similar names.

### Output

The script outputs a `timestamps` array of UTC epoch floats (point events). These are used in the reconciliation step to detect sessions via the gap threshold. Also includes `alternate_paths` when the provided path yields 0 results (see [folder-move-detection.md](./folder-move-detection.md)).

---

## Codex CLI Data Sources

`codex_messages.py` reads from `~/.codex/sessions/YYYY/MM/DD/rollup-*.jsonl`.

### File Structure

Each `.jsonl` file contains newline-delimited JSON entries of different types:

| Entry type | Relevant fields | Purpose |
|---|---|---|
| `session_meta` (first entry) | `payload.cwd`, `payload.id` | Project directory + session UUID |
| `event_msg` with `payload.type == "user_message"` | `payload.message` (string), `payload.text_elements`, `payload.images` | Actual user prompts |
| `event_msg` with `payload.type == "agent_message"` | — | Assistant responses (skip) |
| `turn_context` | `cwd`, `model` | Turn boundaries |

### Matching

Filter by `session_meta.payload.cwd == abs_path` (or the alternate path if a folder move is detected).

### Output

Same as `claude_messages.py`: a `timestamps` array of UTC epoch floats plus `alternate_paths` if applicable.
