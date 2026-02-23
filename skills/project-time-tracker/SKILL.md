---
name: project-time-tracker
description: >
  Analyze and visualize time spent on software projects by combining data from multiple
  sources: WakaTime coding time, git commit session detection, Claude Code usage, and
  Codex CLI usage. Produces both an interactive HTML dashboard (dark-themed, Chart.js)
  and a Markdown report with ASCII charts. Use when the user asks to: analyze work hours,
  calculate time spent on a project, generate a work hours report, visualize coding
  activity, create a project time breakdown, or summarize development effort across date ranges.
---

# Project Time Tracker

Combines four data sources → reconciles → produces HTML dashboard + Markdown report.

## Scripts

All scripts live in `scripts/` next to this SKILL.md. Run them with `python3`:

| Script | Purpose | Key flags |
|--------|---------|-----------|
| `git_sessions.py` | Parse git history → sessions → hours | `<repo> --since YYYY-MM-DD --until YYYY-MM-DD` |
| `wakatime_fetch.py` | WakaTime API → daily hours, filtered to project | `--start YYYY-MM-DD --end YYYY-MM-DD --project name` |
| `claude_messages.py` | Claude Code user prompts per day + timestamps | `--project-path /abs/path` or `--filter name` |
| `codex_messages.py` | Codex CLI user prompts per day + timestamps | `--project-path /abs/path` or `--filter name` |

## Workflow

### 1. Determine scope

Ask for or infer:
- Project directory/directories (git repos)
- Date range (first commit → last commit, or user-specified)
- Output location for HTML + markdown files

### 2. Extract data

Run all four scripts. For multi-repo projects, run `git_sessions.py` on each repo separately then merge results.

```bash
# Git sessions (run per repo)
python3 git_sessions.py /path/to/repo --since 2026-01-15 --until 2026-02-02

# WakaTime — always pass --project to get per-project hours (not all-account)
python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project my-project

# Claude Code — prefer --project-path for exact match
python3 claude_messages.py --project-path /abs/path/to/repo

# Codex CLI — same interface as claude_messages.py
python3 codex_messages.py --project-path /abs/path/to/repo
```

**Folder move detection:** If `claude_messages.py` or `codex_messages.py` return 0 results, check the output for `alternate_paths`. If present, ask the user:
> "No Claude/Codex history found at `/current/path`, but found sessions for `project-name` at `/old/path`. Was this project moved? Should I include that history too?"

If confirmed, re-run with `--project-path /old/path` and merge timestamps from both paths.

### 3. Reconcile hours

**Merged total = best estimate** (git ∪ Claude ∪ Codex ∪ WakaTime intervals, no double-counting):

```python
GAP_H = 1.5  # hours between events → new session

# 1. Collect intervals from git (start/end per session, converted to UTC epoch)
# 2. Collect intervals from Claude timestamps (detect sessions via gap threshold)
# 3. Collect intervals from Codex timestamps (same gap threshold)
# 4. Collect intervals from WakaTime "intervals" field (already [start, end] pairs in UTC epoch)
# 5. Combine all intervals into one list, sort by start
# 6. Merge overlapping/adjacent intervals:
#    for each interval, if next.start - cur.end <= GAP_H * 3600 → extend current
# 7. For each merged interval: est = max(end - start + 0.5h, 0.5h)
# 8. total = Σ est

# Data formats (all UTC epoch floats):
# - git_sessions.py: convert local times using timezone offset from git log
# - claude_messages.py "timestamps": point events → detect sessions via gap
# - codex_messages.py "timestamps": point events → detect sessions via gap
# - wakatime_fetch.py "intervals": already [start_epoch, end_epoch] pairs
#   (fetched from /durations API, per-file intervals pre-merged with 60s tolerance)
```

Why merge matters: AI agent prompts (Claude/Codex) often appear minutes before/after git commits in the same work session. WakaTime captures IDE keystrokes that may fall between commits. A user might research with Claude, write code (WakaTime), then commit (git) — all one session. Union of all four sources captures the true session boundaries without double-counting.

- The merged total replaces "git-only" as the primary estimate
- WakaTime hours shown for reference (active keystrokes only, always lower)

### 4. Generate HTML dashboard

Write a single-file HTML with inline Chart.js (CDN). Dark theme (`#0a0a0a` bg, `#1a1a1a` cards).

Required sections:
1. **Stat cards** — Merged total (git∪claude∪codex∪waka), Git estimate, WakaTime, Sessions, Commits, Claude prompts, Codex prompts
2. **Daily activity chart** — Overlapping bars (git + WakaTime + merged) + AI prompts line on secondary axis
3. **Gantt timeline** — UTC horizontal bars; git, Claude, and Codex as separate colored datasets on same chart (separate swimlane rows when they overlap on same day)
4. **Data table** — Session | Time (UTC) | Active | Est. | WakaTime | Claude | Codex | Commits

Chart.js essentials:
```javascript
Chart.defaults.color = '#888';
Chart.defaults.borderColor = '#2a2a2a';
// Overlapping bars: same barPercentage/categoryPercentage on both datasets, different opacity
// Mixed chart: type:'bar' on container, each dataset has its own type + yAxisID
// Gantt floating bars: data: [[startH, endH]], indexAxis: 'y'
// Claude as line on secondary axis:
{
  type: 'line',
  yAxisID: 'yClaude',
  // right-side axis, max ~100, different color
}
// All charts: responsive: true, maintainAspectRatio: false
```

Save as `<project-dir>/work-hours-analysis.html`.

### 5. Generate Markdown report

```markdown
# [Project] - Work Hours Analysis
## Summary
**Estimated Total Working Hours: Xh** (based on commit timing analysis)

| Date | Sessions | Time Range | Git Est. | WakaTime | Commits | Project |
...

## Timeline
- Start: [date], End: [date], Duration: N days

## Per-Project Breakdown
[sub-project sections with commit/session counts]

## Charts
### Daily Activity (ASCII)
Jan 15  ██░░░░░░░░░░░░░░░░░░  0.5h
...
### Project Distribution
project-a  ████████████████████  45%  (~18h)
...

## Methodology
- Session Detection: commits within 1.5h gap = same session
- Hour Estimate: Σ(session_duration + 0.5h buffer), min 0.5h/session
- Why Git > WakaTime: WakaTime only tracks active IDE typing; git includes thinking/research/AI prompting
```

ASCII bar: `blocks = round(hours / max_hours * 20)`, `█` filled, `░` empty, 20 cols wide.

Save as `<project-dir>/total_hours.md`.

## Notes

**WakaTime auth:** The script reads the API key automatically from `~/.wakatime.cfg` — no manual setup needed. This file is created by any WakaTime IDE plugin (Cursor, VS Code, etc.) when first installed. To inspect it:
```bash
cat ~/.wakatime.cfg   # shows [settings] api_key = waka_xxxx...
```
To get your key manually: [wakatime.com/settings/api-key](https://wakatime.com/settings/api-key). Paste it into `~/.wakatime.cfg` under `[settings]` → `api_key = waka_xxxx`.

WakaTime tracks active keystrokes only — always lower than git estimate. Heavy Claude Code usage means large gap between WakaTime and actual effort.

**Codex CLI data source:** `codex_messages.py` reads `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Each file has:
- `session_meta` (first entry): `payload.cwd` = project directory, `payload.id` = session UUID
- `event_msg` with `payload.type == "user_message"`: actual user prompts (has `payload.message` string + `images`/`text_elements` keys)
- `event_msg` with `payload.type == "agent_message"`: assistant responses
- `turn_context`: turn boundaries with cwd, model, etc.
Output includes `timestamps` (UTC epoch floats) for merged session computation. Also includes folder-move detection via `alternate_paths` when no sessions match.

**Claude Code data sources:** `claude_messages.py` uses two sources:
1. `~/.claude/history.jsonl` — primary; one entry per submitted prompt with `project` (absolute path) and `timestamp` (ms). Filter by `project == abs_path`.
2. `~/.claude/projects/<encoded>/*.jsonl` — session files; each entry has `cwd` (absolute path), `type` ("user"/"assistant"), `timestamp` (ISO). Use for sessions that predate history.jsonl. Filter `type=="user"` and exclude `message.content` that is a `list[tool_result]` (those are tool outputs, not prompts).
Encoded dir name format: `/Users/foo/bar` → `-Users-foo-bar`. Always prefer `--project-path` over `--filter` for accurate matching.

**WakaTime always use `--project`:** Without `--project`, the script returns all-account daily totals which mix multiple projects worked on the same days. Always pass `--project <wakatime-project-name>` to get per-project data.

**Folder move detection:** Both `claude_messages.py` and `codex_messages.py` check for matching project names at different paths when they find 0 results. The output `alternate_paths` field lists candidate old locations. Claude detection scans `history.jsonl` (exact paths) and session file `cwd` fields. Codex detection scans all `session_meta.cwd` fields. If alternates are found, ask the user to confirm, then re-run with the old path and merge all timestamps.

**Multi-repo projects:** Merge session arrays from multiple `git_sessions.py` runs, re-sort by date, recompute daily totals and grand total.
