---
name: agent-sessions
description: >
  Search, list, and resume AI agent sessions across Claude Code, Codex CLI, and Gemini CLI.
  Use when the user asks to find a past conversation, search session history, resume a
  previous session, list recent agent activity, or check what was discussed in a prior
  session. Also use when asked to "find that conversation where I...", "resume my last
  codex session", "what did I work on yesterday", or "search my claude history for X".
---

# Agent Sessions

Search and manage AI coding agent conversation history across Claude Code, Codex CLI, and Gemini CLI.

$ARGUMENTS

## Tools Available

### CLI: `agent-sessions`

Located at `/Users/vladmdgolam/Play/radar/tools/agent-sessions`. A Python 3 script that reads session data from all three agents.

```bash
# List all recent sessions (default 30)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions

# Filter by agent
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent claude
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent codex
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent gemini

# Search in prompts (AND logic, case-insensitive)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --search "metal shader"

# Filter by project name or path
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --project radar

# Combine filters
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent claude --project aino --search "auth"

# JSON output (for parsing)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --json --limit 10

# Resume a Claude Code session
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --resume <session-id>

# Control result count
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --limit 50
```

### TUI: `claude-history`

Located at `~/.local/bin/claude-history`. Rust-based fuzzy search TUI for Claude Code sessions only.

```bash
# Interactive fuzzy search across all Claude sessions
claude-history

# Scoped to current project
claude-history --local

# View a specific session file
claude-history /path/to/session.jsonl

# Resume selected session
claude-history --resume

# Fork from a past session
claude-history --fork-session
```

### GUI: Claude Code History Viewer (CCHV)

Desktop app at `/Applications/Claude Code History Viewer.app`. Supports 7 agents (Claude, Codex, Gemini, Cursor, Cline, Aider, OpenCode) with analytics, cost tracking, and full-text search.

```bash
open "/Applications/Claude Code History Viewer.app"
```

## Data Sources

| Agent | Location | Format |
|-------|----------|--------|
| Claude Code | `~/.claude/projects/<encoded>/*.jsonl` | JSONL with `type`, `message`, `cwd`, `sessionId`, `timestamp` |
| Codex CLI | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | JSONL with `session_meta` (payload.id, payload.cwd) and `response_item` entries |
| Gemini CLI | `~/.gemini/tmp/*/chats/session-*.json` | JSON with `sessionId`, `startTime`, `messages[]` array |

Project mapping for Gemini: `~/.gemini/projects.json` maps absolute paths to project names.

## Workflow

### Finding a past conversation

1. Run `agent-sessions` with appropriate filters to find the session
2. Note the session ID from the output
3. For Claude sessions: use `claude --resume <id>` to continue, or `claude-history` to browse
4. For viewing any agent's full conversation: open CCHV

### Answering "what did I work on?"

```bash
# Yesterday's activity across all agents
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --limit 50 | head -20

# Specific project
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --project bloom-metal

# Specific agent
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent codex --limit 20
```

### Resuming a session

```bash
# Find the session
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --search "shader bug" --agent claude --json

# Resume it (Claude only)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --resume <session-id>
# This execs into: claude --resume <session-id>
```

## JSON Output Schema

When using `--json`, each session object has:

```json
{
  "agent": "claude|codex|gemini",
  "session_id": "uuid",
  "prompt": "first user message (truncated to 120 chars)",
  "timestamp": "ISO 8601",
  "project_path": "/absolute/path/to/project",
  "project_name": "project-dir-name",
  "session_file": "/path/to/session/file"
}
```
