"""Regenerate Claude metadata from root plugin.json without copying the skill."""
import argparse
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.distribution import sync_manifests

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    sync_manifests(parser.parse_args().check)
