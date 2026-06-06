> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick start AIM 2.0

Use this page when you want the shortest practical start into the current AIM 2.0 operating model.

This is the front-door operating path for AIM 2.0 after setup, whether you use Personal AIM, Team AIM, or Enterprise AIM.

## Choose your start mode

Pick one:

- Personal AIM: use AIM yourself with no required committed AIM files
- Team AIM: share a small repo profile with the team through root `aim.profile.yaml`
- Enterprise AIM: use AIM with safe isolation defaults so AIM-internal artifacts are not committed by accident

If the repository owner explicitly wants AIM product docs and adapter helpers committed into the repo, use the Full embedded AIM footprint in [Install AIM 2.0](install-aim-2.0.md).

## Personal AIM

Choose Personal AIM when one developer wants to start AIM without repository mutation.

What this means:

- personal hints live at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- working state stays local
- AIM docs come from the installed package, adapter, or canonical AIM repo
- no committed AIM files are required by default

Normal startup path:

```text
/aim start "EPIC: <desired outcome>"
Mode: Strict
Cost profile: Cost Control
```

If slash commands are not available in the active adapter, state the same intent in plain language.

What AIM should do next:

1. read local AIM state first when it exists
2. read root `aim.profile.yaml` when it exists as the primary shared baseline
3. apply compatible Personal AIM profile hints when they exist
4. inspect the directly affected area before broad docs
5. load short authoritative docs only when risk or missing evidence requires them
6. keep Personal hints local unless you intentionally promote shared facts into Team AIM

If the user-level store is unavailable, continue with session-only hints; never persist repo-awareness under `.aim/`.

## Team AIM

Choose Team AIM when the team wants shared repo adaptation without copying the full AIM method into the repository.

Before the first shared run, create or reuse root `aim.profile.yaml` as the tiny Team AIM profile.

What this means:

- shared repo profile lives at root `aim.profile.yaml`
- working state stays local by default
- AIM docs remain linked or installed, not copied wholesale
- the team shares commands, locality hints, risk zones, and short authoritative docs

Normal startup path:

```text
/aim start "EPIC: <desired outcome>"
Mode: Strict
Cost profile: Cost Control
```

If slash commands are not available in the active adapter, state the same intent in plain language.

What AIM should do next:

1. read local AIM state first when it exists
2. read root `aim.profile.yaml` as the primary shared team baseline
3. apply compatible Personal AIM profile hints for local reuse
4. inspect the directly affected area before broad docs
5. expand only when risk, stale profile facts, ownership boundaries, or missing evidence require it

## Personal vs Team in one rule

Choose Personal AIM when the repo should not change.
Choose Team AIM when the team intentionally wants a tiny shared repo profile.

The difference is sharing:

- Personal AIM keeps repo knowledge local by default
- Team AIM shares repo knowledge intentionally
- both keep active working state separate from the reusable profile

## Execution defaults

Make the execution mode and cost profile explicit when you start.

Use one mode:

- `Mode: Strict`
- `Mode: Auto`

If you do not specify a mode, AIM defaults to `Strict`.

Use one cost profile:

- `Cost profile: Standard`
- `Cost profile: Cost Control`
- `Cost profile: Deep`

Use `Cost Control` for normal low-risk work, cleanup, documentation maintenance, and narrow reversible fixes.
Use `Deep` for trust-sensitive, migration, deployment, security, API, or broad public-method work.

## Cost-aware default

Start with `Cost Control` when the work is reversible and low risk.
Move to `Standard` or `Deep` only when trust, data correctness, deployment, migration, security, or broader product behavior justifies the extra depth.

## Common follow-up commands

- `/aim continue`
- `/aim validate`
- `/aim calibrate-repo`
- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`
- `/aim help`

If slash commands are unavailable, use the same intent in plain language.

## What a normal startup should show

Profile-first startup is part of the visible user path.
When AIM reuses Personal or Team profile data, the operator should see a compact profile-source summary during startup or Gate B.

Expected summary shape:

```text
Profile source: team: aim.profile.yaml (ready)
Layering: personal hints over team baseline
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <directly affected area>
Avoided context: <broad docs, adapter docs, repo-wide scan, or none>
Expansion reason: <none | missing evidence | stale profile | risk | ownership | user requested Deep>
Cheap validation first: <nearest command or check>
```

If no Personal or Team profile exists yet, AIM should say `Profile source: none` and continue with locality-first discovery instead of pretending reuse happened.

After installation, run `/aim calibrate-repo` when readiness is `needs_calibration` or `partially_ready`.
Calibration starts with cheap repository evidence and expands only for uncertainty, risk, conflict, or explicit user direction.

## Keep these boundaries clear

- runtime: how AIM runs
- repo profile: reusable repo knowledge
- working state: current Epic, increment, and gate state
- docs: reference material

Do not treat the repo profile as working state.
Do not treat the docs as the install footprint.

## Start here, go deeper only if needed

- For repository setup, embedded AIM, or adapter packaging: [Install AIM 2.0](install-aim-2.0.md)
- For the broader adoption model: [AIM 2.0 low-footprint adoption](aim-2-low-footprint-adoption.md)
- For troubleshooting start, resume, validation, and adapter behavior: [Troubleshoot AIM 2.0](troubleshoot-aim-2.0.md)
- For Personal profile storage details: [AIM 2.0 Personal local profile storage](personal-local-profile-storage.md)
- For the tiny shared Team profile: [AIM 2.0 Tiny Team Profile Artifact](team-profile-artifact.md)
- For the compact startup summary contract: [AIM 2.0 Profile Source Summary](profile-source-summary.md)
