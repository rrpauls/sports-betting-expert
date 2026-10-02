"""Prepare API environment payloads offline; this script never sends a request."""
from __future__ import annotations
import argparse
import base64
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from scripts.release_version import VERSION
from scripts.distribution import NAME


def payload(kind: str, capability_directory: str | None = None) -> dict:
    if kind == 'self-hosted':
        if not capability_directory or not Path(capability_directory).is_absolute():
            raise ValueError('provide an absolute capability directory containing the skill folder')
        return {'environment': {'type': 'self_hosted', 'workspace_directory': '/workspace',
                                'capability_directories': [capability_directory]}}
    manifest = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
    package = 'openai-plugin' if kind == 'plugin' else 'skill'
    data = (ROOT / 'dist' / f'{NAME}-{package}-v{VERSION}.zip').read_bytes()
    inline = {'type': 'inline', 'name': NAME, 'description': manifest['description'],
              'source': {'type': 'base64', 'media_type': 'application/zip',
                         'data': base64.b64encode(data).decode('ascii')}}
    if kind == 'plugin':
        return {'environment': {'type': 'openai_hosted', 'plugins': [inline]}}
    return {'skills': [inline]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('plugin', 'skill', 'self-hosted'))
    parser.add_argument('--capability-directory')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(payload(args.kind, args.capability_directory), indent=2) + '\n', encoding='utf-8')
