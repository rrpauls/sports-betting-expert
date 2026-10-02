import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).parents[1]
VERSION = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]


class ReleaseTests(unittest.TestCase):
    def test_generated_adapters_derive_from_canonical_files(self):
        subprocess.run([sys.executable, "scripts/build_release.py"], cwd=ROOT, check=True)
        skill = (ROOT / "skills/sports-betting-expert/SKILL.md").read_text()
        grok = (ROOT / f"dist/sports-betting-expert-grok-web-v{VERSION}.md").read_text()
        self.assertIn(skill, grok)
        with ZipFile(ROOT / f"dist/sports-betting-expert-gemini-v{VERSION}.zip") as archive:
            self.assertEqual(archive.read("gemini-knowledge/canonical-skill.md").decode(), skill)

    def test_generated_release_versions_match_both_plugin_manifests(self):
        compatibility = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(compatibility["version"], VERSION)
        subprocess.run([sys.executable, "scripts/build_release.py"], cwd=ROOT, check=True)
        self.assertTrue((ROOT / f"dist/sports-betting-expert-codex-v{VERSION}.zip").is_file())
        self.assertIn(f"sports-betting-expert-skill-v{VERSION}.zip", (ROOT / "dist/SHA256SUMS").read_text())

    def test_codex_release_contains_updater_runtime_modules(self):
        subprocess.run([sys.executable, "scripts/build_release.py"], cwd=ROOT, check=True)
        with ZipFile(ROOT / f"dist/sports-betting-expert-codex-v{VERSION}.zip") as archive:
            names = set(archive.namelist())
        prefix = "sports-betting-expert-codex/plugins/sports-betting-expert/"
        self.assertIn(prefix + "scripts/release_version.py", names)
        self.assertIn(prefix + "scripts/update_plugin.py", names)

    def test_marketplace_catalog_is_importable_codex_format(self):
        market = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(market["name"], "sports-betting-expert")
        self.assertEqual(len(market["plugins"]), 1)
        source = market["plugins"][0]["source"]
        self.assertEqual(source["source"], "url")
        self.assertEqual(source["url"], "https://github.com/rrpauls/sports-betting-expert.git")
        self.assertEqual(source["ref"], "main")

    def test_build_is_byte_reproducible(self):
        subprocess.run([sys.executable, "scripts/build_release.py"], cwd=ROOT, check=True)
        first = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir() if path.is_file()
        }
        subprocess.run([sys.executable, "scripts/build_release.py"], cwd=ROOT, check=True)
        second = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir() if path.is_file()
        }
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
