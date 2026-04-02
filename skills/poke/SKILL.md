---
name: poke
description: "Resume the current task immediately and keep momentum, with optional extra focus from the user. Use when the user wants a nudge like 'poke', 'keep going', 'continue', or 'resume what you were doing' without changing the task."
---

# Poke

Treat this skill as a gentle nudge to keep moving on the current task.

If the user passed extra text with `/poke`, treat it as an additional focus area or reminder:

$ARGUMENTS

## Behavior

1. Re-anchor on the latest user goal and the current repo or session state.
2. If there is unfinished work, choose the next concrete step and do it now.
3. Prefer action over explanation: inspect files, run commands, edit code, and verify results.
4. Keep progress updates brief and useful instead of repeating a long plan.
5. Only ask the user a question if there is a real decision with meaningful tradeoffs.
6. If the task is already complete, respond with a short completion update instead of reopening the work.

## Guardrails

- This is a nudge, not a new task.
- Continue the existing thread unless the user's arguments clearly redirect it.
- Treat vague follow-up text as prioritization, not as a request to restart from scratch.
