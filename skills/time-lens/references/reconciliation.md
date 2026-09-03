# Reconciliation Algorithm Reference

**Run this via `scripts/reconcile.py`, not by hand-rolling it in Python.** Everything below is the algorithm reference / rationale — `reconcile.py` is the tested, deterministic implementation. Feed it the JSON output of `git_sessions.py --raw`, `claude_messages.py`, `codex_messages.py`, `cursor_messages.py`, and `wakatime_fetch.py`.

## Overview

The reconciliation step combines all five data sources into a single merged estimate of actual working time, eliminating double-counting where sources overlap.

**Why merge matters:** AI agent prompts (Claude/Codex/Cursor) often appear minutes before or after git commits in the same work session. WakaTime captures IDE keystrokes that may fall between commits. A typical flow: research with Claude → use Cursor's AI for edits → write code (WakaTime keystroke capture) → commit (git). All four events belong to one session. The union of all five sources captures true session boundaries without double-counting.

The merged total replaces "git-only" as the primary estimate. WakaTime hours are shown for reference only (active keystrokes only, always lower).

---

## Use `activity_timestamps`, not `timestamps` (changed 2026-08-19)

`claude_messages.py`, `codex_messages.py`, and `cursor_messages.py` each output two timestamp arrays:

- `timestamps` — user prompts only (or user commit-equivalent). Good for prompt-count metrics, **bad for reconciliation.**
- `activity_timestamps` — every timestamped event (assistant replies, tool-call/tool-result cycles, patches, reasoning steps), not just prompts.

**Always feed `activity_timestamps` into the reconciliation step below.** Using `timestamps` alone silently drops real work time: a lone user prompt with nothing else recorded for 45+ minutes looks like a single 0-duration point, when in fact the agent may have been running tools continuously that whole time — the timestamp source just never recorded any of it.

This was found by inspecting a real Codex rollout file: a session that looked like an isolated point in `timestamps` (single `user_message`, next prompt 50 minutes later) actually contained **1,343 timestamped events** in that gap (`response_item`/`event_msg` entries — tool calls, patch applications, reasoning), with the longest true idle stretch inside it being **36 seconds**. The "session" was really ~50 minutes of near-continuous work that the prompt-only view had zeroed out.

Practical effect on gap-threshold sensitivity: with `timestamps`-only data, shrinking the gap threshold from 1.5h to 15min on a real project nearly halved the computed total (35.69h → 16.95h), because it kept treating ordinary in-session lulls as session breaks. With `activity_timestamps`, the same threshold sweep moved the total by only ~15% (28.84h → 33.67h) — because the tool-call/reasoning events fill in what's actually happening between prompts, a tight threshold no longer falsely zeroes out active work.

`git_sessions.py` doesn't have this split — a commit is genuinely a point event with no "activity" available in between from git alone. That's fine: the merge step below fills git's gaps in wherever Claude/Codex/Cursor activity overlaps them. Use `git_sessions.py --raw` (raw commit-span durations, no buffer/floor) rather than the default buffered/floored mode when reconciling against `activity_timestamps` — mixing a padded source with unpadded sources double-pads.

---

## Gap Threshold (changed 2026-08-19)

```python
GAP_H = 0.5  # hours — new recommended default, used with activity_timestamps
```

Two events separated by more than the threshold are considered different work sessions. Used both for:
- Detecting sessions from point-event timestamps (git, and `activity_timestamps` for Claude/Codex/Cursor)
- Merging nearby intervals from all sources in the final union step

**Why 0.5h, not the old 1.5h:** 1.5h was tuned to compensate for missing agent-activity data — it had to bridge real gaps because there was nothing recorded inside them. With `activity_timestamps` filling those gaps directly, a much tighter threshold is both accurate and safe. On a real project, 0.5h against `activity_timestamps` landed close to what 1.5h against `timestamps`-only data produced (33.67h vs. 35.69h) — but it got there by actually measuring the gaps instead of assuming they were still "in session."

- Use **15min** for a stricter/conservative estimate (fewer sessions get bridged; good for billing where you want to undercount rather than over).
- Use **0.5h** (30min) as the general default — a reasonable balance that still won't fragment normal back-and-forth prompting.
- The old **1.5h** threshold is legacy — only reach for it if reconciling against `timestamps`-only data (e.g. a source with no activity-level granularity), where it's still doing the job of covering for the missing detail.

---

## Input Data Formats

All timestamps must be converted to **UTC epoch floats** before merging.

| Source | Raw format | Conversion needed |
|---|---|---|
| `git_sessions.py` | `timestamps`: UTC epoch floats (raw commit times, already converted). Also has pre-sessionized `sessions` (buffered by default; pass `--raw` for unbuffered) if you'd rather not re-sessionize yourself. | None |
| `claude_messages.py` | `activity_timestamps`: UTC epoch floats (already converted) | None — detect sessions via gap |
| `codex_messages.py` | `activity_timestamps`: UTC epoch floats (already converted) | None — detect sessions via gap |
| `cursor_messages.py` | `activity_timestamps`: UTC epoch floats (already converted) | None — detect sessions via gap |
| `wakatime_fetch.py` | `[start_epoch, end_epoch]` pairs, UTC epoch floats | None — already intervals |

---

## Algorithm (Pseudocode)

```python
GAP_H = 0.5  # hours between events → new session (use 0.25 for a stricter estimate)

# --- Step 1: Detect sessions from git's raw commit timestamps ---
git_intervals = detect_sessions(git_output["timestamps"], GAP_H)

# --- Step 2: Detect sessions from Claude activity events ---
claude_intervals = detect_sessions(claude_output["activity_timestamps"], GAP_H)

# --- Step 3: Detect sessions from Codex activity events ---
codex_intervals = detect_sessions(codex_output["activity_timestamps"], GAP_H)

# --- Step 4: Detect sessions from Cursor activity events ---
cursor_intervals = detect_sessions(cursor_output["activity_timestamps"], GAP_H)

# --- Step 5: WakaTime intervals (already [start, end] pairs) ---
waka_intervals = wakatime_output["intervals"]  # list of [start_epoch, end_epoch]

# --- Step 6: Combine and sort ---
all_intervals = git_intervals + claude_intervals + codex_intervals + cursor_intervals + waka_intervals
all_intervals.sort(key=lambda x: x[0])  # sort by start time

# --- Step 7: Merge overlapping/adjacent intervals ---
merged = []
for interval in all_intervals:
    if merged and interval[0] - merged[-1][1] <= GAP_H * 3600:
        # Extend current merged interval if gap is within threshold
        merged[-1] = (merged[-1][0], max(merged[-1][1], interval[1]))
    else:
        merged.append(list(interval))

# --- Step 8: Hours per merged interval — raw duration, no buffer/floor ---
estimated_hours = [(end - start) / 3600 for start, end in merged]

# --- Step 9: Sum ---
total_hours = sum(estimated_hours)
```

No `+0.5h` buffer and no `0.5h` floor by default — with `activity_timestamps` in the mix, a merged interval's start/end already reflect real recorded activity, not just a bare commit or prompt. The old buffer/floor existed specifically to compensate for `timestamps`-only data's blind spots; it's redundant (and double-counts) once those blind spots are filled by activity data. If you're reconciling a source that genuinely has no activity granularity (e.g. `timestamps`-only from an older skill version), see "Legacy: buffer/floor" below.

---

## Session Detection from Point Events

Used for git, Claude, Codex, and Cursor timestamps (all point events, not pre-built intervals):

```python
def detect_sessions(timestamps: list[float], gap_h: float) -> list[tuple]:
    """
    Given a sorted list of UTC epoch floats (point events),
    group into sessions separated by gap_h hours.
    Returns list of (session_start, session_end) tuples.
    """
    if not timestamps:
        return []
    timestamps = sorted(timestamps)
    sessions = []
    session_start = timestamps[0]
    session_end   = timestamps[0]
    for ts in timestamps[1:]:
        if ts - session_end > gap_h * 3600:
            sessions.append((session_start, session_end))
            session_start = ts
        session_end = ts
    sessions.append((session_start, session_end))
    return sessions
```

---

## Day-boundary bucketing (optional, for daily breakdowns)

When reporting per-day hours (not just a grand total), bucket a merged session by the calendar date it *started* on, shifted so the day rolls over at **08:00 local time** instead of midnight — otherwise an overnight session spanning e.g. 23:00→06:00 gets split across two days in the daily table even though it's one continuous block of work.

```python
def bucket_date(session_start_epoch, tz):
    local_dt = datetime.fromtimestamp(session_start_epoch, tz)
    shifted = local_dt - timedelta(hours=8)
    return shifted.strftime("%Y-%m-%d")
```

This only affects which day a session's hours are attributed to in a daily table — it does not change the grand total.

---

## Legacy: buffer/floor (pre-2026-08-19 default, still available)

For each merged interval:

```
est = max(end - start + 0.5h, 0.5h)
```

- The `+0.5h` buffer accounts for work done before the first tracked event and after the last (e.g., the developer was thinking before opening the editor).
- The `min 0.5h` floor ensures single-commit sessions (where start == end) still contribute a meaningful estimate rather than 0.

This is still `git_sessions.py`'s default mode (pass `--raw` to disable it) and is worth using if you're reconciling against `timestamps`-only sources with no activity-level data. Don't combine buffered and unbuffered sources in the same reconciliation — pick one mode and apply it consistently, or the buffer double-pads intervals that already reflect real activity spans.

---

## Multi-Repo Projects

When a project spans multiple git repositories (e.g., a monorepo that was split, or a backend + frontend pair):

1. Run `git_sessions.py` on each repository separately.
2. Collect all session arrays.
3. Before reconciliation, merge all git session arrays into one list, sort by start time, and re-merge sessions within the gap threshold.
4. Proceed with the standard reconciliation algorithm above.
