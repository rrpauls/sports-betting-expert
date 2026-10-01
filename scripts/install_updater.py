#!/usr/bin/env python3
"""Create a user-specific macOS LaunchAgent for the sports betting updater."""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


LABEL = "com.rrpauls.sports-betting-expert-updater"
TEMPLATE = Path(__file__).resolve().parents[1] / "launchd" / f"{LABEL}.plist.in"
CHATGPT_CODEX = Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/"
    "CodexCLI.app/Contents/MacOS/codex"
)


def find_codex(explicit: str | None) -> Path:
    candidates = [Path(explicit).expanduser()] if explicit else []
    if not explicit:
        found = shutil.which("codex")
        if found:
            candidates.append(Path(found))
        candidates.append(CHATGPT_CODEX)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return resolved
    raise RuntimeError("Codex CLI was not found; pass its executable path with --codex")


def replace_tokens(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [replace_tokens(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: replace_tokens(item, replacements) for key, item in value.items()}
    return value


def create_launch_agent(
    *,
    home: Path,
    python: Path,
    updater: Path,
    codex: Path,
    path_value: str,
    template: Path = TEMPLATE,
) -> Path:
    with template.open("rb") as stream:
        payload = plistlib.load(stream)
    logs = home / "Library" / "Logs"
    launch_agents = home / "Library" / "LaunchAgents"
    logs.mkdir(parents=True, exist_ok=True)
    launch_agents.mkdir(parents=True, exist_ok=True)
    replacements = {
        "@PYTHON_EXECUTABLE@": str(python.resolve()),
        "@UPDATER_SCRIPT@": str(updater.resolve()),
        "@CODEX_EXECUTABLE@": str(codex.resolve()),
        "@HOME_PATH@": str(home.resolve()),
        "@PATH_VALUE@": path_value,
        "@LOG_OUT@": str(logs / "sports-betting-expert-updater.log"),
        "@LOG_ERROR@": str(logs / "sports-betting-expert-updater.err"),
    }
    rendered = replace_tokens(payload, replacements)
    target = launch_agents / f"{LABEL}.plist"
    with tempfile.NamedTemporaryFile(dir=launch_agents, prefix=f".{LABEL}-", delete=False) as stream:
        temporary = Path(stream.name)
        plistlib.dump(rendered, stream, fmt=plistlib.FMT_XML, sort_keys=False)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", help="Codex CLI executable; otherwise discover it")
    args = parser.parse_args()
    try:
        codex = find_codex(args.codex)
        updater = Path(__file__).resolve().with_name("update_plugin.py")
        agent = create_launch_agent(
            home=Path.home(),
            python=Path(sys.executable),
            updater=updater,
            codex=codex,
            path_value=os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        )
    except (OSError, RuntimeError, plistlib.InvalidFileException) as exc:
        print(f"Could not create updater LaunchAgent: {exc}", file=sys.stderr)
        return 1
    print(f"Created {agent}")
    print(f"Load it with: launchctl bootstrap gui/{os.getuid()} {agent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
