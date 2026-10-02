"""Real CLI integration in temporary profiles; never alters the user's installation."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts import update_plugin, build_release
from scripts.install_updater import CHATGPT_CODEX
from scripts.release_version import VERSION

CODEX = shutil.which('codex') or (str(CHATGPT_CODEX) if CHATGPT_CODEX.is_file() else None)
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(CODEX, 'native Codex CLI not available on this test host')
class NativeCodexTests(unittest.TestCase):
    def test_fresh_install_upgrade_and_verified_rollback(self):
        build_release.main()
        with tempfile.TemporaryDirectory(prefix='sbe-codex-test-') as directory:
            root = Path(directory)
            with ZipFile(ROOT / f'dist/sports-betting-expert-codex-v{VERSION}.zip') as archive:
                archive.extractall(root / 'old')
                archive.extractall(root / 'new')
            marketplace = root / 'old/sports-betting-expert-codex'
            source = marketplace / 'plugins/sports-betting-expert'
            candidate = root / 'new/sports-betting-expert-codex/plugins/sports-betting-expert'
            for relative in ('plugin.json', '.codex-plugin/plugin.json'):
                path = source / relative
                manifest = json.loads(path.read_text(encoding='utf-8'))
                manifest['version'] = '1.0.3'
                path.write_text(json.dumps(manifest), encoding='utf-8')
            expected_old_digest = update_plugin.payload_digest(source)
            profile = root / 'profile'
            profile.mkdir()
            with patch.dict(os.environ, {'CODEX_HOME': str(profile)}):
                for args in (['marketplace', 'add', str(marketplace), '--json'],
                             ['add', 'sports-betting-expert@sports-betting-expert', '--json']):
                    result = subprocess.run([CODEX, 'plugin', *args], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                installed = update_plugin.load_installed(CODEX)[0]
                self.assertEqual(installed['version'], '1.0.3')
                real_verify = update_plugin.verify_listed_payload
                calls = 0
                def reject_first(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        raise RuntimeError('injected post-install verification failure')
                    return real_verify(*args, **kwargs)
                with patch.object(update_plugin, 'verify_listed_payload', side_effect=reject_first):
                    with self.assertRaisesRegex(RuntimeError, 'injected post-install'):
                        update_plugin.refresh_local_archive(CODEX, installed, candidate, VERSION,
                                                            update_plugin.REPOSITORY_URL, '1.0.3')
                self.assertEqual(update_plugin.load_installed(CODEX)[0]['version'], '1.0.3')
                self.assertEqual(update_plugin.payload_digest(source), expected_old_digest)
                self.assertEqual(calls, 2)  # Both failed candidate and restored cache were checked.
                update_plugin.refresh_local_archive(CODEX, installed, candidate, VERSION,
                                                    update_plugin.REPOSITORY_URL, '1.0.3')
                self.assertEqual(update_plugin.load_installed(CODEX)[0]['version'], VERSION)
                self.assertEqual(update_plugin.payload_digest(source), update_plugin.payload_digest(candidate))
