import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from scripts import update_plugin
from scripts.update_plugin import is_newer, parse_version


REPOSITORY = "https://github.com/rrpauls/sports-betting-expert.git"
PLUGIN_NAME = update_plugin.PLUGIN_NAME


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
    catalog = root / ".agents" / "plugins"
    catalog.mkdir(parents=True, exist_ok=True)
    (catalog / "marketplace.json").write_text(json.dumps({
        "name": PLUGIN_NAME,
        "plugins": [{
            "name": PLUGIN_NAME,
            "source": {"source": "url", "url": repository, "ref": "main"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }],
    }), encoding="utf-8")
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


class UpdaterDecisionFlowTests(unittest.TestCase):
    def run_candidate(self, version: str, *, validate_error: Exception | None = None, copies: int = 1):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        candidate = root / "candidate-source"
        write_plugin(candidate, version=version)
        old = [{
            "name": "sports-betting-expert", "marketplaceName": "sports-betting-expert",
            "version": "1.0.2", "source": {"source": "git", "url": REPOSITORY},
            "marketplaceSource": {"sourceType": "git", "source": REPOSITORY},
        }]
        old = [{**old[0], "marketplaceName": f"market-{index}"} for index in range(copies)]
        new = [{**item, "version": version} for item in old]
        refresh_calls = []

        def fake_run(command, *, cwd=None, capture=False):
            if command[:2] == ["git", "clone"]:
                shutil.copytree(candidate, Path(command[-1]))
                return CompletedProcess(command, 0, "", "")
            if command[-2:] == ["rev-parse", "HEAD"]:
                return CompletedProcess(command, 0, "a" * 40 + "\n", "")
            self.fail(f"unexpected updater command: {command}")

        with (
            patch.object(update_plugin, "run", side_effect=fake_run),
            patch.object(update_plugin, "load_installed", side_effect=[old, new]),
            patch.object(update_plugin, "validate_candidate", side_effect=validate_error),
            patch.object(update_plugin, "refresh", side_effect=lambda *args: refresh_calls.append(args)),
            patch.object(update_plugin, "refresh_updater_runtime"),
            patch.object(sys, "argv", ["update_plugin.py", "--codex", "codex"]),
        ):
            result = update_plugin.main()
        temporary.cleanup()
        return result, refresh_calls

    def test_all_installed_copies_are_updated(self):
        result, calls = self.run_candidate("1.0.3", copies=3)
        self.assertEqual(result, 0)
        self.assertEqual({call[1]["marketplaceName"] for call in calls}, {"market-0", "market-1", "market-2"})

    def test_no_installed_plugin_is_a_noop_without_cloning(self):
        with (patch.object(update_plugin, "load_installed", return_value=[]),
              patch.object(update_plugin, "run") as run,
              patch.object(sys, "argv", ["update_plugin.py", "--codex", "codex"])):
            self.assertEqual(update_plugin.main(), 0)
            run.assert_not_called()

    def test_old_install_updates_only_after_candidate_validation(self):
        result, calls = self.run_candidate("1.0.3")
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][3], "1.0.3")
        self.assertEqual(calls[0][4], "a" * 40)

    def test_same_and_older_candidate_versions_do_not_change_install(self):
        same_result, same_calls = self.run_candidate("1.0.2")
        old_result, old_calls = self.run_candidate("1.0.1")
        self.assertEqual((same_result, old_result), (0, 0))
        self.assertEqual(same_calls, [])
        self.assertEqual(old_calls, [])

    def test_invalid_newer_candidate_does_not_reach_install(self):
        result, calls = self.run_candidate("1.0.3", validate_error=RuntimeError("invalid manifest"))
        self.assertEqual(result, 1)
        self.assertEqual(calls, [])


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
            cache = root / "codex-cache"

            def add_local(command, **kwargs):
                shutil.rmtree(cache, ignore_errors=True)
                shutil.copytree(target, cache)
                return CompletedProcess(command, 0, "", "")

            with (
                patch.object(update_plugin, "run", side_effect=add_local) as run_mock,
                patch.object(update_plugin, "codex_cache_payload", return_value=cache),
                patch.object(
                    update_plugin,
                    "load_installed",
                    return_value=[
                        {
                            "name": "sports-betting-expert",
                            "marketplaceName": "sports-betting-expert",
                            "version": "1.0.3",
                            "source": {"source": "local", "path": str(target)},
                        }
                    ],
                ),
            ):
                update_plugin.refresh_local_archive(
                    "codex", installed, candidate, "1.0.3", REPOSITORY, "1.0.2"
                )

            self.assertTrue((target / "agents" / "new.md").is_file())
            self.assertTrue((target / "commands" / "added.md").is_file())
            self.assertFalse((target / "commands" / "removed.md").exists())
            self.assertFalse((target / "local-note.txt").exists())
            self.assertFalse((target / ".git").exists())
            self.assertEqual(update_plugin.payload_digest(cache), update_plugin.payload_digest(candidate))
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
                        "codex", installed, candidate, "1.0.3", REPOSITORY, "1.0.2"
                    )

            self.assertEqual(marker.read_text(encoding="utf-8"), "leave intact")
            run_mock.assert_not_called()

    def test_local_archive_rolls_back_source_and_cached_version_after_post_install_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "installed"
            candidate = root / "candidate"
            write_plugin(target, version="1.0.2")
            (target / "old-component.txt").write_text("old", encoding="utf-8")
            write_plugin(candidate, version="1.0.3")
            installed = {
                "marketplaceName": "sports-betting-expert",
                "source": {"source": "local", "path": str(target)},
            }
            cached_states = [
                [{"name": "sports-betting-expert", "marketplaceName": "sports-betting-expert", "version": "1.0.2", "source": {"source": "local", "path": str(target)}}],
                [{"name": "sports-betting-expert", "marketplaceName": "sports-betting-expert", "version": "1.0.2", "source": {"source": "local", "path": str(target)}}],
            ]
            cache = root / "codex-cache"
            shutil.copytree(target, cache)
            add_count = 0

            def failed_add_then_restore(command, **kwargs):
                nonlocal add_count
                add_count += 1
                if add_count == 2:
                    shutil.rmtree(cache)
                    shutil.copytree(target, cache)
                return CompletedProcess(command, 0, "", "")

            with (
                patch.object(update_plugin, "run", side_effect=failed_add_then_restore) as run_mock,
                patch.object(update_plugin, "codex_cache_payload", return_value=cache),
                patch.object(update_plugin, "load_installed", side_effect=cached_states),
            ):
                with self.assertRaisesRegex(RuntimeError, "did not refresh.*1.0.3"):
                    update_plugin.refresh_local_archive(
                        "codex", installed, candidate, "1.0.3", REPOSITORY, "1.0.2"
                    )

            self.assertEqual((target / "old-component.txt").read_text(encoding="utf-8"), "old")
            self.assertEqual(update_plugin.payload_digest(cache), update_plugin.payload_digest(target))
            self.assertFalse((target / "skills" / "sports-betting-expert" / "new-only.txt").exists())
            self.assertEqual(run_mock.call_count, 2)
            self.assertTrue(all(call.args[0][1:3] == ["plugin", "add"] for call in run_mock.call_args_list))

    def test_candidate_validation_rejects_malformed_yaml_before_running_suite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plugin(root)
            skill = root / "skills" / "sports-betting-expert" / "SKILL.md"
            skill.write_text("---\nname: [\ndescription: broken\n---\n", encoding="utf-8")
            with patch.object(update_plugin, "run") as run_mock:
                with self.assertRaisesRegex(RuntimeError, "invalid YAML"):
                    update_plugin.validate_candidate(root)
            run_mock.assert_not_called()

    def test_candidate_validation_accepts_required_yaml_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plugin(root)
            with patch.object(update_plugin, "run") as run_mock:
                update_plugin.validate_candidate(root)
            self.assertEqual(run_mock.call_count, 3)
            self.assertEqual(run_mock.call_args_list[1].args[0][1], "scripts/build_release.py")

    def test_fresh_clone_candidate_validation_builds_missing_dist(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "fresh-clone"
            shutil.copytree(
                Path(__file__).parents[1],
                candidate,
                ignore=shutil.ignore_patterns(".git", "dist", ".venv", "__pycache__", "*.pyc"),
            )
            shutil.rmtree(candidate / "tests")
            (candidate / "tests").mkdir()
            (candidate / "tests/test_candidate_smoke.py").write_text(
                "import unittest\nclass Smoke(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
                encoding="utf-8",
            )
            self.assertFalse((candidate / "dist").exists())
            update_plugin.validate_candidate(candidate)
            self.assertTrue((candidate / "dist/SHA256SUMS").is_file())

    def test_candidate_validation_fails_for_malformed_compatibility_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plugin(root)
            (root / ".codex-plugin/plugin.json").write_text("{broken", encoding="utf-8")
            with patch.object(update_plugin, "run") as run_mock:
                with self.assertRaisesRegex(RuntimeError, "compatibility manifest is unreadable"):
                    update_plugin.read_candidate_version(root, REPOSITORY)
            run_mock.assert_not_called()

    def test_git_marketplace_validates_the_refreshed_pinned_snapshot_before_add(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            write_plugin(snapshot)
            original_catalog = (snapshot / ".agents/plugins/marketplace.json").read_bytes()
            cache = root / "old-cache"
            write_plugin(cache, version="1.0.2")
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
            main_moved = False

            def fake_run(command, *, cwd=None, capture=False):
                nonlocal main_moved
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
                    main_moved = True  # `main` advances after the validated snapshot is selected.
                    catalog = json.loads((snapshot / ".agents/plugins/marketplace.json").read_text())
                    self.assertEqual(catalog["plugins"][0]["source"]["sha"], revision)
                    self.assertNotIn("ref", catalog["plugins"][0]["source"])
                    shutil.rmtree(cache)
                    shutil.copytree(snapshot, cache)
                    (cache / ".agents/plugins/marketplace.json").write_bytes(original_catalog)
                    return CompletedProcess(command, 0, stdout="", stderr="")
                self.fail(f"unexpected command: {command}")

            def validate(root_to_validate):
                self.assertEqual(root_to_validate, snapshot.resolve())
                events.append("validate")

            installed_list = [{
                "name": "sports-betting-expert", "marketplaceName": "sports-betting-expert",
                "version": "1.0.3", "source": {"source": "git", "url": REPOSITORY, "ref": "main"},
            }]

            with (
                patch.object(update_plugin, "run", side_effect=fake_run),
                patch.object(update_plugin, "validate_candidate", side_effect=validate),
                patch.object(update_plugin, "tracked_tree_digest", return_value="validated-tree"),
                patch.object(update_plugin, "load_installed", return_value=installed_list),
                patch.object(update_plugin, "codex_cache_payload", return_value=cache),
            ):
                update_plugin.refresh_git_marketplace(
                    "codex", "sports-betting-expert", "1.0.3", revision, REPOSITORY, "1.0.2"
                )

            restored_catalog = json.loads((snapshot / ".agents/plugins/marketplace.json").read_text())
            self.assertEqual(restored_catalog["plugins"][0]["source"]["ref"], "main")
            self.assertNotIn("sha", restored_catalog["plugins"][0]["source"])
            self.assertTrue(main_moved)
            self.assertEqual(update_plugin.payload_digest(cache), update_plugin.payload_digest(snapshot))

            self.assertEqual(
                events,
                [
                    "list",
                    "remote",
                    "revision",
                    "status",
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
                    "list",
                    "remote",
                    "revision",
                    "status",
                ],
            )

    def test_git_marketplace_does_not_install_if_main_moves_after_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            write_plugin(snapshot)
            cache = root / "old-cache"
            write_plugin(cache, version="1.0.2")
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

            with (
                patch.object(update_plugin, "run", side_effect=fake_run),
                patch.object(update_plugin, "codex_cache_payload", return_value=cache),
            ):
                with self.assertRaisesRegex(RuntimeError, "moved after candidate validation"):
                    update_plugin.refresh_git_marketplace(
                        "codex", "sports-betting-expert", "1.0.3", "a" * 40, REPOSITORY, "1.0.2"
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
