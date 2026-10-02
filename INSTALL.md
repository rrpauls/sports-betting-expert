# Installation and updates

Automatic skill invocation and automatic content updating are independent capabilities. The matrix summarizes the supported paths; account and workspace eligibility still applies.

| Host / installation type | Automatic invocation | Automatic content update | Update source | Update mechanism | Limitations / required permissions |
|---|---|---|---|---|---|
| Codex / ChatGPT Desktop Git marketplace | When relevant after enabling the plugin | Automatic after updater setup on macOS | GitHub `main`, with a newer semantic version for every distributed change | Dedicated updater virtual environment and daily macOS LaunchAgent; validates clean clone, build, artifact checks, then installs from the validated marketplace commit | Codex CLI and logged-in macOS user session required. Direct Git installs without a verifiable marketplace snapshot remain unchanged. Linux/Windows scheduling is not implemented. Restart desktop to load updated content. |
| Codex / ChatGPT Desktop portable ZIP | When relevant after enabling the plugin | Automatic after updater setup on macOS | GitHub `main`, with a newer semantic version for every distributed change | Validated updater replaces the local source folder atomically and refreshes Codex's cache | Same scheduler requirements. |
| ChatGPT Web manual Skill ZIP | When relevant after upload and enablement | No | Release ZIP produced from GitHub `main` | Replace/re-upload the ZIP | Requires upload permission and feature availability. The ZIP is a copy and does not track GitHub. |
| ChatGPT Web GitHub-managed workspace marketplace | When relevant after workspace installation and enablement | Yes, daily sync by OpenAI | GitHub marketplace repository, normally `main` | Workspace admin imports `.agents/plugins/marketplace.json`; use “Sync now” for an early refresh | Eligible managed workspace and admin GitHub access required. Workspace admins control installation policy. Do not install the local LaunchAgent for this hosted path. |
| Claude Web uploaded Skill ZIP | When relevant after upload and enablement | No | Release ZIP produced from GitHub `main` | Replace/re-upload the ZIP | Uploaded skill is a static copy. No GitHub-synced Claude Web organization marketplace is claimed. |
| Gemini Web native Skill | When relevant after import and enablement | No | Current canonical `SKILL.md` or release package | Re-import/replace after release | GitHub is not a live skill source; availability depends on account rollout. |
| Grok Web Project Markdown | In conversations inside that Project | No | Generated Markdown adapter from `main` | Replace the Project file | Project-scoped static content; no verified source synchronization. |

Root [`plugin.json`](plugin.json) is the authoritative release version. GitHub `main` is the canonical development and update source, but updates are intentionally applied only when the candidate semantic version is newer than the installed version. Do not change packaged plugin/skill/updater content without a version bump. CI rejects version regressions and same-version distributed changes.

## Codex and ChatGPT Desktop

### Git marketplace

Add the repository and install the plugin:

```bash
codex plugin marketplace add rrpauls/sports-betting-expert --ref main
codex plugin add sports-betting-expert@sports-betting-expert
```

Plugin installation alone does not enable scheduled update checks. On macOS, from a repository checkout, run:

```bash
python3 scripts/install_updater.py
```

For an extracted Codex ZIP, run the script from the packaged plugin directory:

```bash
python3 plugins/sports-betting-expert/scripts/install_updater.py
```

The single setup command creates a dedicated updater virtual environment, installs PyYAML there, copies the updater runtime into `~/Library/Application Support/Sports Betting Expert Updater`, creates and loads the per-user LaunchAgent, and verifies that launchd registered it. It preserves the Python used for setup and works with a normal supported `python3`; `pyenv` is not required. The launchd job checks once per day while the user is logged in.

Check registration and remove the scheduler/runtime with:

```bash
python3 scripts/install_updater.py status
python3 scripts/install_updater.py uninstall
```

The updater compares strict semantic versions. For a newer candidate, it runs candidate tests, builds artifacts from a fresh clone (which starts without `dist/`), and validates those artifacts. It temporarily pins the marketplace plugin source to the validated commit SHA, then verifies the installed versioned Codex cache against the validated bytes. If `main` moves before snapshot validation, the attempt stops and a later run retries. Local archive replacement is atomic and restores both the source folder and Codex cache after post-install failure. No automatic scheduler is provided for Linux or Windows.

Restart ChatGPT Desktop after an update to load the new skill content. Start a new Codex task so the updated skill catalog is loaded.

### Portable Codex ZIP

Build the current artifact, extract `sports-betting-expert-codex-v1.0.3.zip`, then add its local marketplace and plugin:

```bash
codex plugin marketplace add ./sports-betting-expert-codex
codex plugin add sports-betting-expert@sports-betting-expert
```

Run the updater setup command from the extracted plugin directory to enable daily macOS checks.

## ChatGPT Web

Choose one path:

1. **Manual Skill ZIP:** open **Plugins → Skills → Create → Upload from your computer**, upload `sports-betting-expert-skill-v1.0.3.zip`, and enable it. This portable upload does not sync with GitHub; replace/re-upload it for updates.
2. **GitHub-managed workspace marketplace:** an eligible workspace admin opens **Workspace settings → Plugins → Add → Import marketplace**, supplies `https://github.com/rrpauls/sports-betting-expert` as the source, leaves Path empty, and selects the repository's default branch (`main`). OpenAI performs daily marketplace sync; admins can select **Sync now**. The importing admin must retain GitHub access. Workspace policies and role permissions govern which members can install the plugin. Do not set up the local macOS updater for this hosted path.

OpenAI's currently documented marketplace manifest location is `.agents/plugins/marketplace.json`. See [Importing and syncing plugin marketplaces from GitHub](https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github).

## Claude Web

Enable code execution/file creation if required by the account, open **Customize → Skills → Add → Create skill → Upload a skill**, upload `sports-betting-expert-skill-v1.0.3.zip`, and enable it. To update, upload/replace with the next release ZIP. Claude's GitHub integration synchronizes selected repository context for chats/projects, not an uploaded Skill ZIP; no organization-marketplace sync is claimed for this host.

## Gemini Web

Gemini Apps support native skills based on `SKILL.md`. Follow [INSTALL-GEMINI.md](INSTALL-GEMINI.md) and import the canonical skill. Replace/re-import it after a release; GitHub is not a live skill source. The older v1.0.2 Gem ZIP remains a legacy artifact.

## Grok Web

Create or open a Grok Project and upload `sports-betting-expert-grok-web-v1.0.3.md`. Replace that static adapter after a new release. It applies inside that Project only and does not synchronize directly with GitHub.

## Verification prompts

1. Relevant: `Проверь матч из моего сообщения и скажи, при какой цене появляется value.`
2. Coupon: `Разбери этот купон, правила расчёта и самое слабое плечо.`
3. Live: `Счёт и состояние матча такие-то; пересчитай сценарии без выдуманных live-данных.`
4. Negative routing: `Кто выиграл вчерашний матч?` — answer directly without forcing a betting report.
5. Tennis gate: `Оцени pre-match теннисный рынок.` — do not recommend or add a tennis bet; explain that tennis selections are live-only.
6. Profile on: `Используй профиль priority-live-tennis.` — apply football → baseball → cricket screening order; keep tennis live-only.
