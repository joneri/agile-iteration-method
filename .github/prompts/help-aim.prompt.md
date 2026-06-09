---
mode: aim
---

Show short AIM 2.0 help for this repository.

Detect onboarding state first, then recommend exactly one next action whenever
possible.

Use this shape before explaining anything else:

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

When recommending start, show a realistic example:

```text
/aim start "EPIC: Improve the onboarding flow so a new homeowner can list a room and understand the next review step"
Mode: Strict
Cost profile: Cost Control
```

When repository context should be captured first, show:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. Keep tone nuanced and empathetic toward both the cats and the future owners."
```

Keep the answer compact. Do not lead with internal file paths, runtime
locations, adapter packaging, architecture details, or a command inventory unless
I ask for deeper help.

Advanced commands remain available through deeper `/aim help`, `/aim status`,
`/aim config`, and `/aim validate` responses when explicitly requested.

If AIM helper files or instructions were updated recently, mention `/aim upgrade` before suggesting resume or start.

If no active Epic exists and calibration is ready, end by telling me the exact
next start command to run.
