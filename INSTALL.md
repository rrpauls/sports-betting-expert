# Installation

## Codex

```bash
codex plugin marketplace add rrpauls/sports-betting-expert --ref main
codex plugin add sports-betting-expert@sports-betting-expert
```

The repository and personal marketplace catalogs point the plugin source at GitHub `main`. The daily checker handles GitHub-link installs through the marketplace upgrade command; for an archive install, it atomically refreshes the installed local source folder and then uses `codex plugin add` to refresh Codex's cache.

Run a one-time check with:

```bash
pyenv exec python scripts/update_plugin.py
```

For daily checks on macOS, install and load the LaunchAgent from the repository root:

```bash
mkdir -p ~/Library/LaunchAgents
cp launchd/com.rrpauls.sports-betting-expert-updater.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.rrpauls.sports-betting-expert-updater.plist
```

It checks once per day while the user session is logged in. A candidate is applied only when its version is newer and its manifest, nested skill, artifact validation, and test suite pass. Git marketplaces use `codex plugin marketplace upgrade`; local archive installs refresh their source folder atomically, then run `codex plugin add`. Restart ChatGPT desktop after an update to load the new local plugin files.

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

Follow [INSTALL-GEMINI.md](INSTALL-GEMINI.md). A Gem must be selected; it is not injected into unrelated Gemini chats.

## Grok Web

Create or open a Grok Project and upload `sports-betting-expert-grok-web-v1.0.2.md`. Use conversations inside that Project. This does not install an account-wide skill.

## Smoke prompts

1. Relevant: `Проверь матч из моего сообщения и скажи, при какой цене появляется value.`
2. Coupon: `Разбери этот купон, правила расчёта и самое слабое плечо.`
3. Live: `Счёт и состояние матча такие-то; пересчитай сценарии без выдуманных live-данных.`
4. Negative routing: `Кто выиграл вчерашний матч?` — answer directly without forcing a betting report.
5. Tennis gate: `Оцени pre-match теннисный рынок.` — do not recommend or add a tennis bet; explain that tennis selections are live-only.
6. Profile on: `Используй профиль priority-live-tennis.` — apply football → baseball → cricket screening order; keep tennis live-only.
