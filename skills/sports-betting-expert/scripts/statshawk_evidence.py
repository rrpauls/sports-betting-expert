#!/usr/bin/env python3
"""Create a bounded, timestamped evidence snapshot from StatsHawk MCP output."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
TOOLS = {
    "get_box_score", "get_injury_history", "get_mlb_matchups", "get_play_by_play",
    "get_player_props", "get_standings", "get_stat_capabilities", "get_team_roster",
    "search_games", "search_player",
}
ALLOWED_KEYS = {
    "id", "game_id", "person_id", "player_id", "team_id", "league", "season",
    "date", "start_time", "status", "phase", "period", "clock", "home", "away",
    "home_team", "away_team", "team", "opponent", "player", "name", "position",
    "injury", "designation", "stat", "stat_id", "value", "rank", "record", "score",
    "games_played", "sample_size", "unit", "description", "capabilities", "results",
    "data", "items",
}
SENSITIVE_PARTS = {"token", "secret", "password", "cookie", "authorization", "email", "session"}


def timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("--observed-at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("--observed-at must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")


def project(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        raise ValueError("input nesting exceeds eight levels")
    if isinstance(value, dict):
        output = {}
        for key in sorted(value):
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_PARTS):
                raise ValueError(f"sensitive field is not allowed: {key}")
            if normalized in ALLOWED_KEYS:
                output[str(key)] = project(value[key], depth + 1)
        return output
    if isinstance(value, list):
        if len(value) > 2_000:
            raise ValueError("input contains more than 2000 list items")
        return [project(item, depth + 1) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, str) and len(value) > 2_000:
            return value[:2_000]
        return value
    return str(value)[:2_000]


def snapshot(tool: str, league: str, observed_at: str, payload: Any) -> dict[str, Any]:
    if tool not in TOOLS:
        raise ValueError(f"unsupported StatsHawk tool: {tool}")
    if not league or len(league) > 32:
        raise ValueError("league must be a short competition code")
    return {
        "schema_version": SCHEMA_VERSION,
        "provider": "statshawk",
        "tool": tool,
        "league": league.lower(),
        "observed_at": timestamp(observed_at),
        "read_only": True,
        "data": project(payload),
    }


def write_private(path: Path, value: dict[str, Any]) -> None:
    if path.exists() and path.is_symlink():
        raise ValueError(f"refusing symlinked output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        else:
            path.chmod(0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", required=True, choices=sorted(TOOLS))
    parser.add_argument("--league", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--input", required=True, help="StatsHawk JSON file or - for stdin")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
        write_private(Path(args.output), snapshot(args.tool, args.league, args.observed_at, json.loads(raw)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
