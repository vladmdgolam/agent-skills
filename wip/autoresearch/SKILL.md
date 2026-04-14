---
name: autoresearch
description: >
  Automatically research and reverse-engineer a technique, visual effect, algorithm,
  or codebase. Given a reference (image, video, URL, library name, description, or
  existing code), Claude researches how it works, reverse-engineers the approach, and
  produces a structured findings document. Use when you want to understand "how is this
  made", "reverse engineer this effect", "research this technique", or "figure out how
  X works so I can implement it".
---

# Autoresearch

Given a reference target, automatically research it and produce a reverse-engineering
report with implementation guidance.

## Input (via $ARGUMENTS or conversation context)

The target can be any of:
- A visual reference — image path, screenshot, video frame
- A URL — article, repo, shader toy link, paper
- A library or tool name — "how does pixelmatch work"
- A description — "that liquid metal refraction effect"
- An existing codebase or file — reverse-engineer undocumented code
- A combination of the above

## Research phases

### 1. Identify the target
Clarify what's being researched: a visual technique, an algorithm, an architecture, a
library internals. If ambiguous, ask one focused question before proceeding.

### 2. Collect evidence
- **Visual refs**: analyze images/screenshots with vision tools — describe what's happening geometrically, mathematically, temporally
- **Code refs**: read source files — identify core algorithms, data structures, key functions
- **Web research**: search for papers, shader implementations, blog posts, prior art
- **Existing project context**: scan `refs/`, `docs/`, `reference/`, `CLAUDE.md`, `README.md` in the working directory for related material already gathered

### 3. Reverse engineer
Break the technique into layers:
- What is the high-level effect or behavior?
- What mathematical/algorithmic primitives drive it?
- What are the key parameters and how do they interact?
- What are the non-obvious parts (the "tricks")?
- What constraints apply (platform, performance, compatibility)?

### 4. Implementation map
Translate findings into actionable implementation notes for the current project:
- Language/platform fit (GLSL ES 1.00, Metal MSL, TypeScript, etc.)
- Suggested implementation order (scaffold → core → details)
- Known pitfalls from the research

## Output

Save a Markdown report to `refs/research-<topic>-<YYYY-MM-DD>.md` if a `refs/` folder
exists, otherwise to the current directory as `research-<topic>-<YYYY-MM-DD>.md`.

```markdown
# [Topic] — Autoresearch
_Date: YYYY-MM-DD | Source: [reference used]_

## What it is
One paragraph: the effect/technique/system in plain terms.

## How it works
### Core mechanism
### Key mathematical primitives
### Parameters & controls
### The non-obvious parts

## Prior art & references
- [link or file] — what it contributes

## Implementation map
### Platform notes
### Suggested approach
### Pitfalls

## Open questions
- [ ] ...
```

## Behavior

1. Identify the target from `$ARGUMENTS` or conversation context.
2. Run all relevant research phases in parallel where possible.
3. Synthesize into the report structure above — omit empty sections.
4. Save the file and confirm path to user.
5. Optionally: if the project has a `todo.md` or `tasks.md`, offer to append
   a follow-up implementation task.

$ARGUMENTS
