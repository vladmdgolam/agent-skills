---
name: document-knowledge
description: >
  Distills everything Claude has learned in the current conversation into a structured
  Markdown knowledge document saved to disk. Use when the user wants to capture findings,
  decisions, architecture insights, or research from a session — phrases like "document
  what you know", "save your knowledge", "write up what we found", or "document this".
---

# Document Knowledge

Scan the current conversation, extract what was learned, and write it to a structured Markdown file.

## What to capture

- **Findings** — things discovered about the codebase, system, or domain
- **Decisions** — choices made and why
- **Architecture / structure** — how things fit together
- **Gotchas / surprises** — unexpected behavior, edge cases, constraints
- **Open questions** — unresolved issues worth flagging
- **Next steps** — actionable follow-ups if any were identified

Don't summarize the conversation itself — distill the *knowledge* it produced.

## Output

### Filename

Generate a slug from the main topic discussed:  
`knowledge-<topic>-<YYYY-MM-DD>.md`  
e.g. `knowledge-auth-middleware-2026-04-03.md`

If the user passed a name via `$ARGUMENTS`, use that as the filename (add `.md` if missing).

### Save location

Save to the current working directory unless the user specifies otherwise.

### Structure

```markdown
# [Topic] — Knowledge Document
_Generated: YYYY-MM-DD_

## Summary
One short paragraph: what this session was about and the key takeaway.

## Findings
- ...

## Decisions
| Decision | Rationale |
|----------|-----------|
| ...      | ...       |

## Architecture / Structure
(Include only if relevant — diagrams, file relationships, data flow, etc.)

## Gotchas & Constraints
- ...

## Open Questions
- [ ] ...

## Next Steps
- [ ] ...
```

Omit any section that has nothing to add — don't leave empty headings.

## Behavior

1. Review the full conversation context.
2. Extract and synthesize knowledge (not a transcript summary).
3. Write the file to disk using the Write tool.
4. Confirm to the user: filename + path + brief description of what was captured.

$ARGUMENTS
