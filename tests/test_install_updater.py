import plistlib
import tempfile
import unittest
from pathlib import Path

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
            self.assertEqual(payload["EnvironmentVariables"]["PATH"], "/custom/bin:/usr/bin:/bin")
            self.assertEqual(payload["StandardOutPath"], str(home / "Library/Logs/sports-betting-expert-updater.log"))
            self.assertEqual(result, home / "Library/LaunchAgents" / f"{LABEL}.plist")
            self.assertNotIn("@", result.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
