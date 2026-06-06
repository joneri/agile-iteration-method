> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick Start AIM 2.0

Use this page when AIM is installed and you want to begin real work.

New to the product? Read the [public first-time journey](../product/getting-started.md) first.

## 1. Check Repository Readiness

Run:

```text
/aim calibrate-repo
```

Calibration verifies the smallest useful set of repository facts:

- technologies and package tooling
- likely validation commands
- important localities
- risk areas
- documents that should load only when relevant

Shared knowledge belongs in `aim.profile.yaml`.
Personal hints belong in user-level storage.
Active work state belongs in `.aim/`.

If slash commands are unavailable, ask AIM to verify and refine repository awareness.

## 2. Start the Epic

Use a desired outcome:

```text
/aim start "EPIC: <desired user outcome>"
```

Or use explicit intent:

```text
EPIC: <desired user outcome>
Mode: Strict
Cost profile: Standard
```

Avoid beginning with a list of implementation tasks.
AIM uses the Epic to decide what the next useful increment should be.

## 3. Choose Execution Style

- `Mode: Strict`: pause at Gate A, Gate B, and Gate E
- `Mode: Auto`: continue between increments unless escalation is required; Epic closure still requires explicit approval

Strict is a good default for first use and trust-sensitive work.
Auto is useful when the outcome and boundaries are already clear.

## 4. Choose Runtime Depth

- `Cost profile: Cost Control`: narrow, reversible, low-risk work
- `Cost profile: Standard`: normal product work
- `Cost profile: Deep`: security, migration, deployment, public APIs, or broad trust-sensitive changes

Cost profile changes context and verification depth.
It does not remove AIM roles, gates, ownership, or escalation.

## 5. Review Gate A

Confirm:

- outcome
- scope boundaries
- acceptance intent
- important risks

Reply `approve` when the Epic is right.
Use `change: ...` when it needs correction.

## 6. Review the Increment

AIM proposes one Done Increment.

In Strict mode, Gate B waits for approval.
The increment should deliver useful end-to-end value and state how it will be verified.

After implementation and review, Gate E reports:

- delivered behavior
- verification evidence
- remaining risk
- whether another increment is needed

Approve, request adjustment, continue, or close.

## Common Commands

- `/aim continue`
- `/aim status`
- `/aim validate`
- `/aim calibrate-repo`
- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`
- `/aim cost standard|control|deep`
- `/aim help`

## Choose an Adoption Mode

- **Personal**: local-first and flexible
- **Team**: small shared repo-awareness by agreement
- **Enterprise**: isolate AIM internals by default

See [Platforms and adoption modes](../product/platforms-and-adoption.md) for the newcomer explanation and [Operating modes](operating-modes.md) for the canonical rules.

## Need Help?

- [Installation](install-aim-2.0.md)
- [Troubleshooting](troubleshoot-aim-2.0.md)
- [Platform entrypoints](adapter-entry-model.md)
- [Canonical AIM workflow](agile-iteration-method.md)
