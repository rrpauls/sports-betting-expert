#!/usr/bin/env python3
"""Update the installed Codex plugin only after a newer main version validates."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


PLUGIN_NAME = "sports-betting-expert"
REPOSITORY_URL = "https://github.com/rrpauls/sports-betting-expert.git"
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def parse_version(value: str) -> tuple[tuple[int, int, int], tuple[tuple[int, Any], ...] | None]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"not a semantic version: {value!r}")
    core = tuple(int(match.group(index)) for index in range(1, 4))
    prerelease = match.group(4)
    if prerelease is None:
        return core, None
    identifiers: list[tuple[int, Any]] = []
    for item in prerelease.split("."):
        if item.isdigit():
            if len(item) > 1 and item.startswith("0"):
                raise ValueError(f"invalid numeric prerelease identifier in {value!r}")
            identifiers.append((0, int(item)))
        else:
            identifiers.append((1, item))
    return core, tuple(identifiers)


def is_newer(candidate: str, installed: str) -> bool:
    candidate_core, candidate_pre = parse_version(candidate)
    installed_core, installed_pre = parse_version(installed)
    if candidate_core != installed_core:
        return candidate_core > installed_core
    if candidate_pre is None:
        return installed_pre is not None
    if installed_pre is None:
        return False
    for candidate_part, installed_part in zip(candidate_pre, installed_pre):
        if candidate_part != installed_part:
            return candidate_part > installed_part
    return len(candidate_pre) > len(installed_pre)


def run(command: list[str], *, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def load_installed(codex: str) -> list[dict[str, Any]]:
    output = run([codex, "plugin", "list", "--json"], capture=True).stdout
    try:
        state = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Codex returned invalid JSON while listing the installed plugin") from exc
    return [item for item in state.get("installed", []) if item.get("name") == PLUGIN_NAME]


def read_candidate_version(root: Path) -> str:
    manifest_path = root / "plugin.json"
    skill_path = root / "skills" / PLUGIN_NAME / "SKILL.md"
    if not manifest_path.is_file() or not skill_path.is_file():
        raise RuntimeError("candidate is missing plugin.json or its nested skill")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("candidate plugin.json is unreadable or invalid JSON") from exc
    if manifest.get("name") != PLUGIN_NAME:
        raise RuntimeError(f"candidate plugin name must be {PLUGIN_NAME!r}")
    version = manifest.get("version")
    if not isinstance(version, str):
        raise RuntimeError("candidate plugin version must be a string")
    parse_version(version)
    if not manifest.get("description"):
        raise RuntimeError("candidate plugin description is missing")
    compatibility_path = root / ".codex-plugin" / "plugin.json"
    try:
        compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("candidate Codex compatibility manifest is unreadable or invalid JSON") from exc
    if compatibility.get("name") != PLUGIN_NAME or compatibility.get("version") != version:
        raise RuntimeError("candidate Codex compatibility manifest identity/version does not match")
    return version


def validate_candidate(root: Path) -> None:
    skill_path = root / "skills" / PLUGIN_NAME / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not frontmatter:
        raise RuntimeError("candidate nested skill is empty or missing YAML frontmatter")
    fields = frontmatter.group(1)
    if not re.search(r"(?m)^name:\s*\S", fields) or not re.search(
        r"(?m)^description:\s*\S", fields
    ):
        raise RuntimeError("candidate skill frontmatter must include name and description")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root)
    run([sys.executable, "scripts/validate_artifacts.py"], cwd=root)


def refresh_local_archive(
    codex: str, installed: dict[str, Any], candidate: Path, candidate_version: str
) -> None:
    marketplace_name = installed.get("marketplaceName")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        raise RuntimeError("Codex did not report the installed plugin marketplace")
    source = installed.get("source") or {}
    source_path = source.get("path")
    if not isinstance(source_path, str) or not source_path:
        raise RuntimeError("Codex did not report the local archive plugin path")
    source_target = Path(source_path)
    if source_target.is_symlink():
        raise RuntimeError("local archive plugin path must not be a symlink")
    target = source_target.resolve(strict=True)
    if not target.is_dir():
        raise RuntimeError("local archive plugin path must be a real directory")
    try:
        installed_manifest = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("local archive plugin path has no valid plugin manifest") from exc
    if installed_manifest.get("name") != PLUGIN_NAME:
        raise RuntimeError("local archive plugin path identity does not match")

    with tempfile.TemporaryDirectory(prefix=f".{target.name}.update-", dir=target.parent) as temporary:
        staging = Path(temporary) / "new"
        backup = Path(temporary) / "old"
        shutil.copytree(target, staging)
        for relative in ("plugin.json", ".codex-plugin", "skills"):
            source_item = candidate / relative
            target_item = staging / relative
            if target_item.is_dir():
                shutil.rmtree(target_item)
            elif target_item.exists():
                target_item.unlink()
            if source_item.is_dir():
                shutil.copytree(source_item, target_item)
            else:
                shutil.copy2(source_item, target_item)
        os.replace(target, backup)
        try:
            os.replace(staging, target)
            # Reinstall from the local catalog after updating its source folder so Codex refreshes its cache.
            run([codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}", "--json"])
            refreshed = [
                item
                for item in load_installed(codex)
                if item.get("marketplaceName") == marketplace_name
            ]
            if not any(item.get("version") == candidate_version for item in refreshed):
                raise RuntimeError(
                    f"Codex did not refresh the local archive cache to {candidate_version}"
                )
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            os.replace(backup, target)
            raise


def refresh(codex: str, installed: dict[str, Any], candidate: Path, candidate_version: str) -> None:
    marketplace_name = installed.get("marketplaceName")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        raise RuntimeError("Codex did not report the installed plugin marketplace")
    source = installed.get("source") or {}
    if source.get("source") == "local":
        refresh_local_archive(codex, installed, candidate, candidate_version)
        return
    marketplace_source = installed.get("marketplaceSource") or {}
    if marketplace_source.get("sourceType") == "git":
        run([codex, "plugin", "marketplace", "upgrade", marketplace_name, "--json"])
    else:
        # A GitHub plugin installed through a local archive catalog still uses the native add flow.
        run([codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}", "--json"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=os.environ.get("CODEX_CLI", shutil.which("codex")))
    parser.add_argument("--repository", default=REPOSITORY_URL)
    args = parser.parse_args()
    if not args.codex:
        parser.error("Codex CLI was not found; pass --codex or set CODEX_CLI")

    try:
        installations = load_installed(args.codex)
        if not installations:
            print(f"No installed {PLUGIN_NAME} copy found; nothing to update.")
            return 0
        for installed in installations:
            installed_version = installed.get("version")
            if not isinstance(installed_version, str):
                raise RuntimeError("Codex did not report the installed plugin version")
            parse_version(installed_version)

        with tempfile.TemporaryDirectory(prefix="sports-betting-expert-update-") as temporary:
            candidate_root = Path(temporary) / "repo"
            run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--single-branch",
                    "--branch",
                    "main",
                    args.repository,
                    str(candidate_root),
                ]
            )
            candidate_version = read_candidate_version(candidate_root)
            outdated = [
                item
                for item in installations
                if is_newer(candidate_version, str(item.get("version", "")))
            ]
            if not outdated:
                print(
                    f"No update: installed version(s) are current; main has {candidate_version}."
                )
                return 0
            validate_candidate(candidate_root)
            print(f"Validated newer version {candidate_version}; updating from main.")
            for installed in outdated:
                refresh(args.codex, installed, candidate_root, candidate_version)

        updated = load_installed(args.codex)
        stale = [
            item
            for item in outdated
            if not any(
                candidate.get("marketplaceName") == item.get("marketplaceName")
                and candidate.get("version") == candidate_version
                for candidate in updated
            )
        ]
        if stale:
            details = ", ".join(
                f"{item.get('marketplaceName')}={next((c.get('version') for c in updated if c.get('marketplaceName') == item.get('marketplaceName')), 'missing')}"
                for item in stale
            )
            raise RuntimeError(f"Codex did not update all targeted copies to {candidate_version}: {details}")
        previous = ", ".join(str(item.get("version")) for item in outdated)
        print(f"Updated {PLUGIN_NAME} from {previous} to {candidate_version}.")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Update check failed; installed plugin was not intentionally changed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
