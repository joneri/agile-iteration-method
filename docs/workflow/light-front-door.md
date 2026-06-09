# AIM Light Front Door

## Purpose

Make AIM easier to start without removing the method depth that makes it reliable.

This is canonical AIM front-door and first-routing behavior.

The front door should help a user choose the next action first, not teach the full method first.

## How it works

AIM 2.0 detects onboarding state first, then recommends exactly one next action
whenever possible.

Use this default shape before showing commands, paths, or architecture:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one short sentence>.
After that: <one short sentence>.
```

Onboarding states:

| State | Meaning | Recommended next action |
| --- | --- | --- |
| 1. Installed but not calibrated | AIM files are present, but reusable repo knowledge is missing or stale. | `/aim calibrate-repo` |
| 2. Calibrated but no Epic exists | Repo awareness is ready and no active AIM runtime is in progress. | `/aim start "EPIC: <desired outcome>"` |
| 3. Epic exists but is not approved | Gate A is waiting for explicit user decision. | Review Gate A and reply `approve` or `change: ...` |
| 4. Epic approved | AIM has an approved checkpoint and can continue the current loop. | `/aim continue` |
| 5. Blocked | AIM cannot progress without resolving a stated blocker. | Resolve the blocking issue named in status |

AIM may still route to install, upgrade, validate, or deeper help when the state
requires it or the user asks, but those are not replacements for state-first
guidance.

Detailed method concepts, adapter differences, runtime contracts, and reference material stay available behind the document map and workflow docs.

## Key decisions

- The first screen should not require users to understand every AIM concept.
- `Cost Control` is the default lightweight suggestion for ordinary low-risk work.
- The full method remains authoritative in `docs/workflow/agile-iteration-method.md`; `aim.profile.yaml` supplies shared repo-awareness and host-provided instructions remain external environment constraints.
- The lighter front door changes onboarding shape, not AIM role order, gate semantics, or acceptance rules.

## Inputs and outputs

Inputs:
- a user goal
- an existing AIM state
- an install or upgrade need

Outputs:
- one clear next command or document
- optional cost-profile guidance
- links to deeper docs only when needed

## Example-driven start guidance

When recommending `/aim start`, show a realistic example instead of only a
placeholder:

```text
/aim start "EPIC: Improve the onboarding flow so a new homeowner can list a room and understand the next review step"
```

or, for repository-awareness context:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. Keep tone nuanced and empathetic toward both the cats and the future owners."
```

## Progressive disclosure

Do not lead with internal file paths, runtime locations, adapter packaging,
architecture diagrams, or command inventories unless the user asks for that
detail or the current blocker requires it.

Advanced details remain available through `/aim help`, `/aim status`, `/aim
config`, `/aim validate`, and the workflow docs.

## Edge cases

- If an active `.aim/state.json` exists, continue or validate instead of starting a second Epic.
- If the repo is missing AIM files, install before starting.
- If work is high risk, use `Deep` even if the user entered through the lightweight path.

## Debugging

The best check is whether a new user can answer this without reading reference docs:

```text
You are here. Do this next.
```

## Related files

- `README.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/agents/aim.agent.md`
