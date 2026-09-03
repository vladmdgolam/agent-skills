#!/usr/bin/env python3
"""
Parse git log to detect work sessions and estimate total hours.

Usage:
  python3 git_sessions.py <repo_path> [--since YYYY-MM-DD] [--until YYYY-MM-DD]
  python3 git_sessions.py /path/to/repo --since 2026-01-01 --until 2026-02-28

Output: JSON with sessions, daily hours, and totals.
"""

import subprocess
import json
import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

SESSION_GAP_HOURS = 1.5   # commits > this apart = new session
SESSION_BUFFER = 0.5       # hours added per session (startup/context-switching) — legacy default, see --raw
MIN_SESSION_HOURS = 0.5    # minimum session duration — legacy default, see --raw


def get_commits(repo_path, since=None, until=None):
    cmd = ["git", "-C", repo_path, "log", "--format=%H\t%ai\t%s", "--no-merges"]
    if since:
        cmd += [f"--since={since}"]
    if until:
        cmd += [f"--until={until}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t", 2)
        if len(parts) >= 2:
            sha, ts_str = parts[0], parts[1]
            msg = parts[2] if len(parts) > 2 else ""
            try:
                # Parse ISO 8601 with timezone offset
                ts = datetime.fromisoformat(ts_str)
                commits.append({"sha": sha, "ts": ts, "msg": msg})
            except ValueError:
                pass
    return sorted(commits, key=lambda c: c["ts"])


def detect_sessions(commits):
    """Group commits into sessions (gap > SESSION_GAP_HOURS = new session)."""
    if not commits:
        return []
    sessions = []
    current = [commits[0]]
    for commit in commits[1:]:
        gap = (commit["ts"] - current[-1]["ts"]).total_seconds() / 3600
        if gap > SESSION_GAP_HOURS:
            sessions.append(current)
            current = [commit]
        else:
            current.append(commit)
    sessions.append(current)
    return sessions


def session_hours(session, raw_mode=False):
    """
    Duration of a session. By default (legacy behavior) adds a 0.5h buffer
    and enforces a 0.5h floor. With raw_mode=True, neither is applied — a
    single-commit session is a genuine 0.0h point, matching how
    activity_timestamps-based reconciliation treats git (a commit alone,
    with no Claude/Codex activity around it, really is just a point; the
    merge step is what's responsible for extending it if other sources
    show activity nearby).
    """
    if len(session) == 1:
        raw = 0.0
    else:
        raw = (session[-1]["ts"] - session[0]["ts"]).total_seconds() / 3600
    if raw_mode:
        return raw
    return max(raw + SESSION_BUFFER, MIN_SESSION_HOURS)


def main():
    parser = argparse.ArgumentParser(description="Estimate work hours from git history")
    parser.add_argument("repo", help="Path to git repository")
    parser.add_argument("--since", help="Start date YYYY-MM-DD")
    parser.add_argument("--until", help="End date YYYY-MM-DD")
    parser.add_argument("--raw", action="store_true",
                         help="No +0.5h buffer, no 0.5h floor — raw commit-span durations "
                              "(recommended default for reconciliation against activity_timestamps; "
                              "the buffered/floored mode is legacy, kept for backward compatibility)")
    args = parser.parse_args()

    commits = get_commits(args.repo, args.since, args.until)
    if not commits:
        print(json.dumps({"error": "No commits found"}))
        return

    sessions = detect_sessions(commits)

    # Build output
    session_data = []
    daily_hours = defaultdict(float)
    total_hours = 0.0

    for s in sessions:
        start = s[0]["ts"]
        end = s[-1]["ts"]
        h = session_hours(s, raw_mode=args.raw)
        date_str = start.strftime("%Y-%m-%d")
        daily_hours[date_str] += h
        total_hours += h
        session_data.append({
            "date": date_str,
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "start_h": round(start.hour + start.minute / 60, 3),
            "end_h": round((end.hour + end.minute / 60) + (0 if args.raw else SESSION_BUFFER), 3),
            "duration_h": round(h, 2),
            "commits": len(s),
        })

    print(json.dumps({
        "repo": args.repo,
        "total_commits": len(commits),
        "total_sessions": len(sessions),
        "total_hours": round(total_hours, 2),
        "raw_mode": args.raw,
        "date_range": {
            "first": commits[0]["ts"].strftime("%Y-%m-%d"),
            "last": commits[-1]["ts"].strftime("%Y-%m-%d"),
        },
        "sessions": session_data,
        "daily_hours": dict(sorted(daily_hours.items())),
        # Raw commit timestamps (UTC epoch floats) — same shape as
        # claude/codex/cursor's activity_timestamps, for merging into the
        # union-of-sources reconciliation instead of using pre-sessionized data.
        "timestamps": [round(c["ts"].timestamp(), 3) for c in commits],
    }, indent=2))


if __name__ == "__main__":
    main()
