#!/usr/bin/env python3
"""Build deterministic host artifacts from the canonical skill."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


try:
    from .release_version import VERSION
except ImportError:  # Script execution from a repository or extracted release root.
    from release_version import VERSION
PLUGIN_NAME = "sports-betting-expert"
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / PLUGIN_NAME
DIST = REPO_ROOT / "dist"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def archive_info(name: str) -> ZipInfo:
    info = ZipInfo(name, date_time=FIXED_TIME)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def add_bytes(archive: ZipFile, name: str, data: bytes) -> None:
    archive.writestr(archive_info(name), data)


def files_under(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def build_skill_zip(output: Path) -> None:
    with ZipFile(output, "w") as archive:
        for source in files_under(SKILL_ROOT):
            relative = source.relative_to(SKILL_ROOT).as_posix()
            add_bytes(archive, f"{PLUGIN_NAME}/{relative}", source.read_bytes())


def local_marketplace() -> bytes:
    data = {
        "name": PLUGIN_NAME,
        "interface": {"displayName": "Sports Betting Expert"},
        "plugins": [{
            "name": PLUGIN_NAME,
            "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }],
    }
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def build_codex_zip(output: Path) -> None:
    root = f"{PLUGIN_NAME}-codex"
    plugin_prefix = f"{root}/plugins/{PLUGIN_NAME}"
    fixed_files = [
        REPO_ROOT / ".codex-plugin" / "plugin.json",
        REPO_ROOT / "plugin.json",
        REPO_ROOT / "LICENSE",
        REPO_ROOT / "README.md",
        REPO_ROOT / "INSTALL.md",
        REPO_ROOT / "MIGRATION.md",
        REPO_ROOT / "requirements-updater.txt",
        REPO_ROOT / "scripts" / "install_updater.py",
        REPO_ROOT / "scripts" / "update_plugin.py",
        REPO_ROOT / "scripts" / "release_version.py",
        REPO_ROOT / "launchd" / "com.rrpauls.sports-betting-expert-updater.plist.in",
    ]
    with ZipFile(output, "w") as archive:
        add_bytes(archive, f"{root}/.agents/plugins/marketplace.json", local_marketplace())
        add_bytes(archive, f"{root}/INSTALL.md", (REPO_ROOT / "INSTALL.md").read_bytes())
        for source in fixed_files:
            relative = source.relative_to(REPO_ROOT).as_posix()
            add_bytes(archive, f"{plugin_prefix}/{relative}", source.read_bytes())
        for source in files_under(SKILL_ROOT):
            relative = source.relative_to(REPO_ROOT).as_posix()
            add_bytes(archive, f"{plugin_prefix}/{relative}", source.read_bytes())


def gemini_instructions() -> str:
    return """# Sports Betting Expert — Gem Instructions

## Persona

You are an evidence-led sports betting analyst. Default to Russian unless the user requests another language.

## Task

Use `canonical-skill.md` in Knowledge as the governing workflow. Select the mode matching the request: match research, accumulator construction, coupon review, live-position analysis, or a direct market/calculation explanation. Use `sources-and-methods.md` for evidence and arithmetic and `markets-and-coupons.md` for settlement, correlation, cash-out and hedging.

## Context

Current schedules, odds, injuries, lineups and live state require current sources or a clearly labeled user-provided snapshot. Separate facts, reports, assumptions and assessment. Never invent a price, statistic, model run or claimed edge. Never recommend a new pre-match tennis bet or include tennis in a pre-match accumulator; tennis betting selections are always live-only. The optional `priority-live-tennis` profile changes the sport screening order and is off unless the user explicitly enables it.

## Format

Lead with the verdict and main reason. For multiple selections, use a compact table with event time, exact market, offered price/source/time, decision, rationale and main risk. Keep maximum payout, net profit and expected return distinct. Say when the evidence supports waiting or passing.
"""


def gemini_knowledge() -> dict[str, bytes]:
    return {
        "canonical-skill.md": (SKILL_ROOT / "SKILL.md").read_bytes(),
        "sources-and-methods.md": (SKILL_ROOT / "references/sources-and-methods.md").read_bytes(),
        "markets-and-coupons.md": (SKILL_ROOT / "references/markets-and-coupons.md").read_bytes(),
        "priority-live-tennis.md": (SKILL_ROOT / "references/profiles/priority-live-tennis.md").read_bytes(),
    }


def build_gemini_zip(output: Path) -> None:
    with ZipFile(output, "w") as archive:
        add_bytes(archive, "gemini-gem-instructions.md", gemini_instructions().encode())
        add_bytes(archive, "INSTALL-GEMINI.md", (REPO_ROOT / "INSTALL-GEMINI.md").read_bytes())
        for name, data in sorted(gemini_knowledge().items()):
            add_bytes(archive, f"gemini-knowledge/{name}", data)


def build_grok_adapter(output: Path) -> None:
    parts = [
        "# Sports Betting Expert — Grok Web Project Adapter\n",
        "Upload this generated file to a Grok Project. Apply the canonical workflow below to requests inside that Project. It is not an account-wide skill. Default to Russian unless the user asks otherwise. Tennis betting selections are always live-only. The optional `priority-live-tennis` sport-order profile is inactive unless explicitly enabled.\n",
        (SKILL_ROOT / "SKILL.md").read_text(),
        (SKILL_ROOT / "references/sources-and-methods.md").read_text(),
        (SKILL_ROOT / "references/markets-and-coupons.md").read_text(),
        (SKILL_ROOT / "references/profiles/priority-live-tennis.md").read_text(),
    ]
    output.write_text("\n\n".join(parts).rstrip() + "\n")


def write_checksums(outputs: list[Path]) -> None:
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in sorted(outputs)]
    (DIST / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for old in DIST.glob(f"{PLUGIN_NAME}-*"):
        if old.is_file() or old.is_symlink():
            old.unlink()
        elif old.is_dir():
            import shutil

            shutil.rmtree(old)
    (DIST / "SHA256SUMS").unlink(missing_ok=True)
    outputs = [
        DIST / f"{PLUGIN_NAME}-skill-v{VERSION}.zip",
        DIST / f"{PLUGIN_NAME}-codex-v{VERSION}.zip",
        DIST / f"{PLUGIN_NAME}-gemini-v{VERSION}.zip",
        DIST / f"{PLUGIN_NAME}-grok-web-v{VERSION}.md",
    ]
    build_skill_zip(outputs[0])
    build_codex_zip(outputs[1])
    build_gemini_zip(outputs[2])
    build_grok_adapter(outputs[3])
    write_checksums(outputs)


if __name__ == "__main__":
    main()
