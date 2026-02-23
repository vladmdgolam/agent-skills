#!/usr/bin/env python3
"""
Count Codex CLI user prompts for a specific project, with per-day breakdown.

Data source: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
  - session_meta entry: payload.cwd = project directory
  - event_msg entry: payload.type == "user_message" = actual user prompt

Usage:
  python3 codex_messages.py --project-path /abs/path/to/repo
  python3 codex_messages.py --filter project-name

Output JSON:
  {
    "project_path": "...",
    "total_user_messages": N,
    "daily": {"YYYY-MM-DD": count, ...},
    "timestamps": [epoch_float, ...],
    "sessions_found": N
  }
"""

import os
import json
import argparse
import glob
from datetime import datetime, timezone
from collections import defaultdict


def scan_sessions(sessions_dir, project_path=None, name_filter=None):
    """
    Scan Codex session files. Filter by cwd == project_path (exact) or
    basename match for name_filter (substring).
    Returns (daily counts, sorted timestamp list, session count).
    """
    sessions_dir = os.path.expanduser(sessions_dir)
    if not os.path.isdir(sessions_dir):
        return {}, [], 0

    daily = defaultdict(int)
    timestamps = []
    sessions_found = 0

    for jsonl_path in sorted(glob.glob(
        os.path.join(sessions_dir, "**", "*.jsonl"), recursive=True
    )):
        cwd = None
        session_prompts = []

        for line in open(jsonl_path, "r", encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Extract cwd from session_meta (always first entry)
            if obj.get("type") == "session_meta":
                cwd = obj.get("payload", {}).get("cwd", "")
                continue

            # Check cwd match
            if cwd is None:
                continue
            if project_path and cwd != project_path:
                break  # wrong project, skip rest of file
            if name_filter and name_filter.lower() not in os.path.basename(cwd).lower():
                break

            # Count user prompts
            if (obj.get("type") == "event_msg" and
                    obj.get("payload", {}).get("type") == "user_message"):
                ts_str = obj.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    ts_epoch = dt.timestamp()
                    date = dt.strftime("%Y-%m-%d")
                    session_prompts.append((date, ts_epoch))
                except Exception:
                    session_prompts.append((None, None))

        if session_prompts:
            sessions_found += 1
            for date, ts in session_prompts:
                if date:
                    daily[date] += 1
                if ts:
                    timestamps.append(ts)

    return dict(sorted(daily.items())), sorted(timestamps), sessions_found


def find_alternate_paths(sessions_dir, project_path):
    """
    When no sessions match project_path, look for sessions with the same
    basename (last path component) at different parent paths.
    Suggests the project may have been moved.
    """
    sessions_dir = os.path.expanduser(sessions_dir)
    if not os.path.isdir(sessions_dir):
        return []

    target_name = os.path.basename(project_path)
    alternates = set()

    for jsonl_path in glob.glob(
        os.path.join(sessions_dir, "**", "*.jsonl"), recursive=True
    ):
        for line in open(jsonl_path, "r", encoding="utf-8"):
            try:
                obj = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "session_meta":
                cwd = obj.get("payload", {}).get("cwd", "")
                if cwd and cwd != project_path and os.path.basename(cwd) == target_name:
                    alternates.add(cwd)
                break  # only read session_meta

    return sorted(alternates)


def main():
    parser = argparse.ArgumentParser(description="Count Codex user prompts per project by day")
    parser.add_argument("--project-path", help="Absolute path to the project repo (exact match)")
    parser.add_argument("--filter", help="Substring match on project basename")
    parser.add_argument("--sessions-dir", default="~/.codex/sessions")
    args = parser.parse_args()

    if not args.project_path and not args.filter:
        print(json.dumps({"error": "Provide --project-path or --filter"}))
        return

    daily, timestamps, sessions_found = scan_sessions(
        args.sessions_dir, args.project_path, args.filter
    )

    result = {
        "project_path": args.project_path or args.filter,
        "total_user_messages": sum(daily.values()),
        "daily": daily,
        "timestamps": timestamps,
        "sessions_found": sessions_found,
    }

    # Folder move detection
    if sum(daily.values()) == 0 and args.project_path:
        alternates = find_alternate_paths(args.sessions_dir, args.project_path)
        if alternates:
            result["alternate_paths"] = alternates
            result["note"] = (
                f"No Codex sessions found at {args.project_path}, "
                f"but found sessions for '{os.path.basename(args.project_path)}' "
                f"at {len(alternates)} other path(s). Project may have been moved."
            )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
