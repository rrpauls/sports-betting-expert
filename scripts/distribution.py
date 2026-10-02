"""Single package inventory, generated exclusively from canonical source files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = 'sports-betting-expert'
SKILL = ROOT / 'skills' / NAME
BLOCKED = {'.DS_Store', '__pycache__', '.git', '.venv', 'node_modules', '.env'}
GEMINI_TYPES = {'.md', '.py', '.yaml', '.svg'}


def encode_json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()


def canonical_files() -> dict[str, bytes]:
    files = {}
    for path in sorted(SKILL.rglob('*')):
        relative = path.relative_to(SKILL)
        if any(part in BLOCKED for part in relative.parts) or path.suffix in {'.pyc', '.pyo'}:
            continue
        if path.is_symlink():
            raise ValueError(f'canonical source contains symlink: {relative}')
        if path.is_file():
            files[relative.as_posix()] = path.read_bytes()
    return files


def claude_manifest() -> dict:
    root = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
    return {key: root[key] for key in (
        'name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords'
    )}


def claude_marketplace(source: str = './') -> dict:
    plugin = claude_manifest()
    return {'name': NAME, 'description': 'Canonical Sports Betting Expert skill and plugin distribution.', 'owner': plugin['author'],
            'plugins': [{'name': NAME, 'source': source, 'version': plugin['version'],
                         'description': plugin['description']}]}



def grok_marketplace(source: str = './') -> dict:
    catalog = claude_marketplace(source)
    catalog['plugins'][0]['source'] = {'type': 'local', 'path': source}
    return catalog

def plugin_files(host: str) -> dict[str, bytes]:
    files = {'LICENSE': (ROOT / 'LICENSE').read_bytes()}
    files.update({f'skills/{NAME}/{name}': data for name, data in canonical_files().items()})
    if host == 'openai':
        for name in ('plugin.json', '.codex-plugin/plugin.json'):
            files[name] = (ROOT / name).read_bytes()
    elif host == 'claude':
        files['.claude-plugin/plugin.json'] = encode_json(claude_manifest())
    else:
        raise ValueError(f'unknown plugin host: {host}')
    return files


def prefixed(prefix: str, files: dict[str, bytes]) -> dict[str, bytes]:
    return {f'{prefix}/{name}': data for name, data in files.items()}


def package_contents(version: str) -> dict[str, dict[str, bytes]]:
    # Import here to avoid coupling release metadata to canonical source enumeration.
    from .build_release import local_marketplace, gemini_instructions, gemini_knowledge
    skill = canonical_files()
    codex_root = f'{NAME}-codex'
    codex = {f'{codex_root}/.agents/plugins/marketplace.json': local_marketplace(),
             f'{codex_root}/INSTALL.md': (ROOT / 'INSTALL.md').read_bytes()}
    local = plugin_files('openai')
    for name in ('README.md', 'INSTALL.md', 'MIGRATION.md', 'requirements-updater.txt',
                 'scripts/install_updater.py', 'scripts/update_plugin.py',
                 'scripts/release_version.py', 'scripts/schedulers.py',
                 'launchd/com.rrpauls.sports-betting-expert-updater.plist.in'):
        local[name] = (ROOT / name).read_bytes()
    codex.update(prefixed(f'{codex_root}/plugins/{NAME}', local))
    org = {'.claude-plugin/marketplace.json': encode_json(claude_marketplace(f'./plugins/{NAME}'))}
    org['.grok-plugin/marketplace.json'] = encode_json(grok_marketplace(f'./plugins/{NAME}'))
    org.update(prefixed(f'plugins/{NAME}', plugin_files('claude')))
    legacy = {'gemini-gem-instructions.md': gemini_instructions().encode(),
              'INSTALL-GEMINI.md': (ROOT / 'INSTALL-GEMINI.md').read_bytes()}
    legacy.update(prefixed('gemini-knowledge', gemini_knowledge()))
    return {
        f'{NAME}-openai-plugin-v{version}.zip': prefixed(NAME, plugin_files('openai')),
        f'{NAME}-skill-v{version}.zip': prefixed(NAME, skill),
        f'{NAME}-codex-v{version}.zip': codex,
        f'{NAME}-claude-plugin-v{version}.zip': prefixed(NAME, plugin_files('claude')),
        f'{NAME}-claude-marketplace-v{version}.zip': org,
        # Root SKILL.md is accepted by both Apps and Gemini Enterprise.
        f'{NAME}-gemini-skill-v{version}.zip': skill,
        f'{NAME}-gemini-legacy-gem-v{version}.zip': legacy,
    }


def sync_manifests(check: bool = False) -> None:
    for name, payload in (('.claude-plugin/plugin.json', claude_manifest()),
                          ('.claude-plugin/marketplace.json', claude_marketplace()),
                          ('.grok-plugin/marketplace.json', grok_marketplace())):
        path = ROOT / name
        data = encode_json(payload)
        if check:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError(f'stale generated manifest: {name}; run scripts/sync_manifests.py')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
