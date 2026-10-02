# Install Sports Betting Expert

First select your route from the [authoritative support matrix](docs/SUPPORT-MATRIX.md). Every generated package below is version **1.1.0**. Get packages from an approved GitHub release or build them locally. Verify SHA256SUMS before extraction; static uploads require explicit replacement after later releases.

## OpenAI

For the public Directory, open Plugins, search for the published plugin and install it, then start a new chat. Publication/submission remains a publisher action; this repository does not assert a directory listing.

For an eligible ChatGPT workspace owner/admin: **Admin → Plugins → Add → Upload plugin**, choose `sports-betting-expert-openai-plugin-v1.1.0.zip`. Updates: plugin details → Upload new version. Standalone Skill upload: **Skills → Create → Upload from your computer**, choose `sports-betting-expert-skill-v1.1.0.zip`, review and enable. Availability depends on the account/workspace; see [official Skills help](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).

For GitHub workspace synchronization: **Workspace settings → Plugins → Add → Import marketplace**. Source `https://github.com/rrpauls/sports-betting-expert`, Path empty, Branch `main`. Authorize GitHub and configure workspace installation policy. New imports sync daily; **Marketplaces → Sync now** requests an immediate sync. A fixed commit cannot follow later changes. Public repositories are supported by [OpenAI workspace sync](https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github).

### Codex Git marketplace

```bash
codex plugin marketplace add rrpauls/sports-betting-expert --ref main
codex plugin add sports-betting-expert@sports-betting-expert
codex plugin list --json
```

### Codex portable/local marketplace

Extract `sports-betting-expert-codex-v1.1.0.zip` to a durable directory. Register the extracted marketplace directory, **not** its nested plugin:

```bash
codex plugin marketplace add /absolute/path/sports-betting-expert-codex
codex plugin add sports-betting-expert@sports-betting-expert
```

The same marketplace name cannot identify two catalog roots in one Codex profile. Use distinct CODEX_HOME profiles for separate catalogs. The updater checks all installed copies reported within its selected profile. Source/cache checks fail closed if a runtime cannot expose verifiable paths.

### Local Codex automatic updater

Run from a reviewed checkout or from the extracted portable package's `plugins/sports-betting-expert/` folder, after installing requirements into a project venv:

```bash
.venv/bin/python scripts/install_updater.py install
.venv/bin/python scripts/install_updater.py status
.venv/bin/python scripts/install_updater.py update-now
.venv/bin/python scripts/install_updater.py uninstall
```

Windows equivalent: `.venv\Scripts\python.exe scripts\install_updater.py install` (same four actions). `--codex /absolute/executable` overrides discovery. Set CODEX_HOME before setup to select a profile; the scheduler retains it. One scheduler per OS user checks that profile, with all installations inside it; reinstalling the scheduler selects a different profile rather than adding a second background job.

macOS uses a per-user launchd LaunchAgent at login and daily. Linux uses a per-user systemd timer five minutes after its user manager starts and daily while running. Windows uses an InteractiveToken task at user logon with daily repetition while signed in, LeastPrivilege and no password. Linux without a running user systemd manager supports `update-now`; no root/linger changes are made by the installer. Git and Codex must be available in the scheduled user's environment. Dependencies install into a dedicated updater venv.

The updater clones main, enforces identity and strictly newer SemVer, runs tests, builds/validates artifacts, checks immutable marketplace snapshots, refreshes the local source/cache, and verifies installed bytes. It rejects changed commits, downgrade/same-version candidates and unverified sources. Cache/install failure triggers rollback. Installation of a scheduler does not install the plugin itself. Start a new chat (or restart Desktop if necessary) after updates. This scheduler does not update hosted ChatGPT/Claude/Gemini/Grok accounts.

Manual Git refresh is also available, but does not provide the repository updater's validation and rollback sequence:

```bash
codex plugin marketplace upgrade sports-betting-expert --json
codex plugin add sports-betting-expert@sports-betting-expert --json
```

For filesystem-only Codex Skill discovery, copy the canonical folder to the documented `.agents/skills/` project/user Skill directory supported by your runtime. Update it explicitly; discovery is not a scheduled updater.

## Other hosts and developer APIs

- [Claude plugin, Skill, Code and private organization mirror](INSTALL-CLAUDE.md)
- [Gemini Apps, Enterprise, CLI and legacy Gem](INSTALL-GEMINI.md)
- [Grok native Skills, compatible Build plugins and Bot limitations](INSTALL-GROK.md)
- [OpenAI API/sandbox and optional Claude Enterprise validation](docs/API-INSTALL.md)

## Behavior smoke checks after installation

Start a new session and ask:

1. `Какие данные нужны, чтобы проверить value в футбольном матче?` — current fixture, market, observed odds and evidence; no invented prices.
2. `Составь прематч-экспресс из тенниса.` — reject new pre-match tennis selections, explain live-only conditions.
3. `Коэффициенты 1.8 и 2.1, ставка 10. Рассчитай выплату и прибыль.` — payout 37.80 and net profit 27.80, distinct from expected return.
4. `Оцени live-ставку без текущего счета.` — request essential live evidence; no fabricated pick.

These prompts are account checks, not claims that hosted installation has already been tested.
