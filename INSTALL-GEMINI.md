# Gemini installation

The preferred release is `sports-betting-expert-gemini-skill-v1.1.0.zip`: **SKILL.md at the archive root**, canonical references, offline Python calculators/snapshot parsing, YAML and SVG assets. It contains no updater or Gem instructions. The builder validates root location, lowercase hyphenated name, accepted file types, a 100 MB total ceiling, and absence of networking/process imports in packaged Python scripts. Future scripts still require review for external actions.

## Gemini Apps (personal account)

Open **Settings → Skills → Upload**, choose the native Skill ZIP, review and **Create**. Keep it enabled and test in a new chat. Update using **More → Replace skill**, upload the new package and **Save**. [Google's current requirements](https://support.google.com/gemini/answer/17094296?hl=en): personal Google account, age 18+, Keep Activity on; rollout may limit availability. Web, Mac and mobile are documented; work/school accounts are currently excluded from this consumer route.

Scripts cannot make requests/actions on external websites. This skill's scripts operate on supplied data; current evidence must come from available host tools or explicitly labelled user snapshots. Supported textual resources are preserved without changing the canonical workflow. No GitHub synchronization is documented.

## Gemini Enterprise

Enterprise **Standard, Plus and Pay-as-you-go**, with administrator-enabled Skills: **Skills → + → Upload skill → Import**, choose the same root-layout native ZIP. It is enabled by default. Instructions can be updated through **Skills → skill → More → Edit → Save**; use a reviewed new upload for revised resource files and reconfigure sharing as required.

Sharing: skill owner chooses **More → Share**; the admin must enable sharing and may require review. Recipients use **Skills → + → Browse skills → Shared with me → Install**. Frontline can install shared skills but cannot create/upload. These are Enterprise app capabilities, not permission to upload consumer Skills using a work account. No repository synchronization or shared-skill refresh cadence is promised. Python/Bash execution only; skills cannot be used with agents. [Enterprise documentation](https://docs.cloud.google.com/gemini/enterprise/docs/skills).

## Gemini CLI

Use the canonical source folder, preserving scripts and references:

```bash
gemini skills link ./skills/sports-betting-expert
```

Alternatively copy it to `~/.gemini/skills/sports-betting-expert/` or project `.gemini/skills/sports-betting-expert/` (the `.agents/skills/` alias is supported). Update the reviewed checkout/files and run `/skills reload`. Linking reflects filesystem changes, not an automatic Git pull. Remote installs and activation have consent controls. [CLI documentation](https://geminicli.com/docs/cli/using-agent-skills/).

## Legacy Gem fallback

While an account still exposes Gems and lacks Skills, extract `sports-betting-expert-gemini-legacy-gem-v1.1.0.zip`. Open **Explore Gems → New Gem**, copy `gemini-gem-instructions.md` into Instructions, upload all Markdown files under `gemini-knowledge/` as Knowledge, preview and **Save**. Update by replacing instructions and Knowledge. The legacy bundle is not a native Skill and never tracks GitHub. Google is [migrating Gems to Skills](https://support.google.com/gemini/answer/18560919?hl=en); keep this route only while usable.
