#!/usr/bin/env python3
"""
Count Claude Code user prompts for a specific project, with per-day breakdown.

Data sources:
  Primary:   ~/.claude/history.jsonl  — one entry per submitted prompt, has "project" (abs path)
             and "timestamp" (ms epoch).
  Fallback:  ~/.claude/projects/<encoded>/*.jsonl  — session files, use for sessions that
             predate history.jsonl. Filter type="user", exclude tool_result content.

Usage:
  python3 claude_messages.py --project-path /abs/path/to/repo
  python3 claude_messages.py --filter project-name   [substring match on dir name]
  python3 claude_messages.py --project-path /path --projects-dir ~/.claude/projects

Output JSON:
  {
    "project_path": "...",
    "total_user_messages": N,
    "daily": {"YYYY-MM-DD": count, ...},
    "sources": {"history": N, "session_files": N}
  }
"""

import os
import json
import argparse
import glob
from datetime import datetime, timezone
from collections import defaultdict


def path_to_encoded(abs_path):
    """Convert absolute path to Claude's encoded project dir name: /a/b → -a-b"""
    return abs_path.replace("/", "-")


def find_project_dirs(projects_dir, project_path=None, name_filter=None):
    """Return list of matching Claude project dirs."""
    projects_dir = os.path.expanduser(projects_dir)
    if not os.path.isdir(projects_dir):
        return []

    if project_path:
        encoded = path_to_encoded(project_path)
        candidate = os.path.join(projects_dir, encoded)
        return [candidate] if os.path.isdir(candidate) else []

    return [
        e.path for e in sorted(os.scandir(projects_dir), key=lambda e: e.name)
        if e.is_dir() and name_filter and name_filter.lower() in e.name.lower()
    ]


def is_real_prompt(obj):
    """Return True if this session entry is an actual user prompt (not a tool result)."""
    content = obj.get("message", {}).get("content", "")
    if isinstance(content, str):
        return True
    if isinstance(content, list) and content:
        # list[text] = prompt with pasted content; list[tool_result] = tool output
        return content[0].get("type") != "tool_result"
    return False


def collect_from_history(project_path):
    """
    Collect prompts from ~/.claude/history.jsonl filtered by project path.
    Returns: {date: count}, set of rounded timestamps (for dedup with session files).
    """
    daily = defaultdict(int)
    seen_ts = set()
    history_path = os.path.expanduser("~/.claude/history.jsonl")

    if not os.path.exists(history_path) or not project_path:
        return daily, seen_ts

    with open(history_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("project") != project_path:
                continue

            ts_ms = obj.get("timestamp")
            if ts_ms is None:
                continue

            ts_float = ts_ms / 1000.0
            date = datetime.fromtimestamp(ts_float, tz=timezone.utc).strftime("%Y-%m-%d")
            seen_ts.add(round(ts_float))
            daily[date] += 1

    return daily, seen_ts


def collect_from_session_files(project_dirs, project_path, seen_ts):
    """
    Collect actual user prompts from session .jsonl files.
    Skips entries already accounted for in history (dedup by rounded timestamp).
    Returns {date: count}.
    """
    daily = defaultdict(int)

    for proj_dir in project_dirs:
        for jsonl_file in glob.glob(os.path.join(proj_dir, "*.jsonl")):
            try:
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if obj.get("type") != "user":
                            continue
                        if project_path and obj.get("cwd") != project_path:
                            continue
                        if not is_real_prompt(obj):
                            continue

                        ts_str = obj.get("timestamp", "")
                        try:
                            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts_rounded = round(dt.timestamp())
                            date = dt.strftime("%Y-%m-%d")
                        except Exception:
                            continue

                        if ts_rounded not in seen_ts:
                            seen_ts.add(ts_rounded)
                            daily[date] += 1
            except (IOError, PermissionError):
                pass

    return daily


def main():
    parser = argparse.ArgumentParser(description="Count Claude Code prompts per project by day")
    parser.add_argument("--project-path", help="Absolute path to the project repo (exact match)")
    parser.add_argument("--filter", help="Substring match on Claude project dir name")
    parser.add_argument("--projects-dir", default="~/.claude/projects")
    args = parser.parse_args()

    if not args.project_path and not args.filter:
        print(json.dumps({"error": "Provide --project-path or --filter"}))
        return

    project_dirs = find_project_dirs(args.projects_dir, args.project_path, args.filter)

    if not project_dirs:
        result = {
            "project_path": args.project_path or args.filter,
            "total_user_messages": 0,
            "daily": {},
            "timestamps": [],
            "note": "No matching Claude project directory found"
        }
        # Folder move detection: scan history.jsonl for same basename at different paths
        # (history.jsonl stores exact absolute paths — no lossy encoding)
        if args.project_path:
            target_name = os.path.basename(args.project_path)
            alternates = set()
            history_path = os.path.expanduser("~/.claude/history.jsonl")
            if os.path.exists(history_path):
                with open(history_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                            proj = obj.get("project", "")
                            if (proj and proj != args.project_path and
                                    os.path.basename(proj) == target_name):
                                alternates.add(proj)
                        except (json.JSONDecodeError, KeyError):
                            pass
            # Also check project dir names (session cwd fields)
            for entry in os.scandir(os.path.expanduser(args.projects_dir)):
                if not entry.is_dir():
                    continue
                for jf in glob.glob(os.path.join(entry.path, "*.jsonl")):
                    try:
                        with open(jf) as f:
                            obj = json.loads(f.readline().strip())
                            cwd = obj.get("cwd", "")
                            if (cwd and cwd != args.project_path and
                                    os.path.basename(cwd) == target_name):
                                alternates.add(cwd)
                    except Exception:
                        pass
                    break  # only need first line of first file per project
            if alternates:
                result["alternate_paths"] = sorted(alternates)
                result["note"] = (
                    f"No Claude history at {args.project_path}, "
                    f"but found history for '{target_name}' at "
                    f"{len(alternates)} other path(s). Project may have been moved."
                )
        print(json.dumps(result, indent=2))
        return

    # Primary: history.jsonl (one entry per prompt, most reliable)
    daily_history, seen_ts = collect_from_history(args.project_path)

    # Fallback: session files for prompts not captured in history
    daily_sessions = collect_from_session_files(project_dirs, args.project_path, seen_ts)

    # Merge
    all_dates = set(daily_history) | set(daily_sessions)
    daily_merged = {
        date: daily_history.get(date, 0) + daily_sessions.get(date, 0)
        for date in sorted(all_dates)
    }

    print(json.dumps({
        "project_path": args.project_path or args.filter,
        "project_dirs": project_dirs,
        "total_user_messages": sum(daily_merged.values()),
        "daily": daily_merged,
        "sources": {
            "history": sum(daily_history.values()),
            "session_files": sum(daily_sessions.values()),
        },
        # Raw sorted timestamps (Unix epoch floats) — use for merged session detection
        "timestamps": sorted(seen_ts),
    }, indent=2))


if __name__ == "__main__":
    main()
