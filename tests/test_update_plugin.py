import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from scripts import update_plugin
from scripts.update_plugin import is_newer, parse_version


REPOSITORY = "https://github.com/rrpauls/sports-betting-expert.git"


def write_plugin(root: Path, *, version: str = "1.0.3", repository: str = REPOSITORY) -> None:
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "sports-betting-expert",
        "version": version,
        "repository": repository,
        "description": "Test plugin",
    }
    (root / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    compatibility = {"name": "sports-betting-expert", "version": version}
    codex_plugin = root / ".codex-plugin"
    codex_plugin.mkdir(parents=True, exist_ok=True)
    (codex_plugin / "plugin.json").write_text(json.dumps(compatibility), encoding="utf-8")
    skill = root / "skills" / "sports-betting-expert"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        "---\nname: sports-betting-expert\ndescription: Test skill\n---\n",
        encoding="utf-8",
    )


class UpdatePluginVersionTests(unittest.TestCase):
    def test_stable_release_is_newer_than_previous_patch(self):
        self.assertTrue(is_newer("1.0.3", "1.0.2"))

    def test_same_or_older_version_is_not_an_update(self):
        self.assertFalse(is_newer("1.0.2", "1.0.2"))
        self.assertFalse(is_newer("1.0.1", "1.0.2"))

    def test_stable_release_is_newer_than_prerelease(self):
        self.assertTrue(is_newer("2.0.0", "2.0.0-rc.1"))
        self.assertFalse(is_newer("2.0.0-rc.2", "2.0.0"))

    def test_prerelease_order_follows_semver_identifiers(self):
        self.assertTrue(is_newer("1.0.0-rc.2", "1.0.0-rc.1"))
        self.assertTrue(is_newer("1.0.0-rc.1", "1.0.0-beta.9"))

    def test_invalid_versions_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_version("v1.0.3")
        with self.assertRaises(ValueError):
            parse_version("1.0")
        with self.assertRaises(ValueError):
            parse_version("1.0.0-rc.01")


class UpdatePluginRefreshTests(unittest.TestCase):
    def test_local_archive_replaces_complete_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "installed"
            candidate = root / "candidate"
            write_plugin(target, version="1.0.2")
            (target / "commands" / "removed.md").parent.mkdir()
            (target / "commands" / "removed.md").write_text("obsolete", encoding="utf-8")
            (target / "local-note.txt").write_text("old source", encoding="utf-8")
            write_plugin(candidate)
            (candidate / "agents" / "new.md").parent.mkdir()
            (candidate / "agents" / "new.md").write_text("new component", encoding="utf-8")
            (candidate / "commands" / "added.md").parent.mkdir()
            (candidate / "commands" / "added.md").write_text("new command", encoding="utf-8")
            (candidate / ".git").mkdir()

            installed = {
                "marketplaceName": "sports-betting-expert",
                "source": {"source": "local", "path": str(target)},
            }
            with (
                patch.object(update_plugin, "run") as run_mock,
                patch.object(
                    update_plugin,
                    "load_installed",
                    return_value=[
                        {
                            "name": "sports-betting-expert",
                            "marketplaceName": "sports-betting-expert",
                            "version": "1.0.3",
                        }
                    ],
                ),
            ):
                update_plugin.refresh_local_archive(
                    "codex", installed, candidate, "1.0.3", REPOSITORY
                )

            self.assertTrue((target / "agents" / "new.md").is_file())
            self.assertTrue((target / "commands" / "added.md").is_file())
            self.assertFalse((target / "commands" / "removed.md").exists())
            self.assertFalse((target / "local-note.txt").exists())
            self.assertFalse((target / ".git").exists())
            run_mock.assert_called_once_with(
                ["codex", "plugin", "add", "sports-betting-expert@sports-betting-expert", "--json"]
            )

    def test_local_archive_rejects_a_different_repository_before_replacing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "installed"
            candidate = root / "candidate"
            write_plugin(target, version="1.0.2", repository="https://github.com/fork/sports-betting-expert")
            write_plugin(candidate)
            marker = target / "local-note.txt"
            marker.write_text("leave intact", encoding="utf-8")
            installed = {
                "marketplaceName": "sports-betting-expert",
                "source": {"source": "local", "path": str(target)},
            }

            with patch.object(update_plugin, "run") as run_mock:
                with self.assertRaisesRegex(RuntimeError, "identity/repository"):
                    update_plugin.refresh_local_archive(
                        "codex", installed, candidate, "1.0.3", REPOSITORY
                    )

            self.assertEqual(marker.read_text(encoding="utf-8"), "leave intact")
            run_mock.assert_not_called()

    def test_git_marketplace_validates_the_refreshed_pinned_snapshot_before_add(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            write_plugin(snapshot)
            revision = "a" * 40
            marketplace_list = {
                "marketplaces": [
                    {
                        "name": "sports-betting-expert",
                        "root": str(snapshot),
                        "marketplaceSource": {
                            "sourceType": "git",
                            "source": REPOSITORY,
                        },
                    }
                ]
            }
            events = []

            def fake_run(command, *, cwd=None, capture=False):
                if command[1:4] == ["plugin", "marketplace", "upgrade"]:
                    events.append("upgrade")
                    return CompletedProcess(command, 0, stdout="", stderr="")
                if command[1:4] == ["plugin", "marketplace", "list"]:
                    events.append("list")
                    return CompletedProcess(command, 0, stdout=json.dumps(marketplace_list), stderr="")
                if command[:2] == ["git", "-C"]:
                    if command[-2:] == ["get-url", "origin"]:
                        events.append("remote")
                        return CompletedProcess(command, 0, stdout=f"{REPOSITORY}\n", stderr="")
                    if command[-2:] == ["--porcelain=v1", "--untracked-files=all"]:
                        events.append("status")
                        return CompletedProcess(
                            command, 0, stdout="?? .codex-marketplace-install.json\n", stderr=""
                        )
                    events.append("revision")
                    return CompletedProcess(command, 0, stdout=f"{revision}\n", stderr="")
                if command[1:3] == ["plugin", "add"]:
                    events.append("add")
                    return CompletedProcess(command, 0, stdout="", stderr="")
                self.fail(f"unexpected command: {command}")

            def validate(root_to_validate):
                self.assertEqual(root_to_validate, snapshot.resolve())
                events.append("validate")

            with (
                patch.object(update_plugin, "run", side_effect=fake_run),
                patch.object(update_plugin, "validate_candidate", side_effect=validate),
            ):
                update_plugin.refresh_git_marketplace(
                    "codex", "sports-betting-expert", "1.0.3", revision, REPOSITORY
                )

            self.assertEqual(
                events,
                [
                    "upgrade",
                    "list",
                    "remote",
                    "revision",
                    "status",
                    "validate",
                    "list",
                    "remote",
                    "revision",
                    "status",
                    "add",
                ],
            )

    def test_git_marketplace_does_not_install_if_main_moves_after_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            write_plugin(snapshot)
            marketplace_list = {
                "marketplaces": [
                    {
                        "name": "sports-betting-expert",
                        "root": str(snapshot),
                        "marketplaceSource": {
                            "sourceType": "git",
                            "source": REPOSITORY,
                        },
                    }
                ]
            }

            def fake_run(command, *, cwd=None, capture=False):
                if command[1:4] == ["plugin", "marketplace", "upgrade"]:
                    return CompletedProcess(command, 0, stdout="", stderr="")
                if command[1:4] == ["plugin", "marketplace", "list"]:
                    return CompletedProcess(command, 0, stdout=json.dumps(marketplace_list), stderr="")
                if command[:2] == ["git", "-C"]:
                    if command[-2:] == ["get-url", "origin"]:
                        return CompletedProcess(command, 0, stdout=f"{REPOSITORY}\n", stderr="")
                    if command[-2:] == ["--porcelain=v1", "--untracked-files=all"]:
                        return CompletedProcess(
                            command, 0, stdout="?? .codex-marketplace-install.json\n", stderr=""
                        )
                    return CompletedProcess(command, 0, stdout=f"{'b' * 40}\n", stderr="")
                if command[1:3] == ["plugin", "add"]:
                    self.fail("must not install an unvalidated revision")
                self.fail(f"unexpected command: {command}")

            with patch.object(update_plugin, "run", side_effect=fake_run):
                with self.assertRaisesRegex(RuntimeError, "moved after candidate validation"):
                    update_plugin.refresh_git_marketplace(
                        "codex", "sports-betting-expert", "1.0.3", "a" * 40, REPOSITORY
                    )

    def test_direct_git_source_without_snapshot_fails_closed(self):
        installed = {
            "marketplaceName": "personal",
            "source": {"source": "git", "url": REPOSITORY, "ref": "main"},
        }
        with patch.object(update_plugin, "run") as run_mock:
            with self.assertRaisesRegex(RuntimeError, "without a verifiable Git marketplace snapshot"):
                update_plugin.refresh(
                    "codex", installed, Path("candidate"), "1.0.3", "a" * 40, REPOSITORY
                )
        run_mock.assert_not_called()

    def test_git_marketplace_rejects_modified_snapshot_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary) / "snapshot"
            snapshot.mkdir()
            marketplace_list = {
                "marketplaces": [
                    {
                        "name": "sports-betting-expert",
                        "root": str(snapshot),
                        "marketplaceSource": {
                            "sourceType": "git",
                            "source": REPOSITORY,
                        },
                    }
                ]
            }

            def fake_run(command, *, cwd=None, capture=False):
                if command[1:4] == ["plugin", "marketplace", "list"]:
                    return CompletedProcess(command, 0, stdout=json.dumps(marketplace_list), stderr="")
                if command[-2:] == ["get-url", "origin"]:
                    return CompletedProcess(command, 0, stdout=f"{REPOSITORY}\n", stderr="")
                if command[-2:] == ["--porcelain=v1", "--untracked-files=all"]:
                    return CompletedProcess(command, 0, stdout=" M plugin.json\n", stderr="")
                if command[-1:] == ["HEAD"]:
                    return CompletedProcess(command, 0, stdout=f"{'a' * 40}\n", stderr="")
                self.fail(f"unexpected command: {command}")

            with patch.object(update_plugin, "run", side_effect=fake_run):
                with self.assertRaisesRegex(RuntimeError, "outside its validated commit"):
                    update_plugin.marketplace_snapshot(
                        "codex", "sports-betting-expert", REPOSITORY
                    )


if __name__ == "__main__":
    unittest.main()
