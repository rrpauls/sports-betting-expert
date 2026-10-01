import unittest

from scripts.update_plugin import is_newer, parse_version


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


if __name__ == "__main__":
    unittest.main()
