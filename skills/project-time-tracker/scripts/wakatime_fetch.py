#!/usr/bin/env python3
"""
Fetch WakaTime coding time from the WakaTime API.

Reads API key from ~/.wakatime.cfg [settings] api_key.

Usage:
  python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02
  python3 wakatime_fetch.py --start 2026-01-15 --end 2026-02-02 --project snow

Output: JSON with daily summaries and per-project breakdown.
"""

import configparser
import os
import json
import sys
import argparse
import urllib.request
import urllib.parse
import base64
from datetime import datetime, timedelta


def read_api_key():
    cfg_path = os.path.expanduser("~/.wakatime.cfg")
    if not os.path.exists(cfg_path):
        return None
    config = configparser.ConfigParser()
    config.read(cfg_path)
    return config.get("settings", "api_key", fallback=None)


def api_request(endpoint, api_key, params=None):
    base_url = "https://api.wakatime.com/api/v1"
    url = f"{base_url}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    # WakaTime uses Basic Auth with base64-encoded API key
    encoded_key = base64.b64encode(api_key.encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {encoded_key}",
        "User-Agent": "project-time-tracker-skill/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_summaries(api_key, start, end, project=None):
    params = {"start": start, "end": end}
    if project:
        params["project"] = project
    data = api_request("/users/current/summaries", api_key, params)
    if "error" in data:
        return data

    # Parse daily summaries
    daily = []
    project_totals = {}
    total_seconds = 0

    for day in data.get("data", []):
        date = day.get("range", {}).get("date", "")
        day_seconds = day.get("grand_total", {}).get("total_seconds", 0)
        total_seconds += day_seconds

        if day_seconds > 0:
            daily.append({
                "date": date,
                "hours": round(day_seconds / 3600, 2),
                "text": day.get("grand_total", {}).get("text", ""),
            })

        # Aggregate per-project
        for proj in day.get("projects", []):
            pname = proj.get("name", "unknown")
            psecs = proj.get("total_seconds", 0)
            project_totals[pname] = project_totals.get(pname, 0) + psecs

    return {
        "start": start,
        "end": end,
        "total_hours": round(total_seconds / 3600, 2),
        "daily": daily,
        "projects": [
            {"project": k, "hours": round(v / 3600, 2)}
            for k, v in sorted(project_totals.items(), key=lambda x: -x[1])
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch WakaTime coding stats")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--project", help="Filter by project name")
    args = parser.parse_args()

    api_key = read_api_key()
    if not api_key:
        print(json.dumps({"error": "No WakaTime API key found in ~/.wakatime.cfg"}))
        sys.exit(1)

    result = fetch_summaries(api_key, args.start, args.end, args.project)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
