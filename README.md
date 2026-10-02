# Sports Betting Expert

One canonical skill for evidence-led sports betting analysis: [`skills/sports-betting-expert/`](skills/sports-betting-expert/). All host packages derive from those files. The workflow requires current evidence, invents neither prices nor statistics, never places bets, and keeps new tennis selections **live-only**. The optional sport-priority profile stays off unless requested.

## Installation and updates

Use the [audited support matrix](docs/SUPPORT-MATRIX.md) to choose your installation source, then [INSTALL.md](INSTALL.md) for exact steps. Native invocation, installation, content updates and manual refresh are separate capabilities.

- OpenAI: portable plugin ZIP, standalone Skill ZIP, GitHub workspace marketplace, Codex Git/local marketplace, hosted/API and self-hosted capability directory.
- Claude: native plugin/marketplace, standalone Skill, personal/organization upload, private organization mirror, native Code updater and one-way account sync.
- Gemini: native Skill for Apps and Enterprise; Gemini CLI uses the same canonical folder. Gem packaging is an explicitly named legacy fallback.
- Grok: native Skills; Build reuses the Claude plugin and marketplace through [official compatibility](https://docs.x.ai/build/features/skills-plugins-marketplaces). Project Markdown remains a fallback.

Hosted GitHub marketplace synchronization follows the vendor's rules. Claude Code third-party auto-update must be enabled. Static uploads do not track GitHub. Local Codex installations can opt into this repository's daily validated updater on macOS, Linux with user systemd, or Windows Task Scheduler. No local scheduler is installed by uploading a hosted plugin.

## Build and review

Version **1.1.0** is prepared for release; nothing here asserts external publication or directory acceptance. Root `plugin.json` owns the version. Claude manifests are generated metadata, not independent source. Change distributed content only with a newer SemVer.

With the project virtual environment:

```bash
.venv/bin/python -m pip install -r requirements-updater.txt
.venv/bin/python scripts/sync_manifests.py --check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_release.py
.venv/bin/python scripts/validate_artifacts.py
```

On Windows use `.venv\Scripts\python.exe`. If no environment exists, create one with the installed Python 3.11+ interpreter (`python3 -m venv .venv` on Unix, `py -3 -m venv .venv` on Windows) before installing dependencies or running project code.

The builder emits seven ZIPs and one legacy Markdown file plus `SHA256SUMS`. Package layouts and contents are checked against canonical bytes; the public Agent Plugins schema is vendored under `schemas/`. [Release procedure](docs/RELEASING.md) describes clean builds and CI gates. [Distribution verification](docs/VERIFICATION.md) records the scope of local checks and remaining vendor/OS checks.

## License

MIT. This is conditional research and arithmetic, not an odds feed or guaranteed prediction service.
