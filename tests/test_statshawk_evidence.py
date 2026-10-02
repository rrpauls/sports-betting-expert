import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "skills/sports-betting-expert/scripts/statshawk_evidence.py"
SPEC = importlib.util.spec_from_file_location("statshawk_evidence", SCRIPT)
statshawk_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(statshawk_evidence)


class StatsHawkEvidenceTests(unittest.TestCase):
    def test_projects_supported_fields_and_timestamp(self):
        result = statshawk_evidence.snapshot(
            "get_stat_capabilities",
            "MLB",
            "2026-09-26T12:00:00+03:00",
            {"person_id": "per_1", "capabilities": [{"stat_id": "batting.hr"}], "ignored": "drop"},
        )
        self.assertEqual("2026-09-26T09:00:00+00:00", result["observed_at"])
        self.assertEqual("mlb", result["league"])
        self.assertNotIn("ignored", json.dumps(result))
        self.assertIn("batting.hr", json.dumps(result))

    def test_rejects_sensitive_fields(self):
        with self.assertRaisesRegex(ValueError, "sensitive field"):
            statshawk_evidence.snapshot(
                "search_games", "nba", "2026-09-26T09:00:00Z", {"session_token": "secret"}
            )

    def test_cli_writes_private_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            import sys
            source = Path(directory) / "source.json"
            output = Path(directory) / "snapshot.json"
            source.write_text(json.dumps({"results": [{"game_id": "g1", "status": "scheduled"}]}))
            output.write_text("old\n", encoding="utf-8")
            if sys.platform != 'win32':
                output.chmod(0o644)
            code = statshawk_evidence.main([
                "--tool", "search_games", "--league", "nba",
                "--observed-at", "2026-09-26T09:00:00Z",
                "--input", str(source), "--output", str(output),
            ])
            self.assertEqual(0, code)
            if sys.platform != 'win32':
                self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))


if __name__ == "__main__":
    unittest.main()
