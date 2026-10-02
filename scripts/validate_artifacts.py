#!/usr/bin/env python3
"""Validate manifests, archive safety, canonical provenance and complete checksums."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from scripts.distribution import NAME, SKILL, GEMINI_TYPES, package_contents, sync_manifests
from scripts.release_version import VERSION
from scripts.manifest_schema import validate as validate_schema
from scripts.check_version_bump import version_key
DIST = ROOT / 'dist'
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:sk-proj-|ghp_)[A-Za-z0-9_-]{30,}')


def validate_skill(data: bytes) -> None:
    text = data.decode('utf-8')
    match = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n', text, re.DOTALL)
    if not match:
        raise ValueError('SKILL.md must have YAML frontmatter')
    metadata = yaml.safe_load(match[1])
    if not isinstance(metadata, dict) or metadata.get('name') != NAME:
        raise ValueError('skill name must match its directory and canonical identity')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', metadata['name']) or len(metadata['name']) > 64:
        raise ValueError('invalid skill name')
    description = metadata.get('description')
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise ValueError('invalid skill description')


def validate_manifests() -> None:
    sync_manifests(check=True)
    root = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
    schema = json.loads((ROOT / 'schemas/agent-plugin-1.0.0.json').read_text(encoding='utf-8'))
    validate_schema(root, schema)
    version_key(root['version'])
    compatibility = json.loads((ROOT / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
    identity = ('name', 'version', 'description', 'author', 'repository')
    for manifest in (compatibility, claude):
        for key in identity:
            if manifest.get(key) != root[key]:
                raise ValueError(f'manifest identity differs: {key}')
    allowed = set(schema['properties']) - {'$schema', 'extensions'}
    if set(claude) - allowed:
        raise ValueError('unknown Claude plugin fields')
    if set(compatibility) - (allowed | {'skills', 'interface'}):
        raise ValueError('unknown Codex compatibility fields')
    if compatibility.get('skills') != './skills/':
        raise ValueError('invalid Codex skills layout')
    interface = root['extensions']['com.openai']['interface']
    if len(interface['shortDescription']) > 30:
        raise ValueError('OpenAI listing shortDescription exceeds 30 characters')
    # Long descriptions differ intentionally; presentation/asset references must agree.
    for key in ('displayName', 'shortDescription', 'composerIcon', 'logo', 'logoDark', 'defaultPrompt'):
        if compatibility['interface'].get(key) != interface.get(key):
            raise ValueError(f'Codex presentation mismatch: {key}')
    for key in ('composerIcon', 'logo', 'logoDark'):
        value = interface[key]
        if not value.startswith('./') or '..' in PurePosixPath(value).parts or not (ROOT / value).is_file():
            raise ValueError(f'invalid icon reference: {value}')
    market = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
    if market.get('name') != NAME or len(market.get('plugins', [])) != 1:
        raise ValueError('OpenAI marketplace identity/entries invalid')
    item = market['plugins'][0]
    if item.get('name') != NAME or item.get('source') != {
        'source': 'url', 'url': root['repository'] + '.git', 'ref': 'main'
    }:
        raise ValueError('OpenAI marketplace must track the canonical repository main branch')
    if item.get('policy') != {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}:
        raise ValueError('invalid local marketplace policy')
    validate_skill((SKILL / 'SKILL.md').read_bytes())


def validate_zip(path: Path, expected_prefix: str = '') -> None:
    with ZipFile(path) as archive:
        names = archive.namelist()
        if not names or len(names) != len(set(names)):
            raise ValueError('empty archive or duplicate members')
        folded = set()
        for info in archive.infolist():
            name = info.filename
            pure = PurePosixPath(name)
            if (pure.is_absolute() or '..' in pure.parts or '\\' in name or ':' in name
                    or any(ord(char) < 32 for char in name) or str(pure) != name):
                raise ValueError(f'unsafe archive path: {name}')
            if name.casefold() in folded:
                raise ValueError(f'case-colliding archive member: {name}')
            folded.add(name.casefold())
            if expected_prefix and not name.startswith(expected_prefix):
                raise ValueError(f'unexpected archive root: {name}')
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError(f'non-regular archive member: {name}')
            if any(part in {'.DS_Store', '__pycache__', '.git', '.venv', '.env', 'node_modules', 'tests'} for part in pure.parts) or pure.suffix in {'.pyc', '.pyo', '.pem', '.key'}:
                raise ValueError(f'development/secret file included: {name}')
            if info.compress_type not in (ZIP_STORED, ZIP_DEFLATED) or info.flag_bits & 1:
                raise ValueError('unsupported/encrypted ZIP member')
            if info.file_size > 25_000_000:
                raise ValueError('member exceeds 25 MB')
            if SECRET.search(archive.read(name)):
                raise ValueError(f'credential material included: {name}')
        if archive.testzip() is not None:
            raise ValueError('corrupted ZIP')


def validate_gemini(contents: dict[str, bytes]) -> None:
    if 'SKILL.md' not in contents:
        raise ValueError('Gemini requires root SKILL.md')
    validate_skill(contents['SKILL.md'])
    if sum(map(len, contents.values())) > 100_000_000:
        raise ValueError('Gemini skill exceeds 100 MB')
    for name, data in contents.items():
        if Path(name).suffix not in GEMINI_TYPES:
            raise ValueError(f'unsupported Gemini file type: {name}')
        data.decode('utf-8')
        if name.endswith('.py'):
            # Fail closed for future scripts: current calculation and snapshot parsing are offline.
            tree = ast.parse(data.decode())
            for node in ast.walk(tree):
                modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                           else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
                if any(module.split('.')[0] in {'socket', 'urllib', 'requests', 'http', 'httpx', 'subprocess'} for module in modules):
                    raise ValueError(f'Gemini script may perform external actions: {name}')


def main() -> None:
    validate_manifests()
    packages = package_contents(VERSION)
    grok_name = f'{NAME}-grok-web-v{VERSION}.md'
    expected_names = set(packages) | {grok_name}
    actual_names = {path.name for path in DIST.iterdir()}
    if actual_names != expected_names | {'SHA256SUMS'}:
        raise ValueError('dist has missing, extra or stale-version artifacts')
    for name, contents in packages.items():
        path = DIST / name
        if '-skill-v' in name and (path.stat().st_size > 50_000_000 or len(contents) > 500):
            raise ValueError('OpenAI Skill API upload limit exceeded')
        validate_zip(path)
        with ZipFile(path) as archive:
            if set(archive.namelist()) != set(contents):
                raise ValueError(f'archive inventory differs from source: {name}')
            for member, data in contents.items():
                if archive.read(member) != data:
                    raise ValueError(f'archive differs from canonical source: {name}/{member}')
        if 'gemini-skill-' in name:
            validate_gemini(contents)
    grok = (DIST / grok_name).read_text(encoding='utf-8')
    if not grok.startswith('# Sports Betting Expert — Grok Web Project Adapter (legacy fallback)'):
        raise ValueError('invalid legacy Grok adapter')
    for relative in ('SKILL.md', 'references/sources-and-methods.md', 'references/markets-and-coupons.md', 'references/profiles/priority-live-tennis.md'):
        if (SKILL / relative).read_text(encoding='utf-8') not in grok:
            raise ValueError('legacy Grok adapter differs from canonical source')
    checksums = {}
    for line in (DIST / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([^/\\]+)', line)
        if not match or match[2] in checksums:
            raise ValueError('invalid or duplicate checksum line')
        checksums[match[2]] = match[1]
    if set(checksums) != expected_names:
        raise ValueError('checksum inventory differs from release inventory')
    for name in expected_names:
        if hashlib.sha256((DIST / name).read_bytes()).hexdigest() != checksums[name]:
            raise ValueError(f'checksum mismatch: {name}')
    print(f'Artifact validation passed: {len(expected_names)} packages, version {VERSION}')


if __name__ == '__main__':
    main()
