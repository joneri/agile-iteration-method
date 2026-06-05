> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Troubleshoot AIM 2.0

Use this guide when AIM does not start, resume, validate, or behave consistently across adapters.

## Fast checks

Check these first:
1. `.aim/state.json`
2. `.aim/epic.md`
3. the newest files in `.aim/increments/`, `.aim/reviews/`, and `.aim/decisions/`
4. `AGENTS.md`
5. `docs/workflow/agile-iteration-method.md`
6. `docs/features/aim-modularity-context-efficiency.md` when the issue is about file boundaries or increment size
7. `scripts/validate_aim_runtime.py .`

## Startup issues

### Symptom

AIM does not start cleanly.

### Expected AIM behavior

- AIM loads repo-aware context first
- AIM creates `.aim` if it is missing
- AIM stops and escalates if repo-aware context is contradictory in a trust-affecting way

## Resume issues

### Symptom

AIM starts a new Epic when you expected resume behavior.

### Expected AIM behavior

- if `.aim/state.json` describes an incomplete Epic, AIM resumes from that checkpoint
- if there is no active incomplete checkpoint, AIM starts a new Epic at Gate A
- if artifacts contradict the checkpoint, AIM stops and asks instead of guessing

## Increment-scope and file-boundary issues

### Symptom

AIM tries to force one file when the behavior is still small but the structure would be clearer in a few focused files.

### Expected AIM behavior

- small increment means small behavioral scope, not minimal file count
- extra files are justified only when they preserve the approved behavior and create clearer responsibility boundaries
- broad rewrites still require explicit approval

Best reference:
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

## Adapter and parity issues

### Symptom

Codex, Copilot, and Claude Code appear to behave differently.

### Expected AIM behavior

- shared behavior must remain shared
- adapter differences must be documented explicitly
- unsupported capability must preserve policy intent and fall back safely

## Parallel and fallback issues

### Symptom

Parallel capability is missing or inconsistent.

### Expected AIM behavior

- only the main AIM thread owns `state.json`, gate progression, and acceptance
- if bounded parallel capability is unavailable, AIM falls back to sequential execution
- deployment and database migration are not parallel by default

## Install and packaging issues

### Symptom

The repository has some AIM files, but start commands, prompt helpers, or adapter packaging are missing or stale.

### Expected AIM behavior

- `Install AIM 2.0` should point to the current required files and optional adapter helpers
- helper prompts are optional convenience surfaces, not the AIM contract
- Codex, Copilot, and Claude packaging may differ, but the repository contract stays consistent

## Best reference docs

- [README.md](../../README.md)
- [Install AIM 2.0](install-aim-2.0.md)
- [Quick start AIM 2.0](quick-start-aim-2.0.md)
- [Agile iteration method](agile-iteration-method.md)
- [AIM adapter guidance](aim-adapter-guidance.md)