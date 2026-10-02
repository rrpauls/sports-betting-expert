import plistlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install_updater
from scripts.install_updater import LABEL, TEMPLATE, create_launch_agent


class InstallUpdaterTests(unittest.TestCase):
    def test_launch_agent_uses_current_user_and_executable_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "user home"
            python = root / "python"
            updater = root / "plugin" / "scripts" / "update_plugin.py"
            codex = root / "ChatGPT Codex"
            for path in (python, updater, codex):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            result = create_launch_agent(
                home=home,
                python=python,
                updater=updater,
                codex=codex,
                path_value="/custom/bin:/usr/bin:/bin",
                template=TEMPLATE,
            )

            with result.open("rb") as stream:
                payload = plistlib.load(stream)
            arguments = payload["ProgramArguments"]
            self.assertEqual(arguments, [str(python.resolve()), str(updater.resolve()), "--codex", str(codex.resolve())])
            self.assertEqual(payload["EnvironmentVariables"]["HOME"], str(home.resolve()))
            self.assertEqual(payload["EnvironmentVariables"]["CODEX_HOME"], str((home / ".codex").resolve()))
            self.assertEqual(payload["EnvironmentVariables"]["PATH"], "/custom/bin:/usr/bin:/bin")
            self.assertEqual(payload["StandardOutPath"], str(home / "Library/Logs/sports-betting-expert-updater.log"))
            self.assertEqual(result, home / "Library/LaunchAgents" / f"{LABEL}.plist")
            self.assertNotIn("@", result.read_text(encoding="utf-8"))

    def test_scheduler_install_is_idempotent_and_checks_registration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            source = root / "repo"
            runtime_python = root / "runtime/bin/python"
            codex = root / "codex"
            for path in (runtime_python, codex):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            (source / "scripts").mkdir(parents=True)
            for name in ("update_plugin.py", "release_version.py"):
                (source / "scripts" / name).write_text("# test", encoding="utf-8")
            (source / "requirements-updater.txt").write_text("", encoding="utf-8")
            registered = False
            calls = []

            def runner(command, **kwargs):
                nonlocal registered
                calls.append(command[1])
                if command[1] == "bootstrap":
                    registered = True
                elif command[1] == "bootout":
                    registered = False
                if command[1] == "print":
                    return subprocess.CompletedProcess(command, 0 if registered else 1, "", "")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(install_updater, "_ensure_runtime", return_value=runtime_python):
                first = install_updater.install(
                    home=home, source_root=source, codex=codex, runner=runner
                )
                second = install_updater.install(
                    home=home, source_root=source, codex=codex, runner=runner
                )

            self.assertEqual(first, second)
            self.assertEqual(calls, ["bootout", "bootstrap", "print"] * 2)
            self.assertTrue(registered)
            self.assertTrue(first.is_file())

    def test_uninstall_removes_agent_and_dedicated_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            agent = home / "Library/LaunchAgents" / f"{LABEL}.plist"
            agent.parent.mkdir(parents=True)
            agent.touch()
            state = home / "Library/Application Support" / install_updater.STATE_NAME
            state.mkdir(parents=True)
            (state / "marker").touch()
            calls = []

            def runner(command, **kwargs):
                calls.append(command[1])
                return subprocess.CompletedProcess(command, 0, "", "")

            install_updater.uninstall(home=home, runner=runner)
            self.assertEqual(calls, ["bootout"])
            self.assertFalse(agent.exists())
            self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
