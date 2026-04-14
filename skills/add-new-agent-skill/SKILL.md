---
name: add-new-agent-skill
description: "Create a new agent skill in the vladmdgolam/agent-skills repo with proper structure, frontmatter, README entry, and global install. Use when the user wants to add a skill, create a skill, build a new skill, or says 'new skill'. Follows the building-skills-guide patterns."
---

# Add New Agent Skill

Create a new skill in this repo end-to-end: design, write, register, install.

$ARGUMENTS

# Workflow

## Step 1: Define the skill

Before writing anything, establish these with the user:

1. **Name** — kebab-case, descriptive (e.g. `cinema4d-mcp`, `time-lens`, `pdf-look-scanned`)
2. **Category** — which type:
   - **MCP Enhancement** — coordinates MCP tools with domain expertise (e.g. `cinema4d-mcp`, `figma-context-mcp`)
   - **Workflow Automation** — multi-step process with validation gates (e.g. `time-lens`, `pdf-look-scanned`)
   - **Knowledge / Best Practices** — packaged expertise for a domain (e.g. `poke`, `visual-feedback-loop`)
3. **2-3 concrete use cases** — what the user accomplishes, what steps are needed, what tools are involved
4. **Trigger phrases** — exact things a user would say that should activate this skill

If the user already described what they want, extract these from context. Don't ask redundant questions.

## Step 2: Create the skill folder and SKILL.md

Create `skills/<name>/SKILL.md` with this structure:

```markdown
---
name: <name>
description: "<What it does>. <When to use — include trigger phrases>."
---

# <Skill Name>

<One-line summary of purpose>

$ARGUMENTS

# Instructions

## Step 1: <First action>
<Clear, actionable instructions>

## Step 2: <Next action>
...

# Examples

## Example 1: <Scenario>
**User says:** "..."
**Actions:**
1. ...
2. ...
**Result:** ...

# Troubleshooting

## <Common issue>
**Cause:** ...
**Fix:** ...
```

### SKILL.md quality checklist

- [ ] Frontmatter `name` matches folder name exactly
- [ ] `description` is under 1024 chars, has BOTH what + when, includes trigger phrases, no `<>` brackets
- [ ] Body uses `#` headings (not `##` at top level — skills load as full documents)
- [ ] Includes `$ARGUMENTS` if the skill accepts user input after the slash command
- [ ] At least 1 worked example with user prompt → actions → result
- [ ] Instructions are actionable (do X) not descriptive (X is a thing that...)
- [ ] No README.md inside the skill folder (all docs go in SKILL.md or references/)

### When to add supporting directories

- `references/` — deep-dive docs, error tables, API references (keeps SKILL.md focused)
- `scripts/` — executable Python/Bash scripts the skill invokes
- `assets/` — templates, fonts, config files

Only create these if the skill genuinely needs them. Most skills under 400 lines need only SKILL.md.

## Step 3: Update README.md

Add an entry to `README.md` under `## Available Skills` following the existing pattern:

```markdown
### <emoji> <name>

<One-line description matching the SKILL.md frontmatter.>

**Use when:**
- <trigger scenario 1>
- <trigger scenario 2>
- ...

**Covers:**
- <key capability 1>
- <key capability 2>
- ...
```

Choose an emoji that fits the skill's domain. Place the entry in logical order among existing skills.

## Step 4: Install globally

Run:

```bash
~/.nvm/versions/node/v22.21.1/bin/npx skills add vladmdgolam/agent-skills --skill <name> -g -a claude-code -y
```

If this fails, check:
- SKILL.md exists at exact path `skills/<name>/SKILL.md`
- Frontmatter YAML is valid (no tabs, proper quoting)
- Name in frontmatter matches folder name

## Step 5: Verify

1. Check the skill appears in `~/.nvm/versions/node/v22.21.1/bin/npx skills list`
2. Test triggering: start a new Claude Code conversation and say one of the trigger phrases — confirm the skill loads
3. Walk through one example end-to-end

# Design Principles

These come from `references/building-skills-guide.md`:

- **Progressive disclosure** — frontmatter triggers loading; SKILL.md body has instructions; `references/` has deep dives
- **Composability** — skills should work alongside other skills, not conflict
- **Portability** — skills work in Claude.ai, Claude Code, and API identically
- **Action over explanation** — tell the agent what to DO, not what things ARE

# Common Mistakes

| Mistake | Fix |
|---------|-----|
| Description too vague ("helps with X") | Add specific trigger phrases and outcomes |
| Description has `<>` brackets | Remove XML-like brackets, use quotes or backticks |
| Description > 1024 chars | Trim — move details to SKILL.md body |
| Skill folder uses spaces or camelCase | Use kebab-case only |
| SKILL.md named differently (skill.md, Skill.md) | Must be exactly `SKILL.md` |
| Instructions are passive ("X can be done") | Use imperative ("Do X") |
| No examples | Add at least 1 worked example |
| Too many things in SKILL.md | Move reference material to `references/` |
