import hashlib
import subprocess
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).parents[1]


class ReleaseTests(unittest.TestCase):
    def test_generated_adapters_derive_from_canonical_files(self):
        subprocess.run(["python3", "scripts/build_release.py"], cwd=ROOT, check=True)
        skill = (ROOT / "skills/sports-betting-expert/SKILL.md").read_text()
        grok = (ROOT / "dist/sports-betting-expert-grok-web-v1.0.1.md").read_text()
        self.assertIn(skill, grok)
        with ZipFile(ROOT / "dist/sports-betting-expert-gemini-v1.0.1.zip") as archive:
            self.assertEqual(archive.read("gemini-knowledge/canonical-skill.md").decode(), skill)

    def test_build_is_byte_reproducible(self):
        subprocess.run(["python3", "scripts/build_release.py"], cwd=ROOT, check=True)
        first = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir() if path.is_file()
        }
        subprocess.run(["python3", "scripts/build_release.py"], cwd=ROOT, check=True)
        second = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir() if path.is_file()
        }
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
