#!/usr/bin/env python3
"""
Reconcile git/Claude/Codex/Cursor/WakaTime output JSON into a single merged
hour estimate, with an optional supervised-vs-unattended split.

This replaces hand-rolling the merge algorithm inline each time (error-prone —
see references/reconciliation.md's changelog for a real bug this caused: two
different "engine time" bases got compared against each other and produced a
nonsensical result). Feed it the JSON files produced by the other scripts in
this skill; it does the union-of-intervals merge deterministically.

Usage:
  # Single repo
  python3 git_sessions.py /path/to/repo --since 2026-06-29 --until 2026-08-19 --raw > git.json
  python3 claude_messages.py --project-path /path/to/repo > claude.json
  python3 codex_messages.py --project-path /path/to/repo > codex.json
  python3 reconcile.py --git git.json --claude claude.json --codex codex.json \
      --since 2026-06-29 --until 2026-08-19 --tz Europe/Berlin

  # Multi-repo: pass --git/--claude/--codex/--cursor multiple times
  python3 reconcile.py --git backend.json --git frontend.json \
      --claude claude_backend.json --claude claude_frontend.json \
      --since 2026-01-01 --until 2026-02-01

Flags:
  --since / --until      YYYY-MM-DD, inclusive window (UTC calendar days)
  --gap-hours            Session-merge gap threshold, default 0.5 (30min).
                          Use 0.25 for a stricter/conservative estimate.
  --presence-window-min  +/- minutes around a real user prompt (or git commit)
                          counted as "supervised". Default 10. Set to 0 to
                          skip the supervised/unattended split entirely.
  --tz                   IANA tz name for daily bucketing, default UTC.
  --day-boundary-hour    Local hour where the reporting day rolls over,
                          default 8 (08:00) — an overnight session isn't
                          split across two days in the daily table. Pass 0
                          for plain midnight bucketing.
  --daily                Include a per-day breakdown in the output.

Output JSON:
  {
    "window": {"since": "...", "until": "..."},
    "gap_hours": 0.5,
    "engine_hours": N,           # total merged session duration, no buffer/floor
    "engine_sessions": N,
    "supervised_hours": N,       # only present if --presence-window-min > 0
    "unattended_hours": N,
    "supervised_pct": N,
    "presence_window_min": N,
    "sources": {"git_commits": N, "claude_activity": N, "codex_activity": N,
                "cursor_activity": N, "user_prompts": N, "wakatime_intervals": N},
    "daily": {"YYYY-MM-DD": {"engine_hours": N, "supervised_hours": N, "unattended_hours": N}, ...}
        # only present if --daily
  }
"""

import argparse
import json
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


def load_json_files(paths):
    out = []
    for p in paths or []:
        with open(p, "r", encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def day_bounds_epoch(date_str, tz):
    """UTC epoch bounds for a YYYY-MM-DD calendar day (used for --since/--until filtering)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
    return start.timestamp(), (start + timedelta(days=1)).timestamp()


def filter_window(ts_list, win_start, win_end):
    return sorted(t for t in ts_list if win_start <= t < win_end)


def sessionize(ts_list, gap_h):
    """Point events -> list of [start, end] sessions, split where gap > gap_h."""
    if not ts_list:
        return []
    gap_s = gap_h * 3600
    sessions = []
    start = prev = ts_list[0]
    for t in ts_list[1:]:
        if t - prev > gap_s:
            sessions.append([start, prev])
            start = t
        prev = t
    sessions.append([start, prev])
    return sessions


def merge_intervals(intervals, gap_h):
    """Union intervals that overlap or sit within gap_h of each other."""
    gap_s = gap_h * 3600
    intervals = sorted([list(iv) for iv in intervals], key=lambda iv: iv[0])
    merged = []
    for s, e in intervals:
        if merged and s - merged[-1][1] <= gap_s:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def intersect_total(a_intervals, b_intervals):
    """Total seconds of overlap between two interval lists (both pre-sorted or not)."""
    total = 0.0
    for s1, e1 in a_intervals:
        for s2, e2 in b_intervals:
            lo, hi = max(s1, s2), min(e1, e2)
            if hi > lo:
                total += hi - lo
    return total


def bucket_date(epoch, tz, day_boundary_hour):
    local_dt = datetime.fromtimestamp(epoch, tz)
    shifted = local_dt - timedelta(hours=day_boundary_hour)
    return shifted.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(description="Reconcile time-lens data sources into merged hours")
    parser.add_argument("--git", action="append", default=[], help="git_sessions.py output JSON (repeatable)")
    parser.add_argument("--claude", action="append", default=[], help="claude_messages.py output JSON (repeatable)")
    parser.add_argument("--codex", action="append", default=[], help="codex_messages.py output JSON (repeatable)")
    parser.add_argument("--cursor", action="append", default=[], help="cursor_messages.py output JSON (repeatable)")
    parser.add_argument("--waka", action="append", default=[], help="wakatime_fetch.py output JSON (repeatable)")
    parser.add_argument("--since", required=True, help="YYYY-MM-DD (inclusive, UTC calendar day)")
    parser.add_argument("--until", required=True, help="YYYY-MM-DD (exclusive upper bound, UTC calendar day)")
    parser.add_argument("--gap-hours", type=float, default=0.5,
                         help="Session-merge gap threshold in hours (default 0.5)")
    parser.add_argument("--presence-window-min", type=float, default=10,
                         help="+/- minutes around a real prompt/commit counted as supervised (default 10; 0 disables the split)")
    parser.add_argument("--tz", default="UTC", help="IANA tz name for daily bucketing (default UTC)")
    parser.add_argument("--day-boundary-hour", type=float, default=8,
                         help="Local hour the reporting day rolls over at (default 8; use 0 for midnight)")
    parser.add_argument("--daily", action="store_true", help="Include per-day breakdown")
    args = parser.parse_args()

    win_start, _ = day_bounds_epoch(args.since, args.tz)
    _, win_end = day_bounds_epoch(args.until, args.tz)

    tz = ZoneInfo(args.tz) if ZoneInfo else timezone.utc

    git_data = load_json_files(args.git)
    claude_data = load_json_files(args.claude)
    codex_data = load_json_files(args.codex)
    cursor_data = load_json_files(args.cursor)
    waka_data = load_json_files(args.waka)

    # Engine-time inputs: git raw commit timestamps + activity_timestamps
    # (NOT "timestamps") from Claude/Codex/Cursor. Falls back to "timestamps"
    # if a caller passed an older-format JSON without activity_timestamps.
    git_ts = filter_window(
        [t for d in git_data for t in d.get("timestamps", [])], win_start, win_end
    )
    claude_act = filter_window(
        [t for d in claude_data for t in d.get("activity_timestamps", d.get("timestamps", []))],
        win_start, win_end
    )
    codex_act = filter_window(
        [t for d in codex_data for t in d.get("activity_timestamps", d.get("timestamps", []))],
        win_start, win_end
    )
    cursor_act = filter_window(
        [t for d in cursor_data for t in d.get("activity_timestamps", d.get("timestamps", []))],
        win_start, win_end
    )
    waka_intervals = [
        list(iv) for d in waka_data for iv in d.get("intervals", [])
    ]
    # Clip WakaTime intervals to window
    waka_intervals = [
        [max(s, win_start), min(e, win_end)] for s, e in waka_intervals
        if min(e, win_end) > max(s, win_start)
    ]

    per_source_sessions = (
        sessionize(git_ts, args.gap_hours)
        + sessionize(claude_act, args.gap_hours)
        + sessionize(codex_act, args.gap_hours)
        + sessionize(cursor_act, args.gap_hours)
        + waka_intervals
    )
    engine_sessions = merge_intervals(per_source_sessions, args.gap_hours)
    engine_hours = sum(e - s for s, e in engine_sessions) / 3600

    result = {
        "window": {"since": args.since, "until": args.until},
        "gap_hours": args.gap_hours,
        "engine_hours": round(engine_hours, 2),
        "engine_sessions": len(engine_sessions),
        "sources": {
            "git_commits": len(git_ts),
            "claude_activity": len(claude_act),
            "codex_activity": len(codex_act),
            "cursor_activity": len(cursor_act),
            "wakatime_intervals": len(waka_intervals),
        },
    }

    # Supervised/unattended split
    if args.presence_window_min > 0:
        user_ts = sorted(
            filter_window([t for d in git_data for t in d.get("timestamps", [])], win_start, win_end)
            + filter_window([t for d in claude_data for t in d.get("timestamps", [])], win_start, win_end)
            + filter_window([t for d in codex_data for t in d.get("timestamps", [])], win_start, win_end)
            + filter_window([t for d in cursor_data for t in d.get("timestamps", [])], win_start, win_end)
        )
        result["sources"]["user_prompts"] = len(user_ts)

        w = args.presence_window_min * 60
        presence_intervals = merge_intervals([[t - w, t + w] for t in user_ts], 0)
        supervised_secs = intersect_total(engine_sessions, presence_intervals)
        supervised_hours = supervised_secs / 3600
        unattended_hours = engine_hours - supervised_hours

        result["presence_window_min"] = args.presence_window_min
        result["supervised_hours"] = round(supervised_hours, 2)
        result["unattended_hours"] = round(unattended_hours, 2)
        result["supervised_pct"] = (
            round(100 * supervised_hours / engine_hours, 1) if engine_hours > 0 else None
        )

    # Daily breakdown
    if args.daily:
        daily = {}
        for s, e in engine_sessions:
            date_str = bucket_date(s, tz, args.day_boundary_hour)
            daily.setdefault(date_str, {"engine_hours": 0.0})
            daily[date_str]["engine_hours"] += (e - s) / 3600

        if args.presence_window_min > 0:
            for s, e in engine_sessions:
                date_str = bucket_date(s, tz, args.day_boundary_hour)
                sup = intersect_total([[s, e]], presence_intervals) / 3600
                d = daily[date_str]
                d["supervised_hours"] = d.get("supervised_hours", 0.0) + sup
            for date_str, d in daily.items():
                d["unattended_hours"] = d["engine_hours"] - d.get("supervised_hours", 0.0)
                d["supervised_hours"] = round(d.get("supervised_hours", 0.0), 2)
                d["unattended_hours"] = round(d["unattended_hours"], 2)

        for d in daily.values():
            d["engine_hours"] = round(d["engine_hours"], 2)

        result["daily"] = dict(sorted(daily.items()))

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
