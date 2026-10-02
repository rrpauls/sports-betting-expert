# Installation and update audit

Checked against official documentation on **2026-10-02**. This is the authoritative matrix; host guides explain the procedures. A supported package is locally validated, not proof that a vendor accepted it in an account. Product rollout and administrator policy still apply.

Package shorthand (all use root `plugin.json` version): **OpenAI** = `*-openai-plugin-vVERSION.zip`; **Skill** = `*-skill-vVERSION.zip`; **Codex** = `*-codex-vVERSION.zip`; **Claude** = `*-claude-plugin-vVERSION.zip`; **Organization** = `*-claude-marketplace-vVERSION.zip`; **Gemini** = `*-gemini-skill-vVERSION.zip`.

| Environment | Installation method | Package/manifest | Update source | Native automatic update | Manual update | Requirements / limitations |
|---|---|---|---|---|---|---|
| ChatGPT public Plugin Directory | Plugins → search → install (+) | OpenAI, after publisher submission | Published directory version | Platform manages installed version; no Git tracking | Publisher uploads/submits next package | Directory acceptance is external; this repository is not claimed listed [O1,O2] |
| Codex public plugin directory | Directory install | Same OpenAI package | Published directory version | Platform-managed version | Publish new package | Same directory as ChatGPT; start new chat [O1,O2] |
| ChatGPT manual plugin upload | Admin → Plugins → Add → Upload plugin | OpenAI | New ZIP | No | Details → Upload new version | Upload permission/eligible owner or admin; new chat [O1] |
| ChatGPT standalone Skill | Skills → Create → Upload from your computer | Skill | New ZIP | No | Replace/upload updated skill | Eligible Business, Enterprise, Healthcare, Edu; policy and surface availability [O3] |
| ChatGPT Business/Enterprise workspace distribution | Admin upload then set role installation policy | OpenAI | Admin upload | No repository sync for ZIP | Upload new version | Admin may provision installation; content update is separate [O1] |
| ChatGPT GitHub workspace marketplace | Workspace settings → Plugins → Add → Import marketplace | `.agents/plugins/marketplace.json` | GitHub main | Yes, daily sync enabled on import | Marketplaces → Sync now | Public/private github.com; authorized admin; branch tracking, not fixed commit [O4] |
| Codex CLI Git marketplace | `codex plugin marketplace add rrpauls/sports-betting-expert --ref main`; `codex plugin add sports-betting-expert@sports-betting-expert` | `.agents/plugins/marketplace.json` | GitHub main | No documented background plugin-content updater relied on here | Marketplace upgrade then plugin add; validated repository updater preferred | CLI and Git; custom scheduler is opt-in [O2,O5] |
| Codex CLI portable marketplace | Extract Codex; add extracted marketplace path, then plugin add | Codex, local catalog | GitHub main through repository updater | No; repository scheduler provides automation | `install_updater.py update-now` | Keep extracted path; updater validates cache and restores source on failure |
| ChatGPT Desktop / local Codex runtime | Directory or local marketplace exposed by that runtime | OpenAI/Codex | Appropriate directory, Git or local source | Depends on installation source | Same source procedure | Local execution only; hosted ZIP installs do not acquire a local scheduler [O1,O2] |
| OpenAI Skills API / hosted shell | `POST /v1/skills`, mount `skill_reference` | Skill | Uploaded API skill versions | No Git sync; `latest` follows explicitly uploaded versions | `POST /v1/skills/{id}/versions` | Developer API access; 50 MB ZIP, 500 files, 25 MB/file [O6] |
| OpenAI Agents API hosted sandbox | Inline ZIP in `environment.plugins` | OpenAI includes Codex overlay | Session/template payload | No | Replace payload/template, create session | One plugin folder; name/description match overlay [O7] |
| OpenAI self-hosted capability directory | Extract Skill into absolute capability directory | Skill | Operator-managed filesystem | No | Replace reviewed files and start session | Explicit `capability_directories`; execution/tools depend on sandbox [O6] |
| Claude personal Skill | Customize → Skills → + upload | Skill | New ZIP | No Git sync | Re-upload/replace | Free/Pro/Max or allowed Team/Enterprise; code execution enabled [A1] |
| Claude personal plugin upload | Customize → Plugins → Personal plugins → + → Upload plugin | Claude | New ZIP | No | Upload next plugin version | Web, Desktop Chat, Cowork; account/policy permits plugins [A2] |
| Claude Web/Desktop personal repository marketplace | Personal plugins → + → Add marketplace → Add from a repository | `.claude-plugin/marketplace.json` | Public GitHub repository | Source sync exists; do not assume a background cadence | Refresh through repository controls | Personal repository import is distinct from organization import [A2] |
| Claude Code Git marketplace | `claude plugin marketplace add rrpauls/sports-betting-expert`; `claude plugin install sports-betting-expert@sports-betting-expert` | Claude catalog/plugin at repo root | GitHub main | Yes after enabling marketplace auto-update (third-party default off) | `claude plugin marketplace update sports-betting-expert`; `claude plugin update sports-betting-expert@sports-betting-expert` | Session-start update; `/reload-plugins` or next session [A3,A4] |
| Claude Code local plugin | `claude --plugin-dir /absolute/plugin` | Extracted Claude | Filesystem | No | Replace extracted plugin, reload | Development/local use; no custom scheduler [A4] |
| Claude Code filesystem skill | Copy canonical folder to `.claude/skills/` or `~/.claude/skills/` | Skill | Filesystem | No | Replace files | Discovery is not installation/update automation [A5] |
| Claude Team/Enterprise manual organization marketplace | Organization settings → Plugins & skills → Add → Upload a plugin | Claude | Admin upload | New version served after explicit upload, not Git sync | Same-name ZIP upload | Owner/admin; valid ZIP under 200 MB [A6] |
| Claude organization GitHub/GitLab marketplace | Connect private/internal mirror; relative plugin sources | Organization export | Mirror branch | Native source sync when configured | Trigger sync | **Public github.com/gitlab.com repository cannot be connected directly**; private/internal mirror and app access required [A6] |
| Claude Enterprise Plugins API | Validate archive; optionally publish plugin/version | Organization for validation; Claude for publish | Authorized CI uploads | Served version follows uploads unless pinned | Explicit upload/promote | Enterprise only, scoped admin key, beta header; excludes HIPAA-ready/Console orgs; cannot connect marketplace via API [A7] |
| claude.ai → Claude Code | Enable skills; sign into same Claude account | Account skill/plugin | Claude account | One-way session-start and ~10 minute skill checks | Edit/upload in Claude account | Claude Code ≥2.1.273; no API-key/Bedrock sync; not GitHub sync [A1] |
| Gemini Apps web/Mac/mobile | Settings → Skills → Upload → Create | Gemini (root SKILL.md) | New ZIP | No documented repository sync | More → Replace skill, Save | Personal account 18+, Keep Activity; rollout; scripts cannot access internet [G1] |
| Gemini Apps with work/school account | Not currently eligible for consumer Skills | None | — | — | Legacy Gem if available | Consumer help explicitly excludes work/school; distinct from Enterprise [G1] |
| Gemini Enterprise Standard/Plus/Pay-as-you-go | Skills → + → Upload skill → Import | Gemini | Owner-managed upload/edit | No documented repository sync | Edit/Save or import updated package | Admin enables skills; root SKILL.md; Python/Bash only [G2] |
| Gemini Enterprise shared skill / Frontline | Skills → + → Browse skills → Shared with me → Install | Shared Gemini skill | Owner's shared skill | Sharing is documented; no Git sync or promised refresh cadence | Owner edits; recipient uses supported skill controls | Sharing enabled, possible admin review; Frontline cannot create/upload [G2] |
| Gemini CLI | `gemini skills link ./skills/sports-betting-expert`; filesystem skill directories | Same canonical Skill | Local reviewed checkout | No claimed Git auto-update | Pull reviewed source; `/skills reload` | User/workspace skills; remote installs require consent [G3] |
| Gemini legacy Gem | Explore Gems → New Gem; instructions + Knowledge | `*-gemini-legacy-gem-*.zip` | New release | No | Replace instructions/Knowledge | Compatibility while Gems remain on account; never a native Skill [G4] |
| Grok web/iOS/Android native skill | Upload instructions/reference files or describe/save skill | Canonical SKILL.md + references extracted from Skill | New release files | No documented repository sync | Replace saved skill from canonical files | Official announcement supports custom file input; no verified ZIP schema claimed for hosted uploader [X1] |
| Grok Build filesystem Skill | Copy folder to `.grok/skills/` or `~/.grok/skills/`; extra `[skills] paths` | Skill | Filesystem | No | Replace files, inspect/start session | Plugin-provided skills and `~/.agents/skills/` also discovered [X2] |
| Grok Build plugin | `grok --plugin-dir /absolute/plugin`; `.grok/plugins/`, `~/.grok/plugins/` | **Reuse Claude** | Filesystem | No | Replace files/start session | Documented Claude Code compatibility; no separate manifest needed [X2] |
| Grok Build marketplace | Read installed Claude marketplace or use `/plugins` Marketplace tab | **Reuse Claude catalog** or generated `.grok-plugin/marketplace.json` | Configured marketplace | No automatic-update guarantee found | Refresh/update via marketplace UI | `[[marketplace.sources]]`, known_marketplaces; pinned remote sources checked by Grok; no invented CLI flags [X2,X3] |
| Grok Bot private/team skill | Provide canonical files, ask Bot to save skill; attach to team Bot | Canonical skill resources | Private/team skill owner | No Git content sync established | Update saved skill | Marketplace → Your plugins → Manage plugins and skills; shared team Bot skills [X4,X5] |
| Grok Bot organization plugin connector controls | Not implemented as a connector | None | — | — | — | Official team marketplace controls concern MCP connectors; this plugin has no MCP server [X6] |
| Grok legacy Project | Replace generated Markdown in Project | `*-grok-web-*.md` | New release | No | Replace file | Explicit fallback, scoped to that Project |

## Invocation, installation, content updates and refresh

Enabled skills can be selected automatically from their description; that does not install them or refresh their content. Installation starts with the user/admin or a workspace provisioning policy. Update priority is native repository sync, native marketplace updater, account sync, validated local updater, then explicit replacement. New sessions are the conservative validation point after replacement. Claude Code documents `/reload-plugins`; Gemini CLI documents `/skills reload`. Hosted environments never run this repository's local scheduler.

## Official sources and decisions

- **O1** [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)
- **O2** [Portable package and Codex compatibility](https://developers.openai.com/plugins/build/plugins)
- **O3** [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- **O4** [GitHub marketplace synchronization](https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github)
- **O5** [Codex CLI](https://learn.chatgpt.com/docs/codex/cli), plus installed CLI `plugin --help` and `plugin marketplace add --help` verified locally.
- **O6** [Skills API, hosted and self-hosted](https://developers.openai.com/api/docs/guides/tools-skills)
- **O7** [Agents API plugins](https://developers.openai.com/api/docs/guides/agents-api/tools/plugins)
- **A1** [Claude skills and account sync](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- **A2** [Claude personal plugins](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)
- **A3** [Claude installation and automatic updates](https://code.claude.com/docs/en/discover-plugins)
- **A4** [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- **A5** [Claude Code skills](https://code.claude.com/docs/en/skills)
- **A6** [Organization marketplaces and private repository restriction](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
- **A7** [Enterprise Plugins API](https://platform.claude.com/docs/en/manage-claude/plugins-api)
- **G1** [Gemini Apps native Skills and upload limits](https://support.google.com/gemini/answer/17094296?hl=en)
- **G2** [Gemini Enterprise Skills](https://docs.cloud.google.com/gemini/enterprise/docs/skills)
- **G3** [Gemini CLI Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- **G4** [Gems transition](https://support.google.com/gemini/answer/18560919?hl=en)
- **X1** [Grok Skills web/iOS/Android](https://x.ai/news/grok-skills)
- **X2** [Grok Build discovery and Claude compatibility](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- **X3** [Official xAI marketplace source and pinning](https://github.com/xai-org/plugin-marketplace)
- **X4** [Bot private Skills](https://docs.x.ai/grok-bot/skills-routines-and-automations)
- **X5** [Team Bot skills](https://docs.x.ai/grok-bot/team-bots)
- **X6** [Bot organization connector controls](https://docs.x.ai/grok-bot/teams-and-enterprises)

No made-up hosted GitHub updater, consumer Google Workspace Skill upload, Grok Bot connector wrapping, or directory submission is implemented. Gemini Enterprise is supported separately from consumer Google Workspace accounts. Hosted Grok ZIP acceptance and background marketplace update timing lack a verified specification, so the documented file-import/compatible local paths are used. Claude organization APIs validate a public repository anonymously but that **does not** make it eligible for organization source connection.
