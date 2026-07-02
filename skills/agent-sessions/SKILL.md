---
name: agent-sessions
description: >
  Search, list, and resume AI agent sessions across Claude Code, Codex CLI, Gemini CLI,
  opencode, Hermes Agent, and Cline CLI.
  Use when the user asks to find a past conversation, search session history, resume a
  previous session, list recent agent activity, or check what was discussed in a prior
  session. Also use when asked to "find that conversation where I...", "resume my last
  codex session", "read latest convo", "read last messages", "what did I work on
  yesterday", "search my claude history for X", or gives an agent session id such as
  `ses_...`, a UUID, or a Cline id like `1782988565588_qqrxi`.
---

# Agent Sessions

Search and manage AI coding agent conversation history across Claude Code, Codex CLI, Gemini CLI, opencode, Hermes Agent, and Cline CLI.

$ARGUMENTS

## Tools Available

### CLI: `agent-sessions`

Located at `/Users/vladmdgolam/Play/radar/tools/agent-sessions`. A Python 3 script that reads session data from all supported agents.

```bash
# List all recent sessions (default 30)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions

# Filter by agent
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent claude
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent codex
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent gemini
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent opencode
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent hermes
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent cline

# Title/prompt search first (AND logic, case-insensitive; token-efficient)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --search "metal shader" --search-scope titles --limit 10

# Deep full-transcript search only when title/prompt search misses
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --search "metal shader" --search-scope full --limit 10

# Filter by project name or path
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --project radar

# Combine filters
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent claude --project aino --search "auth" --search-scope titles --limit 10

# Compact JSON output (for parsing; omits full transcript search_text)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --json --limit 10

# Include full transcript search_text only if you need client-side full-text search
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --json --include-search-text --limit 10

# Copy compact context for one or more sessions
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --context <session-id>
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --context <id-1> <id-2>

# Build a compact evidence pack for one or more sessions
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --pack <id-1> <id-2> --max-chars 5000

# Read bounded excerpts, optionally around a topic/query
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --read <id-1> <id-2> --query "logo rotation" --max-chars 5000

# Extract only the user's messages
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --read <id-1> <id-2> --role user --max-chars 5000

# Resume a Claude Code session
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --resume <session-id>

# Control result count; prefer small limits unless the user asks for a broad scan
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --limit 10
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
| opencode | `~/.local/share/opencode/opencode.db` | SQLite tables: `session`, `message`, `part`, `project` |
| Hermes Agent | `~/.hermes/state.db` | SQLite tables: `sessions`, `messages` |
| Cline CLI | `~/.cline/data/db/sessions.db` + `~/.cline/data/sessions/*/*.messages.json` | SQLite session index plus JSON message transcripts |

Project mapping for Gemini: `~/.gemini/projects.json` maps absolute paths to project names.

Cline sessions created with `cline --data-dir <path>` can be included by setting `AGENT_SESSIONS_CLINE_DATA_DIRS` to a colon-separated path list.

## Workflow

### First move: never spelunk by hand

If the user asks to read, continue, summarize, compare, or inspect an agent conversation, start with this CLI. Do not begin with broad `find ~`, manual SQLite queries, or copying live agent databases unless this CLI fails.

For explicit session ids, go straight to a pack:

```bash
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --pack <session-id> --max-chars 8000
```

For "latest conversation in this folder/project":

```bash
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --project "$PWD" --limit 5
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --pack <top-session-id> --max-chars 8000
```

For "last messages" or "where did it leave off", prefer `--pack` first; it is designed to include recent excerpts. Use `--read --query "topic"` for focused follow-up.

### Token-efficient retrieval ladder

Use the smallest useful output first:

1. Start with table output and a small limit: `--limit 10`.
2. Add `--agent` and/or `--project` whenever the user gave a clue.
3. Search titles/prompts first: `--search "query" --search-scope titles`.
4. Fall back to `--search-scope full` only if title search misses.
5. Use `--json` only when you need structured parsing; it is compact by default.
6. Do not use `--include-search-text` unless building a UI/client-side index or explicitly inspecting transcript text.
7. For handoff context, prefer `--context <id...>` instead of pasting full JSON.
8. When the user gives session refs and asks to compare, infer, summarize, or conclude from them, run `--pack <id...>` first.
9. If the pack is too broad or the user gave a topic, run `--read <id...> --query "topic"` for focused excerpts.
10. If the user asks for only their own prompts/messages, add `--role user`.

### Finding a past conversation

1. Run `agent-sessions` with appropriate filters to find the session
2. Use `--context <session-id>` if you need a compact handoff block
3. For Claude sessions: use `claude --resume <id>` to continue, or `claude-history` to browse
4. For viewing any agent's full conversation: open CCHV

### Reading provided session refs

If the user pastes blocks like:

```text
agent: codex
session id: 019ee05b-25d6-7153-83af-aee3a848e472
session title: ...
```

Extract the IDs and start with:

```bash
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --pack 019ee05b-25d6-7153-83af-aee3a848e472 <other-id> --max-chars 5000
```

Use the pack as evidence for cross-session conclusions. If the user asks about a specific topic, use:

```bash
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --read <id-1> <id-2> --query "topic terms" --max-chars 5000
```

If the user only wants their own messages/prompts:

```bash
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --read <id-1> <id-2> --role user --max-chars 5000
```

Avoid dumping full transcripts unless the user explicitly asks for exhaustive review.

### Answering "what did I work on?"

```bash
# Recent activity across all agents
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --limit 20

# Specific project
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --project bloom-metal --limit 20

# Specific agent
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --agent codex --limit 20
```

### Resuming a session

```bash
# Find the session
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --search "shader bug" --search-scope titles --agent claude --limit 10

# Resume it (Claude only)
python3 /Users/vladmdgolam/Play/radar/tools/agent-sessions --resume <session-id>
# This execs into: claude --resume <session-id>
```

## JSON Output Schema

When using `--json`, each session object has:

```json
{
  "agent": "claude|codex|gemini|opencode|hermes|cline",
  "session_id": "uuid",
  "prompt": "first user message (truncated to 120 chars)",
  "timestamp": "ISO 8601",
  "project_path": "/absolute/path/to/project",
  "project_name": "project-dir-name",
  "session_file": "/path/to/session/file"
}
```

`--json` omits `search_text` by default. Pass `--include-search-text` only for full-text indexing/search clients.

## Context Output

`--context <session-id>` emits compact pasteable context:

```text
agent: opencode
session id: n
session title: K
```

Multiple IDs emit a list with the same fields.

## Pack And Read Output

`--pack <id...>` emits one bounded evidence pack per session: metadata, brief, key user requests, and recent or query-relevant excerpts.

`--read <id...>` emits bounded transcript excerpts. For long transcripts it includes an initial orientation excerpt plus a `Recent Excerpts` tail so "last messages" are not crowded out. Add `--query "terms"` to return message windows around relevant matches instead of broad excerpts.

Add `--role user` to output/search only user messages, or `--role assistant` for assistant-only excerpts. Default is `--role all`.

Useful controls:

```bash
--role user            # only user messages
--max-chars 5000        # approximate excerpt budget per session
--last-turns 8          # recent messages included in packs/overflow reads
--context-messages 2    # messages before/after each query match
```
