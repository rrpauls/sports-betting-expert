# Installation

## Codex

```bash
codex plugin marketplace add rrpauls/sports-betting-expert --ref v1.0.2
codex plugin add sports-betting-expert@sports-betting-expert
```

Start a new Codex task after installation so the new skill catalog is loaded.

For an offline install, extract `sports-betting-expert-codex-v1.0.2.zip` and run:

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
