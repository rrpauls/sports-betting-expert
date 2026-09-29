# Install as a Gemini Skill

Gemini Apps now support native reusable skills. The canonical source for this repository is [`skills/sports-betting-expert`](skills/sports-betting-expert), so native Gemini Skills are now the preferred installation path.

Google documents that Gemini can import a `SKILL.md` file or a skill ZIP, automatically apply relevant enabled skills, and combine multiple skills. Availability can vary by account and rollout. See:

- [Create & manage skills for Gemini Apps](https://support.google.com/gemini/answer/17094296?hl=en)
- [About the transition from Gems to skills](https://support.google.com/gemini/answer/18560919?hl=en)

## Native skill installation — recommended

1. Use the canonical directory `skills/sports-betting-expert/`.
2. Prepare a ZIP whose main folder contains `SKILL.md` plus the skill's `references/`, `scripts/`, `agents/` and supported text assets. If you build a Gemini-specific ZIP manually, keep `SKILL.md` at the skill root.
3. At [gemini.google.com](https://gemini.google.com), open **Settings → Skills**.
4. Choose **Upload** and select the `SKILL.md` file or the prepared skill ZIP.
5. Review the imported name, description and instructions, then create the skill.
6. Make sure the skill is active if your Gemini UI exposes an enable/disable control.
7. Start a normal Gemini chat and run the smoke prompts from [INSTALL.md](INSTALL.md). Gemini may apply the skill automatically when the prompt matches its description; where available, you can also invoke a skill explicitly from the chat UI.

For the full workflow, prefer the ZIP form so Gemini can access the canonical reference files and scripts as needed rather than importing only `SKILL.md`.

## Legacy Gem path for v1.0.2

The published `sports-betting-expert-gemini-v1.0.2.zip` predates native Gemini Skills and is a **legacy Gem adapter**, not the canonical skill package. Keep this path only for an account where Skills are not yet available.

To install that legacy bundle:

1. Extract `sports-betting-expert-gemini-v1.0.2.zip`.
2. At `gemini.google.com`, open **Explore Gems** and choose **New Gem**.
3. Name it `Sports Betting Expert`.
4. Copy the complete contents of `gemini-gem-instructions.md` into **Instructions**.
5. Under **Knowledge**, upload every Markdown file from `gemini-knowledge/`.
6. Preview with: `Объясни, какие данные тебе нужны для проверки value в футбольном матче.`
7. Click **Save**. Preview alone does not save the Gem.
8. Start a new conversation inside the saved Gem and run the smoke prompts from [INSTALL.md](INSTALL.md).

The legacy Gem is not synchronized with GitHub. Native Gemini Skills should use the canonical `SKILL.md`-based source instead.
