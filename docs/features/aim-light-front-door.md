# AIM Light Front Door

## Purpose

Make AIM easier to start without removing the method depth that makes it reliable.

The front door should help a user choose the next action first, not teach the full method first.

## How it works

AIM 1.6 presents three first choices:
- start a new AIM run
- continue or troubleshoot an existing AIM run
- install or upgrade AIM

Detailed method concepts, adapter differences, runtime contracts, and reference material stay available behind the document map and workflow docs.

## Key decisions

- The first screen should not require users to understand every AIM concept.
- `Cost Control` is the default lightweight suggestion for ordinary low-risk work.
- The full method remains authoritative in `AGENTS.md` and `docs/workflow/agile-iteration-method.md`.
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

## Edge cases

- If an active `.aim/state.json` exists, continue or validate instead of starting a second Epic.
- If the repo is missing AIM files, install before starting.
- If work is high risk, use `Deep` even if the user entered through the lightweight path.

## Debugging

The best check is whether a new user can answer this without reading reference docs:

```text
Do I start, continue, or install?
```

## Related files

- `README.md`
- `docs/workflow/quick-start-aim-1.6.md`
- `docs/workflow/aim-1.6-doc-map.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/agents/aim.agent.md`
