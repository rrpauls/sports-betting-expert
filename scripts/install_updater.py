#!/usr/bin/env python3
"""Install, inspect, or remove the per-user Sports Betting Expert updater."""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any, Callable
try:
    from . import schedulers
except ImportError:
    import schedulers


LABEL = "com.rrpauls.sports-betting-expert-updater"
TEMPLATE = Path(__file__).resolve().parents[1] / "launchd" / f"{LABEL}.plist.in"
CHATGPT_CODEX = Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/"
    "CodexCLI.app/Contents/MacOS/codex"
)
STATE_NAME = "Sports Betting Expert Updater"
Runner = Callable[..., subprocess.CompletedProcess[str]]


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
    codex_home: Path | None = None,
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
        "@CODEX_HOME@": str((codex_home or (home / ".codex")).expanduser().resolve()),
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


def launchctl(action: str, agent: Path, *, uid: int, runner: Runner = subprocess.run) -> subprocess.CompletedProcess[str]:
    return runner(
        ["launchctl", action, f"gui/{uid}", str(agent)],
        check=action != "bootout",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def agent_is_registered(*, uid: int, runner: Runner = subprocess.run) -> bool:
    result = runner(
        ["launchctl", "print", f"gui/{uid}/{LABEL}"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def _ensure_runtime(source_root: Path, state_root: Path, python: Path) -> Path:
    scripts = state_root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ("update_plugin.py", "release_version.py", "schedulers.py"):
        shutil.copy2(source_root / "scripts" / name, scripts / name)
    shutil.copy2(source_root / "requirements-updater.txt", state_root / "requirements-updater.txt")
    # release_version reads this metadata even in the standalone updater runtime.
    shutil.copy2(source_root / "plugin.json", state_root / "plugin.json")
    environment = state_root / "venv"
    runtime_python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not runtime_python.is_file():
        venv.EnvBuilder(with_pip=True, clear=False).create(environment)
    subprocess.run(
        [str(runtime_python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(state_root / "requirements-updater.txt")],
        check=True,
        text=True,
    )
    if not python.is_file():
        raise RuntimeError("the Python interpreter used for updater setup is unavailable")
    return runtime_python


def install(
    *, home: Path, source_root: Path, codex: Path, python: Path = Path(sys.executable),
    runner: Runner = subprocess.run, template: Path = TEMPLATE,
) -> Path:
    state_root = home / "Library" / "Application Support" / STATE_NAME
    runtime_python = _ensure_runtime(source_root, state_root, python)
    updater = state_root / "scripts" / "update_plugin.py"
    agent = create_launch_agent(
        home=home, python=runtime_python, updater=updater, codex=codex,
        path_value=os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        codex_home=Path(os.environ.get("CODEX_HOME", str(home / ".codex"))), template=template,
    )
    launchctl("bootout", agent, uid=getattr(os, "getuid", lambda: 0)(), runner=runner)
    launchctl("bootstrap", agent, uid=getattr(os, "getuid", lambda: 0)(), runner=runner)
    if not agent_is_registered(uid=getattr(os, "getuid", lambda: 0)(), runner=runner):
        raise RuntimeError("LaunchAgent was written but launchd does not report it as registered")
    return agent


def uninstall(*, home: Path, runner: Runner = subprocess.run) -> None:
    agent = home / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    launchctl("bootout", agent, uid=getattr(os, "getuid", lambda: 0)(), runner=runner)
    agent.unlink(missing_ok=True)
    shutil.rmtree(home / "Library" / "Application Support" / STATE_NAME, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("install", "status", "update-now", "uninstall"), default="install")
    parser.add_argument("--codex", help="Codex CLI executable; otherwise discover it")
    args = parser.parse_args()
    home = Path.home()
    agent = home / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    try:
        state = schedulers.state_root(home, sys.platform)
        if args.action == "status":
            registered = (agent_is_registered(uid=getattr(os, "getuid", lambda: 0)()) if sys.platform == "darwin"
                          else schedulers.scheduler_status(sys.platform))
            location = (str(agent) if sys.platform == "darwin" else
                        str(home / ".config/systemd/user" / f"{schedulers.UNIT}.timer")
                        if sys.platform.startswith("linux") else schedulers.LABEL)
            print(f"Updater scheduler: {'registered' if registered else 'not registered'} ({location})")
            return 0 if registered else 1
        if args.action == "uninstall":
            if sys.platform == "darwin":
                uninstall(home=home)
            else:
                schedulers.uninstall_scheduler(sys.platform, home)
                shutil.rmtree(state, ignore_errors=True)
            print("Updater scheduler and its dedicated runtime were removed.")
            return 0
        codex = find_codex(args.codex)
        source_root = Path(__file__).resolve().parents[1]
        if args.action == "update-now":
            command = [sys.executable, str(source_root / "scripts/update_plugin.py"), "--codex", str(codex)]
            return subprocess.run(command, check=False).returncode
        if sys.platform == "darwin":
            agent = install(home=home, source_root=source_root, codex=codex)
        else:
            runtime = _ensure_runtime(source_root, state, Path(sys.executable))
            codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser().resolve()
            command = [str(runtime), str(state / "scripts/update_plugin.py"), "--codex", str(codex),
                       "--codex-home", str(codex_home)]
            agent = schedulers.install_scheduler(sys.platform, home, command, codex_home)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError, plistlib.InvalidFileException) as exc:
        print(f"Updater setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Updater installed and registered: {agent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
