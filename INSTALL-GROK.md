# Grok installation

Native Skills are the primary integration. [xAI documents custom skill creation from conversation/file input on web, iOS and Android](https://x.ai/news/grok-skills). Its public announcement does not establish a strict hosted ZIP schema, so do not assume a plugin ZIP is accepted by the web Skill uploader.

For web/mobile, extract the standalone Skill ZIP, provide canonical `SKILL.md` and its `references/` files to the skill creation flow, and ask Grok to save the workflow as `sports-betting-expert`. Review the saved instructions, especially the live-only tennis gate, and test in a new chat. Updating the saved Skill from a newer release is explicit; it does not follow GitHub. Scripts work only where the host exposes execution and referenced resources. Import verification remains an account-side step.

## Grok Build

The native Agent Skill folder is the exact same canonical folder used by other local hosts. Copy it to project `.grok/skills/sports-betting-expert/` or user `~/.grok/skills/sports-betting-expert/`. Extra roots can be configured under `[skills] paths`; user `~/.agents/skills/` is also discovered. Use `/skills` or `grok inspect` to check discovery.

Plugins: extract **`sports-betting-expert-claude-plugin-v1.1.0.zip`**, then run:

```bash
grok --plugin-dir /absolute/path/sports-betting-expert
```

Or place the extracted plugin under project `.grok/plugins/` or user `~/.grok/plugins/`. Plugin-provided `skills/` is discovered. [Official Claude Code compatibility](https://docs.x.ai/build/features/skills-plugins-marketplaces) covers plugins and marketplaces, so there is no second independently maintained Grok manifest.

Marketplace: a Claude marketplace already registered on the machine is read alongside Grok configuration. Otherwise use the `/plugins` extensions modal's **Marketplace** tab with configured sources. The same `.claude-plugin/marketplace.json` works through the documented compatibility layer. A generated native `.grok-plugin/marketplace.json` also lists this same local plugin; the organization export includes both catalogs with the same plugin bytes. For a portable local catalog extract the Claude marketplace ZIP. Native Grok sources use `[[marketplace.sources]]`/known_marketplaces; follow the current UI/config documentation rather than guessed CLI commands. Refresh and install/update through those controls, then start a new session. **No background automatic content update is claimed.** The [official xAI marketplace](https://github.com/xai-org/plugin-marketplace) pins remote plugins to commits and checks checkout identity.

## Grok Bot and teams

Provide canonical instructions and references and ask the Bot to save the method as a private Skill. Inspect it under **Marketplace → Your plugins → Manage plugins and skills → Private skills**; `/` references saved skills. Private skills are shared across your Bots; a team Bot can use owner-managed team skills. Update them explicitly. [Private skill guidance](https://docs.x.ai/grok-bot/skills-routines-and-automations), [team Bot guidance](https://docs.x.ai/grok-bot/team-bots).

Organization marketplace connector controls are documented for MCP connectors. This package has no MCP server; no connector registration or organization-wide install is performed. No undocumented repository-backed Bot skill updater is supplied. [Organization limits](https://docs.x.ai/grok-bot/teams-and-enterprises).

## Legacy Project fallback

`sports-betting-expert-grok-web-v1.1.0.md` is an explicitly labelled Project-scoped fallback. Upload it to a Project only when the native Skill flow is unavailable, and replace it manually after updates. It is not the preferred native skill route.
