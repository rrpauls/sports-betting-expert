import json
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from scripts import check_version_bump
from scripts.check_version_bump import manifest_version, newer, version_key


class VersionGuardTests(unittest.TestCase):
    def test_semver_order_and_regression(self):
        self.assertTrue(newer("1.0.3", "1.0.2"))
        self.assertTrue(newer("1.0.0", "1.0.0-rc.2"))
        self.assertFalse(newer("1.0.2", "1.0.2"))
        self.assertFalse(newer("1.0.1", "1.0.2"))
        with self.assertRaises(ValueError):
            version_key("1.0.0-rc.01")
        with self.assertRaises(ValueError):
            manifest_version('{"version": "not-semver"}')

    def test_distributed_payload_requires_newer_version(self):
        base = json.dumps({"version": "1.0.2"})
        diff = "skills/sports-betting-expert/SKILL.md\n"
        with (
            patch.object(check_version_bump.subprocess, "run", side_effect=[
                CompletedProcess([], 0, base, ""), CompletedProcess([], 0, diff, "")
            ]),
            patch("builtins.open", return_value=__import__("io").StringIO('{"version":"1.0.2"}')),
        ):
            with self.assertRaisesRegex(ValueError, "without a newer semantic version"):
                check_version_bump.check("base")

    def test_version_regression_is_rejected_even_without_payload_diff(self):
        base = json.dumps({"version": "1.0.2"})
        with (
            patch.object(check_version_bump.subprocess, "run", return_value=CompletedProcess([], 0, base, "")),
            patch("builtins.open", return_value=__import__("io").StringIO('{"version":"1.0.1"}')),
        ):
            with self.assertRaisesRegex(ValueError, "version regression"):
                check_version_bump.check("base")


if __name__ == "__main__":
    unittest.main()
