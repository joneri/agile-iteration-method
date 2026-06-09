# AIM Help

Map this command to `/aim help` from
`docs/workflow/adapter-command-contract.md`.

Keep the default response thin: show `/aim start`, `/aim continue`, `/aim
validate`, and the next useful command for the current checkpoint. This command
is read-only.

Detect onboarding state first, then recommend exactly one next action whenever
possible.

Use:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one short sentence>.
After that: <one short sentence>.
```

State routing:
- installed but not calibrated: `/aim calibrate-repo`
- calibrated but no Epic exists: `/aim start "EPIC: <desired outcome>"`
- Epic exists but is not approved: review Gate A and reply `approve` or `change: ...`
- Epic approved: `/aim continue`
- blocked: resolve the named blocking issue

When recommending `/aim start`, include a realistic example such as:

```text
/aim start "EPIC: Improve the onboarding flow so a new homeowner can list a room and understand the next review step"
```

Do not lead with internal file paths, runtime locations, adapter packaging,
architecture details, or a command inventory unless the user asks for deeper help
or a blocker requires that detail.

If command-file routing is unavailable, state that limitation and handle the
same `/aim help` intent in ordinary Claude chat.
