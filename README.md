# Sports Betting Expert

Canonical multi-host skill for evidence-led sports betting analysis. The maintained behavior lives in [`skills/sports-betting-expert`](skills/sports-betting-expert); release packages and host adapters are generated from it. Tennis selections remain live-only, and the optional `priority-live-tennis` profile remains off by default.

## Distribution and update support

Automatic invocation and automatic content updates are separate host features:

| Host / installation type | Automatic invocation | Automatic content update | Update source | Update mechanism | Limitations / required permissions |
|---|---|---|---|---|---|
| Codex or ChatGPT Desktop, Git marketplace | When relevant, after the plugin is enabled | Automatic after updater setup on macOS | GitHub `main`; each release must have a newer SemVer | Dedicated updater venv plus a daily LaunchAgent validates a clean clone, builds and validates artifacts, then installs from the exact marketplace commit | Run `python3 scripts/install_updater.py`; signed-in user session and Codex CLI required. Direct Git installs without a verifiable marketplace snapshot remain unchanged. Linux and Windows schedulers are not implemented. Restart desktop after an update. |
| Codex or ChatGPT Desktop, portable Codex ZIP | When relevant, after the plugin is enabled | Automatic after updater setup on macOS | GitHub `main`; each release must have a newer SemVer | Updater replaces the local plugin source atomically and refreshes Codex's cache | Same setup and platform requirements as above. |
| ChatGPT Web, manual Skill ZIP | When relevant, after upload and enablement | No | New release ZIP built from GitHub `main` | Replace/re-upload the skill ZIP | Upload permissions and feature availability depend on the account/workspace. A ZIP upload does not track GitHub. |
| ChatGPT Web, GitHub-managed workspace marketplace | When relevant, after workspace installation/enablement | Yes, daily sync by OpenAI | GitHub marketplace repository, normally its default branch (`main`) | Workspace admin imports `.agents/plugins/marketplace.json`; OpenAI synchronizes daily, with an admin “Sync now” option | Eligible managed workspace and admin GitHub access required. Workspace policy controls installation; sync does not grant access to included apps. Do not install the local LaunchAgent for this hosted path. |
| Claude Web, uploaded Skill ZIP | When relevant, after upload and enablement | No | New release ZIP built from GitHub `main` | Replace/re-upload the skill ZIP | Uploaded skills are copies. Anthropic's GitHub project integration syncs repository context, not this skill package; no GitHub-synced organization marketplace is claimed here. |
| Gemini Web, native Skill import | When relevant, after import and enablement | No | Current canonical `SKILL.md` or a release ZIP | Re-import/replace the skill after a release | GitHub is not a live skill source. Availability and skill controls depend on account rollout. |
| Grok Web, Project Markdown adapter | Within that Project's conversations | No | Generated adapter from GitHub `main` | Replace the Project Markdown file after a release | Project-scoped static content, not an account-wide skill or source-sync integration. |

GitHub `main` is the canonical development and update source. Every distributed content or updater change must bump the semantic version in root [`plugin.json`](plugin.json); same-version edits are intentionally not installed by the updater. CI rejects distributed changes without a newer version and version regressions.

The ChatGPT workspace marketplace manifest is at [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). OpenAI documents GitHub marketplace import and daily synchronization for eligible workspace admins in [Importing and syncing plugin marketplaces from GitHub](https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github). OpenAI currently accepts Codex marketplace manifests under `.agents/plugins/marketplace.json`; we do not claim an Anthropic GitHub-synced marketplace for Claude Web.

## Local Codex / ChatGPT Desktop updater

Installing the plugin does not install its scheduler. From a repository checkout, run this once on macOS:

```bash
python3 scripts/install_updater.py
```

This creates a dedicated updater virtual environment, installs its dependency, writes and loads the user LaunchAgent, and confirms launchd registration. It is safe to repeat. Check it with `python3 scripts/install_updater.py status` and remove it with `python3 scripts/install_updater.py uninstall`. See [INSTALL.md](INSTALL.md) for ZIP installation and details.

## Verified release status

Release `v1.0.2` was the latest published release before this repair. Its historical verification was: canonical tests 10/10, artifact validation and checksums passed, Codex and portable packages validated, ChatGPT Web and Claude Web smoke prompts passed, and Gemini/Grok status was user-verified. That evidence applies to `v1.0.2`, not this unreleased `v1.0.3` repair.

Gemini Apps now support native reusable skills based on `SKILL.md`; the older `v1.0.2` Gem bundle remains a legacy artifact. See [INSTALL-GEMINI.md](INSTALL-GEMINI.md) and Google's [Create & manage skills](https://support.google.com/gemini/answer/17094296?hl=en). Availability can vary by account and rollout.

## Build and validate

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-updater.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_release.py
.venv/bin/python scripts/validate_artifacts.py
```

The builder clears stale generated files before producing the current manifest version under `dist/`. CI runs the same tests → build → artifact validation sequence used for updater candidates.

## Boundaries

The calculator performs conditional arithmetic; it does not retrieve odds or predict results. The skill never places bets or operates an account. Current claims and prices require current sources or a clearly labeled user-provided snapshot.

## License

MIT
