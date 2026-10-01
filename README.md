# Sports Betting Expert

Canonical, multi-host skill for evidence-led sports betting analysis. It handles matches, offered odds, accumulators, coupon screenshots, settlement rules, live positions, bankroll questions and performance review without treating uncertain forecasts as facts.

## One source, five hosts

The maintained source is [`skills/sports-betting-expert`](skills/sports-betting-expert). Release artifacts are generated from it:

| Host | Artifact | Invocation boundary |
|---|---|---|
| Codex / ChatGPT desktop | Git marketplace or Codex installer ZIP | Automatic after installation; scheduled checker tracks GitHub `main` |
| ChatGPT Web | Portable skill ZIP | Automatic after upload and enablement |
| Claude Web | Same portable skill ZIP | Automatic after upload and enablement |
| Gemini Web | Canonical `SKILL.md` / skill ZIP | Automatic when relevant after import and enablement; rollout/account availability applies |
| Grok Web | Project Markdown | Persistent only inside the Project |

See [INSTALL.md](INSTALL.md) for exact steps. Tennis betting selections are always live-only. `priority-live-tennis` is an optional sport-order profile and is not active by default.

Gemini Apps now support native reusable skills, including `SKILL.md` import, automatic relevance-based use, and combining multiple skills. Google is transitioning Gems to skills; the dedicated Gemini Gem bundle published with `v1.0.2` is therefore retained only as a legacy release artifact. See Google's [Create & manage skills](https://support.google.com/gemini/answer/17094296?hl=en) and [Gems-to-skills transition](https://support.google.com/gemini/answer/18560919?hl=en) documentation. Availability can vary by account and rollout.

## Automatic Codex and ChatGPT desktop updates

The Codex and ChatGPT desktop personal marketplace entries point to `https://github.com/rrpauls/sports-betting-expert` on `main`. `scripts/update_plugin.py` checks that branch daily, validates a candidate plugin and its test suite, and compares strict semantic versions before changing the installation. A newer valid version uses `codex plugin marketplace upgrade` for a Git marketplace. For a local archive install, the checker atomically refreshes the local plugin source folder and uses `codex plugin add` to refresh its cache. Same-version, older, or invalid candidates are left unapplied. Restart ChatGPT desktop after an update to load the new local plugin files. See [INSTALL.md](INSTALL.md) to enable the macOS LaunchAgent.

## Verified release status

Status for release `v1.0.2` as of 2026-09-17:

| Surface | Evidence | Result |
|---|---|---|
| Canonical skill and calculator | Unit, contract and reproducible-build tests | Passed, 10/10 |
| Codex | Marketplace install; plugin and nested-skill validation | Installed, enabled and passed |
| Portable package | ZIP layout and artifact validation; `claude plugin validate --strict` | Passed |
| ChatGPT Web | Installed skill content plus relevant, tennis-gate, arithmetic and unrelated-query smoke prompts | Passed |
| Claude Web | Uploaded portable skill plus tennis-gate, arithmetic and unrelated-query smoke prompts | Passed |
| Gemini Gem (legacy `v1.0.2`) | Instructions and four Knowledge files replaced with `v1.0.2`; Gem-scoped behavior checked manually | Passed (user-verified) |
| Grok Web | Project adapter replaced with `v1.0.2`; Project-scoped behavior checked manually | Passed (user-verified) |

The table above records the historical `v1.0.2` verification state. For current Gemini installations, prefer the canonical skill path described in [INSTALL-GEMINI.md](INSTALL-GEMINI.md). Native Gemini Skills are platform-supported but were introduced after the `v1.0.2` verification run, so this repository does not claim a separate Gemini Skills smoke-test result for that release. Grok remains Project-scoped.

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
