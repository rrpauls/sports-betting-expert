# Sports Betting Expert

Canonical, multi-host skill for evidence-led sports betting analysis. It handles matches, offered odds, accumulators, coupon screenshots, settlement rules, live positions, bankroll questions and performance review without treating uncertain forecasts as facts.

## One source, five hosts

The maintained source is [`skills/sports-betting-expert`](skills/sports-betting-expert). Release artifacts are generated from it:

| Host | Artifact | Invocation boundary |
|---|---|---|
| Codex | Git marketplace or Codex installer ZIP | Automatic after plugin installation |
| ChatGPT Web | Portable skill ZIP | Automatic after upload and enablement |
| Claude Web | Same portable skill ZIP | Automatic after upload and enablement |
| Gemini Web | Gem instructions and Knowledge ZIP | Persistent only inside the selected Gem |
| Grok Web | Project Markdown | Persistent only inside the Project |

See [INSTALL.md](INSTALL.md) for exact steps. Tennis betting selections are always live-only. `priority-live-tennis` is an optional sport-order profile and is not active by default.

## Build and validate

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
python3 scripts/validate_artifacts.py
python3 /Users/owner/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/sports-betting-expert
python3 /Users/owner/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
claude plugin validate --strict .
```

`scripts/build_release.py` writes deterministic release files under `dist/`. Run it twice and compare `dist/SHA256SUMS` to verify reproducibility.

## Boundaries

The calculator performs conditional arithmetic; it does not retrieve odds or predict results. The skill never places bets or operates an account. Current claims and prices require current sources or a clearly labeled user-provided snapshot.

## License

MIT
