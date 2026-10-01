#!/usr/bin/env python3
"""Validate release archive layout and safety properties."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
VERSION = "1.0.2"
NAME = "sports-betting-expert"


def validate_zip(path: Path, expected_prefix: str) -> None:
    with ZipFile(path) as archive:
        names = archive.namelist()
        if not names:
            raise ValueError(f"empty archive: {path.name}")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise ValueError(f"unsafe archive path: {name}")
            if expected_prefix and not name.startswith(expected_prefix):
                raise ValueError(f"unexpected archive root: {name}")
            mode = archive.getinfo(name).external_attr >> 16
            if mode & 0o170000 == 0o120000:
                raise ValueError(f"symlink not allowed: {name}")
            if "__pycache__" in pure.parts or pure.suffix == ".pyc":
                raise ValueError(f"cache file included: {name}")


def main() -> None:
    skill = DIST / f"{NAME}-skill-v{VERSION}.zip"
    codex = DIST / f"{NAME}-codex-v{VERSION}.zip"
    gemini = DIST / f"{NAME}-gemini-v{VERSION}.zip"
    grok = DIST / f"{NAME}-grok-web-v{VERSION}.md"
    validate_zip(skill, f"{NAME}/")
    validate_zip(codex, f"{NAME}-codex/")
    validate_zip(gemini, "")
    with ZipFile(skill) as archive:
        required = {
            f"{NAME}/SKILL.md",
            f"{NAME}/agents/openai.yaml",
            f"{NAME}/scripts/bet_math.py",
            f"{NAME}/references/sources-and-methods.md",
            f"{NAME}/references/markets-and-coupons.md",
        }
        if not required.issubset(archive.namelist()):
            raise ValueError("portable skill is incomplete")
    with ZipFile(codex) as archive:
        updater_prefix = f"{NAME}-codex/plugins/{NAME}/"
        required = {
            f"{updater_prefix}scripts/update_plugin.py",
            f"{updater_prefix}scripts/install_updater.py",
            f"{updater_prefix}requirements-updater.txt",
            f"{updater_prefix}launchd/com.rrpauls.sports-betting-expert-updater.plist.in",
        }
        if not required.issubset(archive.namelist()):
            raise ValueError("Codex archive is missing its updater or LaunchAgent installer")
    with ZipFile(gemini) as archive:
        if len(archive.namelist()) > 10:
            raise ValueError("Gemini bundle exceeds the documented ten-file upload budget")
        if "gemini-gem-instructions.md" not in archive.namelist():
            raise ValueError("Gemini instructions missing")
    if not grok.read_text().startswith("# Sports Betting Expert — Grok Web Project Adapter"):
        raise ValueError("invalid Grok adapter")
    expected = {}
    for line in (DIST / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    for path in (skill, codex, gemini, grok):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected.get(path.name) != actual:
            raise ValueError(f"checksum mismatch: {path.name}")
    print("Artifact validation passed")


if __name__ == "__main__":
    main()
