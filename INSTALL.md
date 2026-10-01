# Installation

## Codex

```bash
codex plugin marketplace add rrpauls/sports-betting-expert --ref main
codex plugin add sports-betting-expert@sports-betting-expert
```

The repository and personal marketplace catalogs point the plugin source at GitHub `main`. For Git marketplace installs, the daily checker validates Codex's refreshed snapshot and installs only when it resolves to the same commit that passed validation; if `main` moves during the check, the update waits for the next run. Direct Git installs without a verifiable marketplace snapshot are left unchanged. For an archive install, the checker verifies the installed repository identity, replaces the complete local source tree, and then uses `codex plugin add` to refresh Codex's cache.

The Codex ZIP includes the updater, its YAML-validation dependency list, the LaunchAgent installer and its plist template. From a repository checkout, install the updater dependency and run a one-time check with:

```bash
pyenv exec python -m pip install --user -r requirements-updater.txt
pyenv exec python scripts/update_plugin.py
```

From the extracted Codex ZIP, run the equivalent commands from its root:

```bash
pyenv exec python -m pip install --user -r plugins/sports-betting-expert/requirements-updater.txt
pyenv exec python plugins/sports-betting-expert/scripts/update_plugin.py
```

To enable daily checks on macOS, generate a user-specific LaunchAgent from either a repository checkout or extracted ZIP:

```bash
pyenv exec python scripts/install_updater.py
# For an extracted ZIP, use:
# pyenv exec python plugins/sports-betting-expert/scripts/install_updater.py
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.rrpauls.sports-betting-expert-updater.plist
```

The installer fills in the current Python, updater, Codex CLI, home and log paths. The LaunchAgent checks once per day while the user session is logged in. A candidate is applied only when its version is newer and its manifest, YAML frontmatter, artifact validation, and test suite pass. Git marketplaces install only the validated snapshot; local archive installs refresh their complete source folder atomically and restore both source and Codex cache if the post-install check fails. Restart ChatGPT desktop after an update to load the new local plugin files.

Start a new Codex task after installation so the new skill catalog is loaded.

For an archive install, extract `sports-betting-expert-codex-v1.0.2.zip` and run:

```bash
codex plugin marketplace add ./sports-betting-expert-codex
codex plugin add sports-betting-expert@sports-betting-expert
```

## ChatGPT Web

Open **Plugins → Skills → Create → Upload from your computer**, upload `sports-betting-expert-skill-v1.0.2.zip`, and enable the skill. Availability depends on the account and workspace settings.

## Claude Web

Enable code execution/file creation, open **Customize → Skills → Add → Create skill → Upload a skill**, upload `sports-betting-expert-skill-v1.0.2.zip`, and enable it.

## Gemini Web

Gemini Apps now support native skills based on `SKILL.md`. Follow [INSTALL-GEMINI.md](INSTALL-GEMINI.md) and prefer the canonical skill over the older Gem adapter. Gemini can automatically apply an enabled skill when it is relevant, and skills can be combined. Availability still depends on Google's account/rollout state.

The published `sports-betting-expert-gemini-v1.0.2.zip` remains a legacy Gem bundle for the historical `v1.0.2` release; it is not the preferred installation path when native Gemini Skills are available.

## Grok Web

Create or open a Grok Project and upload `sports-betting-expert-grok-web-v1.0.2.md`. Use conversations inside that Project. This does not install an account-wide skill.

## Smoke prompts

1. Relevant: `Проверь матч из моего сообщения и скажи, при какой цене появляется value.`
2. Coupon: `Разбери этот купон, правила расчёта и самое слабое плечо.`
3. Live: `Счёт и состояние матча такие-то; пересчитай сценарии без выдуманных live-данных.`
4. Negative routing: `Кто выиграл вчерашний матч?` — answer directly without forcing a betting report.
5. Tennis gate: `Оцени pre-match теннисный рынок.` — do not recommend or add a tennis bet; explain that tennis selections are live-only.
6. Profile on: `Используй профиль priority-live-tennis.` — apply football → baseball → cricket screening order; keep tennis live-only.
