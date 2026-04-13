> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.5 reference run

Use this document as the concrete reference example for how AIM 1.5 works in this repository.

## Goal

Show one coherent AIM 1.5 flow that covers:
- start
- resume
- inspect
- adapter-aware behavior in Codex, Copilot, and Claude Code
- the 1.5 rule that a small increment may use several focused files without expanding behavioral scope

## Reference scenario

Repository:
- this repository

Epic example:
- `Make AIM 1.5 feel finished in the public onboarding path without redesigning the method`

Runtime assumptions:
- `AGENTS.md` is the repo profile entrypoint
- `.aim/state.json` is the authoritative runtime checkpoint
- adapters share the same conceptual startup and resume flow where parity is possible

## Step 1: Start

1. Open the repo in the chosen adapter.
2. Start with `/aim start "EPIC: ..."` when the adapter exposes it.
3. Otherwise use explicit AIM intent:
   - `EPIC: <desired outcome>`
   - `Mode: Strict`

Expected behavior:
- AIM detects repo root
- AIM loads repo-aware context
- AIM creates `.aim` if missing
- AIM initializes or resumes the active Epic
- AIM enters the role sequence and reports Gate A

## Step 2: Approve one increment

After Gate A and Gate B are approved:
- the main AIM thread proceeds through `Dev`, `Reviewer`, and post-review `TDO`
- soft gates do not require extra approval unless escalation conditions are met
- `.aim/state.json` reflects the active gate and role

AIM 1.5 expectation:
- the increment stays small by behavior
- the implementation may use several focused files if that reduces context load and preserves the approved behavior

## Step 3: Resume safely

Interrupt the session after a gate has been recorded.

Expected behavior on restart:
- AIM reads `.aim/state.json`
- if the Epic is incomplete, AIM resumes from the recorded checkpoint
- AIM does not silently start a new Epic

## Step 4: Compare adapters

Shared behavior:
- same conceptual bootstrap order
- same `.aim` workspace contract
- same resume semantics
- same ownership of `state.json`, gates, and acceptance

Adapter differences:
- commands, UI handoffs, and tool surfaces can differ
- packaging gaps must be treated as documented limitations, not hidden parity

## Step 5: Inspect runtime state

Best files to inspect:
- `AGENTS.md`
- `.aim/state.json`
- `.aim/epic.md`
- the newest file in `.aim/increments/`
- the newest file in `.aim/reviews/`
- the newest file in `.aim/decisions/`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-modularity-context-efficiency.md`
- `docs/workflow/aim-adapter-guidance.md`

What good looks like:
- one active authoritative checkpoint
- gate and role align with increment, review, and decision artifacts
- helper files remain clearly secondary to the official runtime artifacts
- the visible checkpoints make clear who is speaking, what decision is needed now, and what happens next

## Related documents

- [README.md](../../README.md)
- [Quick start AIM 1.5](quick-start-aim-1.5.md)
- [AIM 1.5 interaction examples](aim-1.5-interaction-examples.md)
- [Troubleshoot AIM 1.5](troubleshoot-aim-1.5.md)
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
