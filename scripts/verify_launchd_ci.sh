#!/bin/bash
set -euo pipefail

label="com.rrpauls.sports-betting-expert-ci-$RANDOM"
uid="$(id -u)"
launch_agents="$HOME/Library/LaunchAgents"
mkdir -p "$launch_agents"
agent="$launch_agents/$label.plist"
umask 077
cleanup() {
  launchctl bootout "gui/$uid" "$agent" >/dev/null 2>&1 || true
  rm -f "$agent"
}
trap cleanup EXIT

LABEL="$label" AGENT="$agent" python3 - <<'PY'
import os
import plistlib

payload = {
    "Label": os.environ["LABEL"],
    "ProgramArguments": ["/usr/bin/true"],
    "RunAtLoad": False,
    "StartInterval": 86400,
}
with open(os.environ["AGENT"], "wb") as stream:
    plistlib.dump(payload, stream)
PY

launchctl bootstrap "gui/$uid" "$agent"
launchctl print "gui/$uid/$label" >/dev/null
launchctl bootout "gui/$uid" "$agent"
if launchctl print "gui/$uid/$label" >/dev/null 2>&1; then
  echo "launchd still reports $label after bootout" >&2
  exit 1
fi
echo "launchd bootstrap, registration, and bootout passed"
