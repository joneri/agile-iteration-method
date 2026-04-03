> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 reference run

Use this document as the concrete reference example for how AIM 1.4 works in this repository.

## Goal

Show one coherent AIM 1.4 flow that covers:
- start
- resume
- inspect
- adapter-aware behavior in Codex and Copilot

This is an example of the accepted AIM 1.4 contracts in practice.
It does not define a second runtime model.

## Reference scenario

Repository:
- this repository

Epic example:
- `AIM 1.4 unified runtime, shared state, and cross-platform parity`

Runtime assumptions:
- `AGENTS.md` is the repo profile entrypoint
- `.aim/state.json` is the authoritative runtime checkpoint
- Codex and Copilot share the same conceptual startup and resume flow where parity is possible

## Step 1: Start in Codex

1. Open the repo in VS Code.
2. Open Codex chat for the workspace.
3. Invoke `[$agile-iteration-method](...)` and provide the Epic candidate directly.
4. Make mode explicit, for example `Mode: Strict`.

Expected behavior:
- AIM detects repo root
- AIM loads repo-aware context
- AIM creates `.aim` if missing
- AIM initializes or resumes the active Epic
- AIM enters the role sequence and reports Gate A

Inspect after start:
- `.aim/epic.md`
- `.aim/state.json`

## Step 2: Move from Epic approval to increment flow

After the Epic is approved at Gate A and the next Done Increment is approved at Gate B:
- the main AIM thread proceeds through `Dev`, `Reviewer`, and post-review `TDO`
- soft gates do not require extra approval unless escalation conditions are met
- `.aim/state.json` reflects the active gate and role

Visible interaction expectation:
- `Dev` reports implementation and verification progress
- `Reviewer` reports findings and readiness
- post-review `TDO` turns the increment into a demo, test, and feedback checkpoint and explains whether it should be accepted or adjusted
- `PO` then makes the Epic-level decision to continue, close, or separate new scope

Inspect during progress:
- `.aim/increments/`
- `.aim/reviews/`
- `.aim/decisions/`

## Step 3: Resume safely

Interrupt the session after a gate has been recorded.

Expected behavior on restart:
- AIM reads `.aim/state.json`
- if the Epic is incomplete, AIM resumes from the recorded checkpoint
- AIM does not silently start a new Epic

If the checkpoint is contradictory:
- AIM stops and asks instead of guessing

## Step 4: Compare Codex and Copilot

Codex reference:
- uses the AIM skill together with the repo instructions and the available Codex runtime/tool surface
- may expose bounded parallel capability where runtime support exists

Copilot reference:
- uses `.github/agents/aim*.agent.md` and `.github/prompts/` as interface packaging
- uses the `aim` agent plus `/aim start` and `/aim continue` as entry helpers

Shared behavior:
- same conceptual bootstrap order
- same `.aim` workspace contract
- same resume semantics
- same ownership of `state.json`, gates, and acceptance

Adapter differences:
- commands, UI handoffs, and tool surfaces can differ
- current packaging gaps must be treated as documented limitations, not hidden parity

## Step 5: Inspect runtime state

Best files to inspect:
- `AGENTS.md`
- `.aim/state.json`
- `.aim/epic.md`
- the newest file in `.aim/increments/`
- the newest file in `.aim/reviews/`
- the newest file in `.aim/decisions/`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-1.4-runtime-workspace.md`
- `docs/features/aim-1.4-bootstrap-and-resume.md`
- `docs/features/aim-1.4-validator-support.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`

What “good” looks like:
- one active authoritative checkpoint
- gate and role align with increment, review, and decision artifacts
- helper files, if present, remain clearly secondary to the official runtime artifacts
- Codex and Copilot docs describe the same conceptual flow
- the visible checkpoints also make clear who is speaking, what decision is needed now, and what happens next

## Step 6: Handle failure cases

If `.aim` is missing:
- AIM creates it before continuing

If repo-aware policy is contradictory:
- AIM escalates instead of guessing

If validator result is `recoverable`:
- the main AIM thread may repair the issue without trust loss

If adapter capability is missing:
- AIM preserves the intended runtime contract and falls back safely

If bounded parallel capability is missing:
- AIM runs sequentially without changing ownership rules

## Related documents

- `README.md`
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/aim-1.4-interaction-examples.md`
- `docs/workflow/copilot-layer.md`
- `docs/workflow/troubleshoot-aim-1.4.md`
- `docs/features/aim-1.4-runtime-workspace.md`
- `docs/features/aim-1.4-bootstrap-and-resume.md`
- `docs/features/aim-1.4-validator-support.md`
- `docs/features/aim-1.4-migration-support.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`
