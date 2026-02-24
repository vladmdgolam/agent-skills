#!/usr/bin/env python3
"""
Count Cursor IDE user prompts for a specific project, with per-day breakdown.

Data sources:
  Primary:   ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb
             — cursorDiskKV table: composerData:{sessionId} (workspace URI) and
               bubbleId:{sessionId}:{messageId} (per-message timestamps)
  Fallback:  ~/Library/Application Support/Cursor/User/workspaceStorage/*/state.vscdb
             — ItemTable: composer.composerData (session-level timestamps only)
             — ItemTable: legacy chatdata keys (per-message timestamps)

Usage:
  python3 cursor_messages.py --project-path /abs/path/to/repo
  python3 cursor_messages.py --filter project-name

Output JSON:
  {
    "project_path": "...",
    "total_user_messages": N,
    "daily": {"YYYY-MM-DD": count, ...},
    "timestamps": [epoch_float, ...],
    "sessions_found": N,
    "sources": {"global_storage": N, "workspace_storage": N}
  }
"""

import os
import sys
import json
import argparse
import sqlite3
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import unquote, urlparse


def get_cursor_data_dir():
    """Return the Cursor User data directory for the current platform."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Cursor/User")
    elif sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", ""), "Cursor", "User")
    else:  # Linux
        return os.path.expanduser("~/.config/Cursor/User")


def uri_to_path(uri):
    """Convert a file:// URI to an absolute path."""
    if not uri:
        return ""
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return unquote(parsed.path)
    return uri


def paths_match(path1, path2):
    """Check if two paths refer to the same directory."""
    return os.path.normpath(path1) == os.path.normpath(path2)


def scan_workspace_mappings(cursor_dir):
    """Scan workspaceStorage dirs → dict of workspace_id → project_path."""
    ws_dir = os.path.join(cursor_dir, "workspaceStorage")
    if not os.path.isdir(ws_dir):
        return {}

    mappings = {}
    for entry in os.scandir(ws_dir):
        if not entry.is_dir():
            continue
        ws_json = os.path.join(entry.path, "workspace.json")
        if not os.path.exists(ws_json):
            continue
        try:
            with open(ws_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            folder = data.get("folder", "")
            if folder:
                mappings[entry.name] = uri_to_path(folder)
        except (json.JSONDecodeError, IOError):
            pass

    return mappings


def _extract_bubble_timestamp(bubble):
    """
    Extract a UTC epoch float from a Cursor bubble/message object.
    Tries fields in priority order (mirrors cursor-history's fallback chain).
    Returns epoch float or None.
    """
    # 1. createdAt ISO string (new format, >= Sept 2025)
    created_at = bubble.get("createdAt")
    if created_at and isinstance(created_at, str):
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, TypeError):
            pass

    # 2. timingInfo fields (Unix ms)
    timing = bubble.get("timingInfo")
    if isinstance(timing, dict):
        for field in ("clientStartTime", "clientRpcSendTime",
                      "clientSettleTime", "clientEndTime"):
            val = timing.get(field)
            if val and isinstance(val, (int, float)) and val > 1_000_000_000_000:
                return val / 1000.0

    # 3. Plain timestamp field (legacy, ms epoch)
    ts = bubble.get("timestamp")
    if ts and isinstance(ts, (int, float)) and ts > 1_000_000_000_000:
        return ts / 1000.0

    return None


def collect_from_global_storage(cursor_dir, project_path=None, name_filter=None):
    """
    Collect user prompt timestamps from global storage's cursorDiskKV table.
    Returns (daily_counts, timestamps, sessions_found).
    """
    global_db = os.path.join(cursor_dir, "globalStorage", "state.vscdb")
    if not os.path.exists(global_db):
        return {}, [], 0

    daily = defaultdict(int)
    timestamps = []
    sessions_found = 0

    try:
        conn = sqlite3.connect(f"file:{global_db}?mode=ro", uri=True)
        cur = conn.cursor()

        # Check if cursorDiskKV table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'"
        )
        if not cur.fetchone():
            conn.close()
            return {}, [], 0

        # Get all composer sessions with their workspace URIs
        cur.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
        )

        matching_session_ids = []
        for key, value in cur.fetchall():
            try:
                session_id = key.split(":", 1)[1]
                data = json.loads(value) if isinstance(value, str) else {}
                ws_uri = data.get("workspaceUri", "")
                ws_path = uri_to_path(ws_uri)

                if project_path:
                    if not ws_path or not paths_match(ws_path, project_path):
                        continue
                elif name_filter:
                    basename = os.path.basename(os.path.normpath(ws_path)) if ws_path else ""
                    if not basename or name_filter.lower() not in basename.lower():
                        continue

                matching_session_ids.append(session_id)
            except (json.JSONDecodeError, IndexError, AttributeError):
                continue

        # For each matching session, get user-message bubble data
        for session_id in matching_session_ids:
            session_ts = []
            cur.execute(
                "SELECT value FROM cursorDiskKV WHERE key LIKE ?",
                (f"bubbleId:{session_id}:%",),
            )

            for (value,) in cur.fetchall():
                try:
                    bubble = json.loads(value) if isinstance(value, str) else {}
                except json.JSONDecodeError:
                    continue

                # Only count user messages (type=1)
                if bubble.get("type") != 1:
                    continue

                ts_epoch = _extract_bubble_timestamp(bubble)
                if ts_epoch is not None:
                    session_ts.append(ts_epoch)

            if session_ts:
                sessions_found += 1
                for ts in session_ts:
                    date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                    daily[date] += 1
                    timestamps.append(ts)

        conn.close()
    except (sqlite3.Error, IOError):
        pass

    return dict(sorted(daily.items())), sorted(timestamps), sessions_found


def collect_from_workspace_storage(cursor_dir, project_path=None,
                                   name_filter=None, seen_ts=None):
    """
    Fallback: collect timestamps from per-workspace state.vscdb databases.
    Reads composer.composerData and legacy chatdata keys from ItemTable.
    Deduplicates against already-seen timestamps from global storage.
    Returns (daily_counts, timestamps, sessions_found).
    """
    if seen_ts is None:
        seen_ts = set()

    ws_mappings = scan_workspace_mappings(cursor_dir)
    if not ws_mappings:
        return {}, [], 0

    daily = defaultdict(int)
    timestamps = []
    sessions_found = 0

    for ws_id, ws_path in ws_mappings.items():
        if project_path and not paths_match(ws_path, project_path):
            continue
        if name_filter:
            basename = os.path.basename(os.path.normpath(ws_path))
            if name_filter.lower() not in basename.lower():
                continue

        db_path = os.path.join(cursor_dir, "workspaceStorage", ws_id, "state.vscdb")
        if not os.path.exists(db_path):
            continue

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()

            # --- Composer data (session-level timestamps) ---
            cur.execute(
                "SELECT value FROM ItemTable WHERE key = 'composer.composerData'"
            )
            row = cur.fetchone()
            if row and row[0]:
                try:
                    data = json.loads(row[0])
                    for composer in data.get("allComposers", []):
                        created = composer.get("createdAt")
                        updated = composer.get("lastUpdatedAt")
                        for ts_ms in (created, updated):
                            if (ts_ms and isinstance(ts_ms, (int, float))
                                    and ts_ms > 1_000_000_000_000):
                                ts_epoch = ts_ms / 1000.0
                                ts_rounded = round(ts_epoch)
                                if ts_rounded not in seen_ts:
                                    seen_ts.add(ts_rounded)
                                    date = datetime.fromtimestamp(
                                        ts_epoch, tz=timezone.utc
                                    ).strftime("%Y-%m-%d")
                                    daily[date] += 1
                                    timestamps.append(ts_epoch)
                        if created or updated:
                            sessions_found += 1
                except json.JSONDecodeError:
                    pass

            # --- Legacy chat data keys (per-message timestamps) ---
            for key in (
                "workbench.panel.aichat.view.aichat.chatdata",
                "workbench.panel.chat.view.chat.chatdata",
            ):
                cur.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
                row = cur.fetchone()
                if not (row and row[0]):
                    continue
                try:
                    data = json.loads(row[0])
                    for session in data.get("chatSessions", data.get("tabs", [])):
                        has_msgs = False
                        for msg in session.get("messages", session.get("bubbles", [])):
                            if msg.get("role") != "user":
                                continue
                            ts_ms = msg.get("timestamp")
                            if (ts_ms and isinstance(ts_ms, (int, float))
                                    and ts_ms > 1_000_000_000_000):
                                ts_epoch = ts_ms / 1000.0
                                ts_rounded = round(ts_epoch)
                                if ts_rounded not in seen_ts:
                                    seen_ts.add(ts_rounded)
                                    date = datetime.fromtimestamp(
                                        ts_epoch, tz=timezone.utc
                                    ).strftime("%Y-%m-%d")
                                    daily[date] += 1
                                    timestamps.append(ts_epoch)
                                    has_msgs = True
                        if has_msgs:
                            sessions_found += 1
                except json.JSONDecodeError:
                    pass

            conn.close()
        except (sqlite3.Error, IOError):
            pass

    return dict(sorted(daily.items())), sorted(timestamps), sessions_found


def find_alternate_paths(cursor_dir, project_path):
    """
    When no sessions match project_path, look for workspaces with the same
    basename at different parent paths.
    """
    ws_mappings = scan_workspace_mappings(cursor_dir)
    target_name = os.path.basename(os.path.normpath(project_path))
    alternates = set()

    for _ws_id, ws_path in ws_mappings.items():
        if not ws_path:
            continue
        if (not paths_match(ws_path, project_path)
                and os.path.basename(os.path.normpath(ws_path)) == target_name):
            alternates.add(ws_path)

    # Also check global storage composerData for workspaceUri matches
    global_db = os.path.join(cursor_dir, "globalStorage", "state.vscdb")
    if os.path.exists(global_db):
        try:
            conn = sqlite3.connect(f"file:{global_db}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='cursorDiskKV'"
            )
            if cur.fetchone():
                cur.execute(
                    "SELECT value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
                )
                for (value,) in cur.fetchall():
                    try:
                        data = json.loads(value) if isinstance(value, str) else {}
                        ws_uri = data.get("workspaceUri", "")
                        ws_path = uri_to_path(ws_uri)
                        if (ws_path and not paths_match(ws_path, project_path)
                                and os.path.basename(os.path.normpath(ws_path))
                                == target_name):
                            alternates.add(ws_path)
                    except (json.JSONDecodeError, AttributeError):
                        pass
            conn.close()
        except (sqlite3.Error, IOError):
            pass

    return sorted(alternates)


def main():
    parser = argparse.ArgumentParser(
        description="Count Cursor IDE prompts per project by day"
    )
    parser.add_argument(
        "--project-path",
        help="Absolute path to the project repo (exact match)",
    )
    parser.add_argument(
        "--filter", help="Substring match on project basename"
    )
    args = parser.parse_args()

    if not args.project_path and not args.filter:
        print(json.dumps({"error": "Provide --project-path or --filter"}))
        return

    cursor_dir = get_cursor_data_dir()

    # Primary: global storage (per-message timestamps from cursorDiskKV)
    daily_global, ts_global, sessions_global = collect_from_global_storage(
        cursor_dir, args.project_path, args.filter
    )

    # Fallback: workspace storage (session-level + legacy per-message timestamps)
    seen_ts = {round(t) for t in ts_global}
    daily_ws, ts_ws, sessions_ws = collect_from_workspace_storage(
        cursor_dir, args.project_path, args.filter, seen_ts
    )

    # Merge
    all_dates = set(daily_global) | set(daily_ws)
    daily_merged = {
        date: daily_global.get(date, 0) + daily_ws.get(date, 0)
        for date in sorted(all_dates)
    }
    all_timestamps = sorted(set(ts_global + ts_ws))

    result = {
        "project_path": args.project_path or args.filter,
        "total_user_messages": sum(daily_merged.values()),
        "daily": daily_merged,
        "timestamps": all_timestamps,
        "sessions_found": sessions_global + sessions_ws,
        "sources": {
            "global_storage": sum(daily_global.values()),
            "workspace_storage": sum(daily_ws.values()),
        },
    }

    # Folder move detection
    if sum(daily_merged.values()) == 0 and args.project_path:
        alternates = find_alternate_paths(cursor_dir, args.project_path)
        if alternates:
            result["alternate_paths"] = alternates
            result["note"] = (
                f"No Cursor sessions found at {args.project_path}, "
                f"but found workspaces for "
                f"'{os.path.basename(args.project_path)}' "
                f"at {len(alternates)} other path(s). "
                f"Project may have been moved."
            )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
