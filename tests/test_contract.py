import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills/sports-betting-expert"


class CanonicalContractTests(unittest.TestCase):
    def test_plugin_identity_and_version_are_consistent(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        portable = json.loads((ROOT / "plugin.json").read_text())
        marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(codex["name"], "sports-betting-expert")
        self.assertEqual(portable["name"], codex["name"])
        self.assertEqual(codex["version"], portable["version"])
        self.assertEqual(marketplace["plugins"][0]["name"], codex["name"])
        self.assertEqual(marketplace["plugins"][0]["source"]["ref"], "main")

    def test_markdown_links_resolve_inside_skill(self):
        markdown_files = [SKILL / "SKILL.md", *SKILL.joinpath("references").rglob("*.md")]
        for source in markdown_files:
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", source.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((source.parent / target).resolve().is_file(), f"{source}: {target}")

    def test_tennis_gate_is_universal_and_profile_only_changes_priority(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        profile = (SKILL / "references/profiles/priority-live-tennis.md").read_text()
        self.assertIn("Never recommend a new pre-match tennis bet", entrypoint)
        self.assertIn("Tennis betting selections are live-only", entrypoint)
        self.assertIn("The profile changes the screening order", entrypoint)
        self.assertIn("live-only tennis gate applies whether or not this profile is active", profile)

    def test_statshawk_adapter_is_documented_and_packaged(self):
        adapter = SKILL / "scripts/statshawk_evidence.py"
        methods = (SKILL / "references/sources-and-methods.md").read_text()
        self.assertTrue(adapter.is_file())
        self.assertIn("StatsHawk MCP snapshots", methods)
        self.assertIn("statshawk_evidence.py", methods)


if __name__ == "__main__":
    unittest.main()
