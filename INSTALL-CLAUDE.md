# Claude installation

See the [support matrix](docs/SUPPORT-MATRIX.md) for account restrictions and source links.

## Personal Web, Desktop Chat and Cowork

Native plugin: **Customize → Plugins → Personal plugins → + → Upload plugin**, select `sports-betting-expert-claude-plugin-v1.1.0.zip`. Replace with a later plugin ZIP when updating; an uploaded ZIP has no Git source.

Repository marketplace: in the same Personal plugins section choose **+ → Add marketplace → Add from a repository**, enter `https://github.com/rrpauls/sports-betting-expert`. Use that surface's repository refresh controls. Do not assume the Claude Code auto-update cadence applies to Web/Desktop personal plugins. [Official personal plugin guide](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).

Standalone Skill: enable code execution under **Settings → Capabilities** (or organization policy), then **Customize → Skills → +**, upload `sports-betting-expert-skill-v1.1.0.zip` and enable it. Update by replacing/re-uploading the Skill. Avoid enabling two copies of the same skill through both plugin and standalone routes.

## Claude Code

```bash
claude plugin marketplace add rrpauls/sports-betting-expert
claude plugin install sports-betting-expert@sports-betting-expert
claude plugin list
```

Third-party marketplace auto-update starts **off**. Run `/plugin`, select **Marketplaces → sports-betting-expert → Enable auto-update**. Claude Code refreshes enabled marketplaces after session start; apply with `/reload-plugins` or start the next session. Explicit update:

```bash
claude plugin marketplace update sports-betting-expert
claude plugin update sports-betting-expert@sports-betting-expert
```

Local plugin: extract the Claude ZIP, then `claude --plugin-dir /absolute/path/sports-betting-expert`. Filesystem Skill: copy `skills/sports-betting-expert/` to `~/.claude/skills/sports-betting-expert/` or your project's `.claude/skills/sports-betting-expert/`. Explicitly replace local files on update. [Claude's update rules](https://code.claude.com/docs/en/discover-plugins).

## One-way account synchronization

Sign into Claude Code **v2.1.273+** using the same Claude account where the Skill is enabled. Run `/skills` and check **claude.ai sync**. Sync runs on session start and checks changes roughly every ten minutes; it reads the account and does not modify it. API-key and cloud-provider sign-in do not receive account sync. `syncClaudeAiSkills: false` disables it. This follows account uploads/edits, not this repository's GitHub commits. [Official account sync](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## Organization distribution

Manual: organization owner/admin opens **Organization settings → Plugins & skills → Add → Upload a plugin**, uploads the **Claude plugin ZIP** (not the marketplace ZIP), then configures access. Uploading the same name replaces its version. Uploaded plugins appear on supported Claude surfaces and signed-in Code accounts.

Repository sync: **this public github.com repository cannot be connected directly to a Claude organization marketplace**. Export a complete marketplace, vendor it into a separate **private/internal** GitHub repository, and connect that mirror:

1. Build and validate locally.
2. Extract `sports-betting-expert-claude-marketplace-v1.1.0.zip` into an empty private marketplace repository. It contains `.claude-plugin/marketplace.json` plus `plugins/sports-betting-expert/` with its generated manifest and canonical skill. Sources are relative and self-contained.
3. Review and commit the export in that private repository. On each future release, replace only those vendored paths using the validated new export; do not manually edit the generated skill.
4. Connect the private repository from organization settings and authorize the Claude GitHub App. Choose the tracked branch and configure native sync/access. Trigger sync after the initial connection and inspect results.

The export also works as a local Claude Code marketplace (`claude plugin marketplace add /absolute/export`). A private/internal GitLab mirror is another vendor-supported organization source; follow its configured GitLab integration. [Organization rules](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization).

Optional Enterprise API archive validation and version deployment are in [API-INSTALL.md](docs/API-INSTALL.md). They are not part of ordinary CI and cannot connect a marketplace for you.
