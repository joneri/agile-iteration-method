> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.1 release notes (publish draft)

## Release summary

AIM 1.1 keeps the core method stable and improves adoption speed.

Main outcomes:
- clearer kickoff contract (PO Epic first, TDO Done Increment next)
- stronger Copilot support
- lower friction for daily operation via handoff UI buttons and commands

## Promoted features

### 1) Copilot layer with canonical specs
- `docs/workflow/copilot-layer.md`
- `.github/agents/`
- `.github/prompts/`

### 2) Handoff UI buttons in Copilot
The `aim` agent includes:
- `Approve`
- `Request changes`
- `Replan`
- `Status`
- `Continue`

### 3) Command-driven start and migration
- `Install AIM`
- `Start working according to AIM`
- `/aim start "EPIC: ..."`
- `/migrate-aim-1.0-to-1.1`

### 4) Terminology cleanup
- `docs/features-explanations/` -> `docs/features/`
- `docs/runbooks/` -> `docs/epics/`

## Contributor acknowledgment

AIM 1.1 includes contributor input from:
- [@liamwears](https://github.com/liamwears)

See:
- `CONTRIBUTORS.md`

## Suggested publish text (short)

AIM 1.1 is out.

What is new:
- improved Copilot support with canonical custom-agent and prompt files
- handoff UI buttons to speed up gate flow
- Epic-first kickoff contract (PO defines Epic, TDO defines Done Increment)
- one-command migration path from AIM 1.0

## Suggested publish checklist

1. Confirm `README.md` and `CHANGELOG.md` are updated.
2. Confirm `.github/agents/` and `.github/prompts/` are present.
3. Confirm `CONTRIBUTORS.md` includes new acknowledgments.
4. Tag release as `v1.1.0`.
