#!/usr/bin/env python3
"""Update the installed Codex plugin only after a newer main version validates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:
    from .release_version import SEMVER_PATTERN
except ImportError:  # Script execution from an extracted release package.
    from release_version import SEMVER_PATTERN


PLUGIN_NAME = "sports-betting-expert"
REPOSITORY_URL = "https://github.com/rrpauls/sports-betting-expert.git"
SEMVER = SEMVER_PATTERN


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


def repository_identity(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        return None
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if len(path.split("/")) != 2:
        return None
    return parsed.hostname.casefold(), path.casefold()


def repository_matches(value: Any, expected: str) -> bool:
    expected_identity = repository_identity(expected)
    return expected_identity is not None and repository_identity(value) == expected_identity


def read_candidate_version(root: Path, repository: str = REPOSITORY_URL) -> str:
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
    if not repository_matches(manifest.get("repository"), repository):
        raise RuntimeError("candidate plugin repository does not match the configured repository")
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
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "candidate YAML validation requires PyYAML; install requirements-updater.txt"
        ) from exc
    try:
        metadata = yaml.safe_load(frontmatter.group(1))
    except yaml.YAMLError as exc:
        raise RuntimeError("candidate skill frontmatter is invalid YAML") from exc
    if (
        not isinstance(metadata, dict)
        or metadata.get("name") != PLUGIN_NAME
        or not isinstance(metadata.get("description"), str)
        or not metadata["description"].strip()
    ):
        raise RuntimeError("candidate skill frontmatter must define its name and description")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root)
    run([sys.executable, "scripts/build_release.py"], cwd=root)
    run([sys.executable, "scripts/validate_artifacts.py"], cwd=root)


def payload_digest(root: Path) -> str:
    """Hash installed release files, excluding Git metadata and generated build/cache output."""
    required = (root / "plugin.json", root / ".codex-plugin" / "plugin.json")
    if not all(path.is_file() for path in required):
        raise RuntimeError(f"plugin payload is incomplete at {root}")
    ignored = {".git", ".venv", "__pycache__", "dist"}
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and not any(part in ignored for part in path.relative_to(root).parts)
        and path.name != ".codex-marketplace-install.json"
        and path.suffix != ".pyc"
    )
    digest = hashlib.sha256()
    for path in sorted(set(files), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def tracked_tree_digest(root: Path) -> str:
    files = run(["git", "-C", str(root), "ls-files", "-z"], capture=True).stdout
    digest = hashlib.sha256()
    for name in sorted(item for item in files.split("\0") if item):
        path = root / name
        relative = name.encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def codex_cache_payload(marketplace_name: str, version: str) -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    return codex_home / "plugins" / "cache" / marketplace_name / PLUGIN_NAME / version


def pin_marketplace_plugin(root: Path, repository: str, revision: str) -> tuple[Path, bytes]:
    """Temporarily replace the plugin's mutable ref with Codex's supported immutable SHA selector."""
    path = root / ".agents" / "plugins" / "marketplace.json"
    try:
        original = path.read_bytes()
        catalog = json.loads(original)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Git marketplace snapshot has no readable Codex marketplace manifest") from exc
    matches = [
        item for item in catalog.get("plugins", [])
        if item.get("name") == PLUGIN_NAME
        and isinstance(item.get("source"), dict)
        and item["source"].get("source") == "url"
        and repository_matches(item["source"].get("url"), repository)
    ]
    if len(matches) != 1:
        raise RuntimeError("marketplace must contain exactly one root Git entry for this plugin")
    source = matches[0]["source"]
    source.pop("ref", None)
    source["sha"] = revision
    data = (json.dumps(catalog, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    _atomic_write(path, data)
    return path, original


def _atomic_write(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def restore_marketplace_manifest(path: Path, original: bytes) -> None:
    _atomic_write(path, original)


def verify_listed_payload(
    codex: str, marketplace_name: str, version: str, expected_digest: str,
    *, require_source_path: bool, installed_items: list[dict[str, Any]] | None = None,
) -> None:
    matches = [
        item for item in (installed_items if installed_items is not None else load_installed(codex))
        if item.get("marketplaceName") == marketplace_name and item.get("name") == PLUGIN_NAME
    ]
    installed = next((item for item in matches if item.get("version") == version), None)
    if installed is None:
        raise RuntimeError(f"Codex did not install {PLUGIN_NAME} {version} from {marketplace_name}")
    source = installed.get("source") or {}
    source_path = source.get("path")
    if isinstance(source_path, str) and source_path:
        reported_path = Path(source_path).resolve(strict=True)
        if not reported_path.is_dir() or payload_digest(reported_path) != expected_digest:
            raise RuntimeError("Codex installed source differs from the validated plugin bytes")
    cache_version = "local" if source.get("source") == "local" else version
    cached_path = codex_cache_payload(marketplace_name, cache_version)
    if not cached_path.is_dir():
        if require_source_path:
            raise RuntimeError(f"Codex did not expose a verifiable installed cache at {cached_path}")
        return
    if payload_digest(cached_path) != expected_digest:
        raise RuntimeError("Codex installed/cache payload differs from the validated plugin bytes")


def refresh_updater_runtime(candidate: Path) -> None:
    """Atomically replace the LaunchAgent's copied updater after a successful plugin update."""
    runtime_script = Path(__file__).resolve()
    runtime_dir = runtime_script.parent
    for name in ("update_plugin.py", "release_version.py"):
        source = candidate / "scripts" / name
        target = runtime_dir / name
        with tempfile.NamedTemporaryFile(dir=runtime_dir, prefix=f".{name}-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(source.read_bytes())
        try:
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def refresh_local_archive(
    codex: str,
    installed: dict[str, Any],
    candidate: Path,
    candidate_version: str,
    repository: str,
    installed_version: str,
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
    if (
        installed_manifest.get("name") != PLUGIN_NAME
        or not repository_matches(installed_manifest.get("repository"), repository)
    ):
        raise RuntimeError("local archive plugin path identity/repository does not match")

    with tempfile.TemporaryDirectory(prefix=f".{target.name}.update-", dir=target.parent) as temporary:
        staging = Path(temporary) / "new"
        backup = Path(temporary) / "old"
        shutil.copytree(
            candidate,
            staging,
            ignore=shutil.ignore_patterns(".git"),
        )
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
            verify_listed_payload(
                codex, marketplace_name, candidate_version, payload_digest(candidate),
                require_source_path=True, installed_items=refreshed,
            )
        except Exception as update_error:
            if target.exists():
                shutil.rmtree(target)
            os.replace(backup, target)
            try:
                run([codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}", "--json"])
                restored = [
                    item
                    for item in load_installed(codex)
                    if item.get("marketplaceName") == marketplace_name
                ]
                if not any(item.get("version") == installed_version for item in restored):
                    raise RuntimeError(
                        f"Codex did not restore the cached plugin to {installed_version}"
                    )
                verify_listed_payload(
                    codex, marketplace_name, installed_version, payload_digest(target),
                    require_source_path=True, installed_items=restored,
                )
            except Exception as rollback_error:
                raise RuntimeError(
                    f"source restored, but cached plugin rollback failed: {rollback_error}"
                ) from update_error
            raise


def marketplace_snapshot(
    codex: str, marketplace_name: str, repository: str
) -> tuple[Path, str]:
    output = run([codex, "plugin", "marketplace", "list", "--json"], capture=True).stdout
    try:
        marketplaces = json.loads(output).get("marketplaces", [])
    except (json.JSONDecodeError, AttributeError) as exc:
        raise RuntimeError("Codex returned an invalid marketplace list") from exc
    marketplace = next(
        (item for item in marketplaces if item.get("name") == marketplace_name), None
    )
    if not marketplace:
        raise RuntimeError(f"Codex did not report marketplace {marketplace_name!r}")
    source = marketplace.get("marketplaceSource") or {}
    if (
        source.get("sourceType") != "git"
        or not repository_matches(source.get("source"), repository)
    ):
        raise RuntimeError("configured marketplace is not the expected Git repository")
    root_value = marketplace.get("root")
    if not isinstance(root_value, str) or not root_value:
        raise RuntimeError("Codex did not report the Git marketplace snapshot path")
    root = Path(root_value).resolve(strict=True)
    remote = run(
        ["git", "-C", str(root), "remote", "get-url", "origin"], capture=True
    ).stdout.strip()
    if not repository_matches(remote, repository):
        raise RuntimeError("Git marketplace checkout origin does not match the repository")
    revision = run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture=True
    ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Git marketplace snapshot has no valid commit revision")
    status = run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        capture=True,
    ).stdout.splitlines()
    unexpected = [line for line in status if line[3:] != ".codex-marketplace-install.json"]
    if unexpected:
        raise RuntimeError("Git marketplace snapshot contains files outside its validated commit")
    return root, revision


def refresh_git_marketplace(
    codex: str,
    marketplace_name: str,
    candidate_version: str,
    candidate_revision: str,
    repository: str,
    installed_version: str,
) -> None:
    prior_root, prior_revision = marketplace_snapshot(codex, marketplace_name, repository)
    prior_cache = codex_cache_payload(marketplace_name, installed_version)
    if not prior_cache.is_dir():
        raise RuntimeError(f"cannot preserve prior Codex plugin cache at {prior_cache}")
    prior_payload_digest = payload_digest(prior_cache)
    with tempfile.TemporaryDirectory(prefix="sports-betting-expert-marketplace-rollback-") as backup_dir:
        prior_copy = Path(backup_dir) / "marketplace"
        cache_copy = Path(backup_dir) / "plugin-cache"
        shutil.copytree(prior_root, prior_copy, symlinks=True)
        shutil.copytree(prior_cache, cache_copy, symlinks=True)
        install_attempted = False
        try:
            run([codex, "plugin", "marketplace", "upgrade", marketplace_name, "--json"])
            snapshot, snapshot_revision = marketplace_snapshot(codex, marketplace_name, repository)
            if snapshot_revision != candidate_revision:
                raise RuntimeError(
                    "Git marketplace moved after candidate validation; no plugin was installed. "
                    "Retry the update check to validate the refreshed revision."
                )
            if read_candidate_version(snapshot, repository) != candidate_version:
                raise RuntimeError("Git marketplace snapshot version does not match the validated candidate")
            validate_candidate(snapshot)
            expected_tree_digest = tracked_tree_digest(snapshot)
            if (
                marketplace_snapshot(codex, marketplace_name, repository)[1] != candidate_revision
                or tracked_tree_digest(snapshot) != expected_tree_digest
            ):
                raise RuntimeError("Git marketplace snapshot changed during validation; no plugin was installed")
            manifest_path, manifest_backup = pin_marketplace_plugin(
                snapshot, repository, candidate_revision
            )
            install_attempted = True
            try:
                run([codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}", "--json"])
            finally:
                restore_marketplace_manifest(manifest_path, manifest_backup)
            after_snapshot, after_revision = marketplace_snapshot(codex, marketplace_name, repository)
            if after_revision != candidate_revision or tracked_tree_digest(after_snapshot) != expected_tree_digest:
                raise RuntimeError("Codex marketplace source changed during installation")
            verify_listed_payload(
                codex, marketplace_name, candidate_version, payload_digest(snapshot),
                require_source_path=True,
            )
        except Exception as update_error:
            if not install_attempted:
                raise
            failed_root = prior_root.with_name(prior_root.name + ".failed-update")
            try:
                if failed_root.exists():
                    shutil.rmtree(failed_root)
                os.replace(prior_root, failed_root)
                staging = prior_root.with_name(prior_root.name + ".rollback-staging")
                shutil.copytree(prior_copy, staging, symlinks=True)
                os.replace(staging, prior_root)
                restored_revision = run(
                    ["git", "-C", str(prior_root), "rev-parse", "HEAD"], capture=True
                ).stdout.strip()
                if restored_revision != prior_revision:
                    raise RuntimeError("marketplace rollback did not restore the previous revision")
                manifest_path, manifest_backup = pin_marketplace_plugin(
                    prior_root, repository, prior_revision
                )
                try:
                    run([codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}", "--json"])
                finally:
                    restore_marketplace_manifest(manifest_path, manifest_backup)
                if prior_cache.exists():
                    shutil.rmtree(prior_cache)
                prior_cache.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(cache_copy, prior_cache, symlinks=True)
                verify_listed_payload(
                    codex, marketplace_name, installed_version, prior_payload_digest,
                    require_source_path=True,
                )
                shutil.rmtree(failed_root, ignore_errors=True)
            except Exception as rollback_error:
                raise RuntimeError(
                    f"update failed ({update_error}); rollback of marketplace/source and Codex cache failed: {rollback_error}"
                ) from update_error
            raise


def refresh(
    codex: str,
    installed: dict[str, Any],
    candidate: Path,
    candidate_version: str,
    candidate_revision: str,
    repository: str,
) -> None:
    marketplace_name = installed.get("marketplaceName")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        raise RuntimeError("Codex did not report the installed plugin marketplace")
    source = installed.get("source") or {}
    if source.get("source") == "local":
        installed_version = installed.get("version")
        if not isinstance(installed_version, str):
            raise RuntimeError("Codex did not report the installed plugin version")
        refresh_local_archive(
            codex,
            installed,
            candidate,
            candidate_version,
            repository,
            installed_version,
        )
        return
    marketplace_source = installed.get("marketplaceSource") or {}
    if marketplace_source.get("sourceType") == "git":
        refresh_git_marketplace(
            codex,
            marketplace_name,
            candidate_version,
            candidate_revision,
            repository,
            str(installed.get("version", "")),
        )
    elif source.get("source") == "git":
        raise RuntimeError(
            "cannot safely refresh a direct Git plugin without a verifiable Git marketplace snapshot"
        )
    else:
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
            candidate_revision = run(
                ["git", "-C", str(candidate_root), "rev-parse", "HEAD"], capture=True
            ).stdout.strip()
            if not re.fullmatch(r"[0-9a-f]{40}", candidate_revision):
                raise RuntimeError("Git did not report a valid candidate commit revision")
            candidate_version = read_candidate_version(candidate_root, args.repository)
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
                refresh(
                    args.codex,
                    installed,
                    candidate_root,
                    candidate_version,
                    candidate_revision,
                    args.repository,
                )
            refresh_updater_runtime(candidate_root)

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
