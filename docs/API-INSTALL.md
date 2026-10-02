# Optional developer/API installations

These operations require your vendor account and approval within your environment. Ordinary builds and CI need no secrets and send no API requests. The helpers only prepare payload files locally.

## OpenAI Skills API

The standalone Skill ZIP satisfies the one-top-level-folder upload layout and is checked for file count/size. Create it using the [Skills API](https://developers.openai.com/api/docs/guides/tools-skills):

```bash
curl --fail-with-body https://api.openai.com/v1/skills \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F 'files=@dist/sports-betting-expert-skill-v1.1.0.zip;type=application/zip'
```

Record the returned skill ID. Mount it in the shell tool environment's `skills` array as `{"type":"skill_reference","skill_id":"<returned-id>","version":"latest"}` or pin a reviewed numeric version. Explicitly upload a later version to `POST /v1/skills/{skill_id}/versions` using the same multipart `files` part. `latest` follows uploaded versions; it is not a GitHub sync. Default/pinned version behavior is controlled by the API caller.

Inline container Skill payload:

```bash
.venv/bin/python scripts/api_payloads.py skill --output /absolute/path/skill-container.json
```

The output's `skills` array can be supplied to the documented container creation endpoint. Add container settings appropriate to your API workflow.

## OpenAI Agents API hosted plugin

```bash
.venv/bin/python scripts/api_payloads.py plugin --output /absolute/path/plugin-environment.json
```

Use its `environment` object in a session-creation request with your agent/model configuration. It embeds the OpenAI plugin ZIP with a Codex overlay, matching name and description. Rebuild and regenerate after updates; change templates/new sessions explicitly. Existing sessions do not reload. See [hosted plugin documentation](https://developers.openai.com/api/docs/guides/agents-api/tools/plugins).

## Self-hosted capabilities

Extract the standalone Skill ZIP into `/workspace/capabilities/`, producing `/workspace/capabilities/sports-betting-expert/SKILL.md`. Then:

```bash
.venv/bin/python scripts/api_payloads.py self-hosted \
  --capability-directory /workspace/capabilities \
  --output /absolute/path/self-hosted-environment.json
```

Supply this environment in your self-hosted session creation, adapting the workspace path for your deployment. Filesystem replacement is operator-managed; create a new session after changes. Available tools/network policy still determine whether current evidence can be retrieved.

## Claude Enterprise validation and deployment

[Enterprise Plugins API](https://platform.claude.com/docs/en/manage-claude/plugins-api) requires an Enterprise organization (not Console; not HIPAA-ready), an admin key scoped `read:plugins` or `write:plugins`, `anthropic-version: 2023-06-01` and `anthropic-beta: ce-plugins-2026-09-01`.

Optional private-pipeline validation (archive validation sends content for review without storing or connecting a marketplace):

```bash
curl --fail-with-body --max-time 180 \
  https://api.anthropic.com/v1/organizations/plugin_marketplaces/validate_archive \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H 'anthropic-version: 2023-06-01' \
  -H 'anthropic-beta: ce-plugins-2026-09-01' \
  -F 'archive=@dist/sports-betting-expert-claude-marketplace-v1.1.0.zip;type=application/zip' \
  --output validation-report.json
jq -e '.valid == true' validation-report.json
```

HTTP success alone is not validation success. Archive limit is 32 MB; inspect plugin warnings/errors. Public `validate_repository` is anonymous and cannot validate a private mirror by URL. This differs from authenticated organization connection, which requires a private/internal marketplace on github.com.

For intentionally configured publishing, `POST /v1/organizations/plugins` creates an organization plugin; `POST /v1/organizations/plugins/{plugin_id}/versions` uploads its next immutable version. Use the vendor SDK with the **Claude plugin ZIP**, record returned IDs and scan status, and choose served-version policy before allowing members access. An unpinned served version follows each upload. This repository does not issue deployment writes or supply organization identifiers. Connecting a marketplace still happens in claude.ai; the API cannot create/connect it. No public directory submission is automated.
