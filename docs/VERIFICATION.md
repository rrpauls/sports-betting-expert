# Distribution verification and remaining external steps

Local verification on 2026-10-02, macOS:

- Full canonical/distribution/updater/scheduler test suite: **62 tests passed**. Includes real Codex fresh local installation, injected post-install failure with verified source/cache rollback, and subsequent real upgrade from fixture 1.0.3 to 1.1.0 in temporary profiles. Native Codex integration is skipped on test hosts without Codex.
- Root manifest validated against the vendored official Agent Plugins 1.0 schema. Its supported constraints are checked offline and unsupported constraints fail closed, preserving existing updater runtimes without adding a dependency.
- Claude plugin and marketplace: installed Claude CLI `plugin validate --strict` passed.
- All eight artifacts validated against canonical contents and complete SHA-256 inventory. Repeated builds were byte-identical. Native Gemini Skill root/layout, accepted resources, offline-script constraints and API payloads passed.
- macOS launchd: real temporary bootstrap, registered-state check and bootout passed; no production updater was installed.
- Canonical `skills/sports-betting-expert/` has no task edits. Existing behavior and calculation tests, including the tennis gate, passed.

GitHub Actions defines the full Ubuntu/macOS/Windows matrix and native scheduler registration/status/removal. Ubuntu also executes a harmless generated service; Windows CI verifies XML/task registration/removal, while actual InteractiveToken task execution requires a signed-in interactive user. Those remote jobs have **not run as part of this local-only implementation**. Workflow YAML parses locally; that is not a CI pass.

The actual local Codex test found versioned local caches in the current runtime. The updater now verifies versioned caches first and the older `local` layout only as a compatibility fallback. It still verifies byte digests and rollback.

Remaining deployment actions: review and approve the branch, push/run remote CI when authorized, then approve a release tag push. Public OpenAI/Claude/xAI directory submissions, hosted-account smoke checks, API uploads and organization access policy changes are separate actions. A Claude organization GitHub connection needs a private/internal mirror and administrator authorization; the public canonical repository is not directly eligible. No release, vendor submission, hosted upload or organization-wide installation occurred.
