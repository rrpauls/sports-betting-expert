import base64
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts import distribution, validate_artifacts, check_release, api_payloads
from scripts.build_release import main as build, archive_info
from scripts.release_version import VERSION


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()

    def test_manifests_and_all_packages(self):
        validate_artifacts.main()
        for filename, contents in distribution.package_contents(VERSION).items():
            with self.subTest(package=filename), ZipFile(distribution.ROOT / 'dist' / filename) as archive:
                self.assertEqual({name: archive.read(name) for name in archive.namelist()}, contents)

    def test_both_plugins_and_org_export_use_identical_canonical_skill(self):
        skill = distribution.canonical_files()
        for host in ('claude', 'openai'):
            plugin = distribution.plugin_files(host)
            self.assertEqual({name.removeprefix(f'skills/{distribution.NAME}/'): data
                              for name, data in plugin.items() if name.startswith('skills/')}, skill)
        packages = distribution.package_contents(VERSION)
        org = packages[f'{distribution.NAME}-claude-marketplace-v{VERSION}.zip']
        market = json.loads(org['.claude-plugin/marketplace.json'])
        source = market['plugins'][0]['source'].removeprefix('./')
        self.assertIn(f'{source}/.claude-plugin/plugin.json', org)
        self.assertIn(f'{source}/skills/{distribution.NAME}/SKILL.md', org)
        self.assertEqual(market['plugins'][0]['version'], VERSION)

    def test_gemini_root_limits_and_offline_scripts(self):
        validate_artifacts.validate_gemini(distribution.canonical_files())
        for extra in ({'payload.docx': b'binary'}, {'scripts/network.py': b'import urllib.request\n'},
                      {'scripts/network.py': b'from subprocess import run\n'}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_artifacts.validate_gemini(distribution.canonical_files() | extra)
        with self.assertRaises(ValueError):
            validate_artifacts.validate_gemini({'nested/SKILL.md': b''})

    def test_skill_metadata_is_validated(self):
        for data in (b'no frontmatter', b'---\nname: other\ndescription: test\n---\n',
                     b'---\nname: sports-betting-expert\ndescription: 123\n---\n'):
            with self.assertRaises(ValueError):
                validate_artifacts.validate_skill(data)

    def test_archive_rejects_unsafe_members_and_secrets(self):
        import sys
        names = ['../escape', '/absolute', 'C:/escape', './alias',
                 '.DS_Store', 'a/__pycache__/x.pyc', '.env', 'tests/test.py']
        if sys.platform != 'win32':
            names.append('a\\escape')
            
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'test.zip'
                with ZipFile(path, 'w') as archive:
                    archive.writestr(archive_info(name), b'test')
                with self.assertRaises(ValueError):
                    validate_artifacts.validate_zip(path)
        for mode, data in ((0o120777, b'target'), (0o100644, b'-----BEGIN PRIVATE KEY-----')):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'test.zip'
                info = archive_info('file')
                info.external_attr = mode << 16
                with ZipFile(path, 'w') as archive:
                    archive.writestr(info, data)
                with self.assertRaises(ValueError):
                    validate_artifacts.validate_zip(path)

    def test_symlink_canonical_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.md'
            source.write_text('test')
            try:
                (root / 'link.md').symlink_to(source)
            except OSError:
                self.skipTest('OS account cannot create symlinks')
            with patch.object(distribution, 'SKILL', root), self.assertRaises(ValueError):
                distribution.canonical_files()

    def test_checksum_corruption_fails_then_build_restores(self):
        sums = distribution.ROOT / 'dist/SHA256SUMS'
        original = sums.read_bytes()
        try:
            sums.write_bytes(original.replace(original[:64], b'0' * 64, 1))
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                validate_artifacts.main()
        finally:
            sums.write_bytes(original)

    def test_release_tag_and_generated_manifest_drift(self):
        check_release.check_tag('v' + VERSION)
        with self.assertRaises(ValueError):
            check_release.check_tag('v0.0.0')
        with patch.object(distribution, 'claude_manifest', return_value=distribution.claude_manifest() | {'name': 'bad'}):
            with self.assertRaisesRegex(ValueError, 'stale generated manifest'):
                distribution.sync_manifests(check=True)

    def test_hosted_api_payload_decodes_to_valid_plugin_zip(self):
        payload = api_payloads.payload('plugin')['environment']
        self.assertEqual(payload['type'], 'openai_hosted')
        inline = payload['plugins'][0]
        self.assertEqual(inline['name'], distribution.NAME)
        with ZipFile(io.BytesIO(base64.b64decode(inline['source']['data']))) as archive:
            manifest = json.loads(archive.read(f'{distribution.NAME}/.codex-plugin/plugin.json'))
            self.assertEqual(manifest['description'], inline['description'])
            self.assertEqual(manifest['version'], VERSION)
        import os
        expected_path = os.path.abspath('/workspace/capabilities')
        config = api_payloads.payload('self-hosted', expected_path)
        self.assertEqual(config['environment']['capability_directories'], [expected_path])

    def test_native_grok_catalog_resolves_same_plugin_without_second_copy(self):
        native = distribution.grok_marketplace()
        self.assertEqual(native['plugins'][0]['source'], {'type': 'local', 'path': './'})
        self.assertEqual(native['plugins'][0]['version'], VERSION)
        org = distribution.package_contents(VERSION)[f'{distribution.NAME}-claude-marketplace-v{VERSION}.zip']
        catalog = json.loads(org['.grok-plugin/marketplace.json'])
        plugin_path = catalog['plugins'][0]['source']['path'].removeprefix('./')
        self.assertIn(plugin_path + '/.claude-plugin/plugin.json', org)

    def test_tampered_archive_is_rejected_even_with_recomputed_checksum(self):
        filename = f'{distribution.NAME}-gemini-skill-v{VERSION}.zip'
        path = distribution.ROOT / 'dist' / filename
        sums = distribution.ROOT / 'dist/SHA256SUMS'
        original, checksums = path.read_bytes(), sums.read_bytes()
        try:
            with ZipFile(io.BytesIO(original)) as archive:
                contents = {name: archive.read(name) for name in archive.namelist()}
            contents['SKILL.md'] += b'\nTampered instructions\n'
            with ZipFile(path, 'w') as archive:
                for name, data in contents.items():
                    archive.writestr(archive_info(name), data)
            old_digest = hashlib.sha256(original).hexdigest().encode()
            new_digest = hashlib.sha256(path.read_bytes()).hexdigest().encode()
            sums.write_bytes(checksums.replace(old_digest, new_digest))
            with self.assertRaisesRegex(ValueError, 'differs from canonical source'):
                validate_artifacts.main()
        finally:
            path.write_bytes(original)
            sums.write_bytes(checksums)

    def test_vendored_schema_constraints_fail_closed_without_extra_dependencies(self):
        from scripts.manifest_schema import validate
        schema = json.loads((distribution.ROOT / 'schemas/agent-plugin-1.0.0.json').read_text())
        valid = json.loads((distribution.ROOT / 'plugin.json').read_text())
        validate(valid, schema)
        for change in ({'skills': './skills/'}, {'name': 'UPPERCASE'}, {'author': {'name': 3}},
                       {'keywords': [3]}, {'extensions': {'com.openai': 'not-an-object'}},
                       {'$schema': 'wrong'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(valid | change, schema)
        with self.assertRaises(ValueError):
            validate({}, schema)
        with self.assertRaisesRegex(ValueError, 'unsupported schema constraints'):
            validate(valid, schema | {'oneOf': []})
