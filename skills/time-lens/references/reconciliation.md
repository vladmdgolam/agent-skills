# Reconciliation Algorithm Reference

## Overview

The reconciliation step combines all four data sources into a single merged estimate of actual working time, eliminating double-counting where sources overlap.

**Why merge matters:** AI agent prompts (Claude/Codex) often appear minutes before or after git commits in the same work session. WakaTime captures IDE keystrokes that may fall between commits. A typical flow: research with Claude → write code (WakaTime keystroke capture) → commit (git). All three events belong to one session. The union of all four sources captures true session boundaries without double-counting.

The merged total replaces "git-only" as the primary estimate. WakaTime hours are shown for reference only (active keystrokes only, always lower).

---

## Gap Threshold

```python
GAP_H = 1.5  # hours
```

Two events separated by more than 1.5 hours are considered different work sessions. This threshold is used both for:
- Detecting sessions from point-event timestamps (Claude, Codex)
- Merging nearby intervals from all sources in the final union step

---

## Input Data Formats

All timestamps must be converted to **UTC epoch floats** before merging.

| Source | Raw format | Conversion needed |
|---|---|---|
| `git_sessions.py` | Local datetime strings with timezone offset from `git log` | Convert using offset → UTC epoch |
| `claude_messages.py` | Point events, UTC epoch floats (already converted by script) | None — detect sessions via gap |
| `codex_messages.py` | Point events, UTC epoch floats (already converted by script) | None — detect sessions via gap |
| `wakatime_fetch.py` | `[start_epoch, end_epoch]` pairs, UTC epoch floats | None — already intervals |

---

## Algorithm (Pseudocode)

```python
GAP_H = 1.5  # hours between events → new session

# --- Step 1: Gather intervals from git ---
# git_sessions.py output: list of {start_local, end_local, tz_offset}
git_intervals = []
for session in git_output["sessions"]:
    start_epoch = local_to_utc_epoch(session["start"], session["tz_offset"])
    end_epoch   = local_to_utc_epoch(session["end"],   session["tz_offset"])
    git_intervals.append((start_epoch, end_epoch))

# --- Step 2: Detect sessions from Claude point events ---
claude_intervals = detect_sessions(claude_output["timestamps"], GAP_H)

# --- Step 3: Detect sessions from Codex point events ---
codex_intervals = detect_sessions(codex_output["timestamps"], GAP_H)

# --- Step 4: WakaTime intervals (already [start, end] pairs) ---
waka_intervals = wakatime_output["intervals"]  # list of [start_epoch, end_epoch]

# --- Step 5: Combine and sort ---
all_intervals = git_intervals + claude_intervals + codex_intervals + waka_intervals
all_intervals.sort(key=lambda x: x[0])  # sort by start time

# --- Step 6: Merge overlapping/adjacent intervals ---
merged = []
for interval in all_intervals:
    if merged and interval[0] - merged[-1][1] <= GAP_H * 3600:
        # Extend current merged interval if gap is within threshold
        merged[-1] = (merged[-1][0], max(merged[-1][1], interval[1]))
    else:
        merged.append(list(interval))

# --- Step 7: Estimate hours per merged interval ---
estimated_hours = []
for start, end in merged:
    raw_duration_h = (end - start) / 3600
    est = max(raw_duration_h + 0.5, 0.5)  # add 0.5h buffer, min 0.5h
    estimated_hours.append(est)

# --- Step 8: Sum ---
total_hours = sum(estimated_hours)
```

---

## Session Detection from Point Events

Used for Claude and Codex timestamps (which are point events, not intervals):

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

## Hour Estimate Formula

For each merged interval:

```
est = max(end - start + 0.5h, 0.5h)
```

- The `+0.5h` buffer accounts for work done before the first tracked event and after the last (e.g., the developer was thinking before opening the editor).
- The `min 0.5h` floor ensures single-commit sessions (where start == end) still contribute a meaningful estimate rather than 0.

---

## Multi-Repo Projects

When a project spans multiple git repositories (e.g., a monorepo that was split, or a backend + frontend pair):

1. Run `git_sessions.py` on each repository separately.
2. Collect all session arrays.
3. Before reconciliation, merge all git session arrays into one list, sort by start time, and re-merge sessions within the gap threshold.
4. Proceed with the standard reconciliation algorithm above.
