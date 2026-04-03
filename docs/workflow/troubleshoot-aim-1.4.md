> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Troubleshoot AIM 1.4

Use this guide when AIM 1.4 does not start, resume, validate, or behave consistently across adapters.

## Fast checks

Check these first:
1. `.aim/state.json`
2. `.aim/epic.md`
3. the newest files in `.aim/increments/`, `.aim/reviews/`, and `.aim/decisions/`
4. `AGENTS.md`
5. `docs/workflow/agile-iteration-method.md`

## Startup issues

### Symptom
AIM does not start cleanly.

### Check
- confirm the repo root is correct
- confirm `AGENTS.md` exists
- confirm repo-aware AIM instructions are readable

### Expected AIM 1.4 behavior
- AIM loads repo-aware context first
- AIM creates `.aim` if it is missing
- AIM stops and escalates if repo-aware context is contradictory in a trust-affecting way

## Resume issues

### Symptom
AIM starts a new Epic when you expected resume behavior.

### Check
- inspect `.aim/state.json`
- verify whether it points to an incomplete Epic
- verify that `current_role`, `gate`, and increment state match the newest runtime artifacts

### Expected AIM 1.4 behavior
- if `.aim/state.json` describes an incomplete Epic, AIM resumes from that checkpoint
- if there is no active incomplete checkpoint, AIM starts a new Epic at Gate A
- if artifacts contradict the checkpoint, AIM stops and asks instead of guessing

## `.aim` workspace issues

### Symptom
`.aim` exists but the runtime state is unclear.

### Check
- confirm required artifacts exist:
  - `.aim/epic.md`
  - `.aim/state.json`
  - `.aim/increments/`
  - `.aim/decisions/`
  - `.aim/reviews/`
- confirm helper artifacts are not pretending to be authoritative state

### Expected AIM 1.4 behavior
- `state.json` is the durable runtime checkpoint
- helper artifacts may exist, but must remain secondary
- only the main AIM thread owns shared runtime state

## Validator issues

### Symptom
Validation reports `healthy`, `recoverable`, `blocked`, or `contradictory`.

### Check
- compare validator output with `.aim/state.json`
- compare the active increment with the newest increment, review, and decision artifacts
- compare current repo-aware instructions with the normalized runtime expectations

### Expected AIM 1.4 behavior
- `healthy` means the runtime checkpoint is coherent enough to trust for continuation
- `recoverable` means the main AIM thread can repair the gap without trust loss
- `blocked` means explicit user input is required
- `contradictory` means authoritative artifacts disagree and escalation is required

## Parity and adapter issues

### Symptom
Codex and Copilot appear to behave differently.

### Check
- compare `docs/workflow/agile-iteration-method.md`
- compare `docs/workflow/copilot-layer.md`
- compare `docs/features/aim-1.4-platform-adapters-and-parity.md`

### Expected AIM 1.4 behavior
- shared behavior must remain shared
- adapter differences must be documented explicitly
- unsupported capability must preserve policy intent and fall back safely

## Parallel and fallback issues

### Symptom
Parallel capability is missing or inconsistent.

### Check
- confirm whether the adapter actually exposes bounded parallel capability
- confirm repo-aware policy allows parallel work
- confirm no parallel path is writing `.aim/state.json` or advancing gates

### Expected AIM 1.4 behavior
- only the main AIM thread owns `state.json`, gate progression, and acceptance
- if bounded parallel capability is unavailable, AIM falls back to sequential execution
- deployment and database migration are not parallel by default

## Migration issues

### Symptom
An AIM 1.2 repo does not migrate cleanly to AIM 1.4.

### Check
- compare the repo against `docs/workflow/migrate-aim-1.2-to-1.4.md`
- confirm legacy artifacts are classified as tolerated, migrated, archived, or removed
- confirm `.aim/epic.md` and `.aim/state.json` are treated as authoritative after migration

### Expected AIM 1.4 behavior
- migration reuses the shared runtime model
- legacy helper artifacts may remain temporarily
- contradictory legacy state must be escalated instead of guessed through

## Best reference docs

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-1.4-runtime-workspace.md`
- `docs/features/aim-1.4-bootstrap-and-resume.md`
- `docs/features/aim-1.4-validator-support.md`
- `docs/features/aim-1.4-migration-support.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`
