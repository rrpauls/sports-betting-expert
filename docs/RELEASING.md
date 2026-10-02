# Release procedure

Root `plugin.json` is authoritative. Distributed file changes require a newer SemVer; CI compares against the PR base or push predecessor and prevents regression/same-version mutation. Update the Codex overlay version/presentation with root metadata, then run `scripts/sync_manifests.py` to regenerate Claude metadata. Never edit a host's skill copy.

The `release.yml` workflow is triggered by a `vX.Y.Z` tag pushed after review/approval. It checks tag/version equality, generated manifest consistency, the full suite on Linux/macOS/Windows, actual OS scheduler registration/removal, archive validation and repeated byte-identical builds. A clean Ubuntu checkout builds release assets only after every validation job succeeds. Upload fails on unexpected/stale files, missing checksums or invalid packages. Notes come from `docs/RELEASE-NOTES-vX.Y.Z.md`; a missing/empty notes file fails publication. CI's version guard runs before the release upload. No vendor submission is performed.

Current outputs:

```text
sports-betting-expert-openai-plugin-v1.1.0.zip
sports-betting-expert-skill-v1.1.0.zip
sports-betting-expert-codex-v1.1.0.zip
sports-betting-expert-claude-plugin-v1.1.0.zip
sports-betting-expert-claude-marketplace-v1.1.0.zip
sports-betting-expert-gemini-skill-v1.1.0.zip
sports-betting-expert-gemini-legacy-gem-v1.1.0.zip
sports-betting-expert-grok-web-v1.1.0.md
SHA256SUMS
```

The standalone Skill is reused by Claude, Codex/Grok filesystem discovery and OpenAI Skills API; Grok Build reuses Claude plugin/catalog. Gemini's native archive has root SKILL.md as required by Enterprise, hence its separate package. The organization archive is a complete private-mirror export. Legacy Gemini and Grok outputs are explicitly labelled fallbacks.

For local release verification on a clean committed checkout:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_release.py --tag v1.1.0
```

The helper checks manifest identity, exact inventory/checksums and deterministic rebuilding, and rejects tracked-file drift. `dist/` remains generated/ignored. Release publication requires a separately authorized tag push; a local branch commit alone publishes nothing.
