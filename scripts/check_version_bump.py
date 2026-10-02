#!/usr/bin/env python3
"""Require a non-regressing semantic version for distributed payload changes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

try:
    from .release_version import SEMVER_PATTERN as SEMVER
except ImportError:
    from release_version import SEMVER_PATTERN as SEMVER


RELEASE_PATHS = (
    ".agents/plugins/marketplace.json", ".codex-plugin/", "plugin.json", "skills/",
    "scripts/build_release.py", "scripts/validate_artifacts.py", "scripts/release_version.py",
    "scripts/update_plugin.py", "scripts/install_updater.py", "scripts/bet_math.py",
    "scripts/statshawk_evidence.py", "requirements-updater.txt", "launchd/",
    "README.md", "INSTALL.md", "INSTALL-GEMINI.md", "MIGRATION.md", "LICENSE",
)


def version_key(value: str) -> tuple[tuple[int, int, int], tuple[tuple[int, object], ...] | None]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"invalid semantic version: {value!r}")
    core = tuple(int(match.group(i)) for i in range(1, 4))
    prerelease = match.group(4)
    if prerelease is None:
        return core, None
    identifiers = []
    for item in prerelease.split("."):
        if item.isdigit():
            if len(item) > 1 and item.startswith("0"):
                raise ValueError(f"invalid numeric prerelease identifier: {value!r}")
            identifiers.append((0, int(item)))
        else:
            identifiers.append((1, item))
    return core, tuple(identifiers)


def newer(left: str, right: str) -> bool:
    left_core, left_pre = version_key(left)
    right_core, right_pre = version_key(right)
    if left_core != right_core:
        return left_core > right_core
    if left_pre is None:
        return right_pre is not None
    if right_pre is None:
        return False
    for a, b in zip(left_pre, right_pre):
        if a != b:
            return a > b
    return len(left_pre) > len(right_pre)


def manifest_version(contents: str) -> str:
    value = json.loads(contents).get("version")
    if not isinstance(value, str):
        raise ValueError("plugin.json must contain a string version")
    version_key(value)
    return value


def check(base_ref: str) -> None:
    base_json = subprocess.run(
        ["git", "show", f"{base_ref}:plugin.json"], check=True, text=True, capture_output=True
    ).stdout
    base_version = manifest_version(base_json)
    current_version = manifest_version(open("plugin.json", encoding="utf-8").read())
    if newer(base_version, current_version):
        raise ValueError(f"version regression: base is {base_version}, current is {current_version}")
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"], check=True, text=True, capture_output=True
    ).stdout.splitlines()
    distributed = [
        path for path in changed
        if any(path == prefix or path.startswith(prefix) for prefix in RELEASE_PATHS)
    ]
    if distributed and not newer(current_version, base_version):
        raise ValueError(
            f"distributed payload changed without a newer semantic version ({base_version}): "
            + ", ".join(distributed)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()
    try:
        check(args.base_ref)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Version check failed: {exc}", file=sys.stderr)
        return 1
    print("Release version is valid for the changed files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
