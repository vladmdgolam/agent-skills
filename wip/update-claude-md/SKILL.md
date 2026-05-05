---
name: update-claude-md
description: >
  Appends a thought, instruction, or note to the nearest CLAUDE.md in the current
  project. Use when the user wants to record a preference, rule, or context for future
  Claude sessions — phrases like "add this to claude.md", "remember this for next time",
  "note to claude", or "update claude.md".
---

# Update CLAUDE.md

Append the user's note to the nearest `CLAUDE.md` without disturbing existing content.

## Arguments

`$ARGUMENTS` — the text to add. If empty, ask the user what they want to add.

## Finding the right CLAUDE.md

1. Look for `CLAUDE.md` in the current working directory.
2. Walk up parent directories until one is found or the repo root is reached.
3. If none exists, ask the user before creating one.

## How to append

- Add the content under an appropriate existing heading if one fits, or create a new one.
- Keep the user's wording — don't rewrite or over-format.
- Separate new content from existing content with a blank line.
- Never delete or restructure existing content.

### Minimal example

User runs: `/update-claude-md always use pnpm, not npm`

Before:
```markdown
# My Project

Use TypeScript strict mode.
```

After:
```markdown
# My Project

Use TypeScript strict mode.

Always use pnpm, not npm.
```

### With a matching section

If the file already has a relevant section (e.g. `## Package Manager`), append under it rather than creating a duplicate heading.

## Behavior

1. Find the nearest `CLAUDE.md`.
2. Read it.
3. Determine the best place to insert the note.
4. Edit the file — append cleanly.
5. Confirm to the user: which file was updated + the line(s) added.

$ARGUMENTS
