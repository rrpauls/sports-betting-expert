"""Gate a release tag and detect non-reproducible generated outputs."""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from scripts.release_version import VERSION
from scripts.validate_artifacts import validate_manifests


def check_tag(tag: str) -> None:
    if tag != f'v{VERSION}':
        raise ValueError(f'tag {tag!r} must equal v{VERSION}')
    validate_manifests()


def snapshot() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'dist').iterdir() if p.is_file()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    check_tag(parser.parse_args().tag)
    for script in ('build_release.py', 'validate_artifacts.py'):
        subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], cwd=ROOT, check=True)
    first = snapshot()
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_release.py')], cwd=ROOT, check=True)
    if first != snapshot():
        raise ValueError('release build is not byte reproducible')
    subprocess.run(['git', 'diff', '--exit-code'], cwd=ROOT, check=True)
    print(f'Release gate passed: v{VERSION}')
