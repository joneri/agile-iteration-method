> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Troubleshoot AIM

Use this guide when AIM does not start, resume, validate, or behave consistently across adapters.

## Fast checks

Follow [runtime source routing](adapter-command-contract.md#runtime-source-routing)
before checking files. Inspect the exact action-envelope target first. For native
Story work, use the trusted Story helper's compact status for
`.aim/product-backlog.json`; inspect only its relevant delivery and evidence.
For an explicitly selected legacy workspace, inspect its `state.json`, `epic.md`
and linked increment, review and decision evidence. Root legacy state is not a
fallback for native work.

Then check `aim.profile.yaml`, the relevant canonical contract and the nearest
verification command. Run AIM's validator only from a trusted AIM distribution;
never execute a same-named target-repository script merely because it exists.

## Startup issues

### Symptom

AIM does not start cleanly.

### Expected AIM behavior

- AIM classifies intent and resolves the authoritative runtime before resuming
- Authorized runtime writes create needed state through the trusted helper; help,
  status, Discuss and UI observation do not create `.aim`
- AIM stops and escalates if repo-aware context is contradictory in a trust-affecting way

## Resume issues

### Symptom

AIM starts a new Epic when you expected resume behavior.

### Expected AIM behavior

- native Story continuation resumes its selected delivery and frozen scope
- explicit legacy continuation resumes its incomplete checkpoint
- starting new work requires the corresponding intent and planning authority;
  missing state alone does not authorize a new Epic
- if artifacts contradict the checkpoint, AIM stops and asks instead of guessing

## Increment-scope and file-boundary issues

### Symptom

AIM tries to force one file when the behavior is still small but the structure would be clearer in a few focused files.

### Expected AIM behavior

- small increment means small behavioral scope, not minimal file count
- extra files are justified only when they preserve the approved behavior and create clearer responsibility boundaries
- broad rewrites still require explicit approval

Best reference:
- [AIM modularity and context efficiency](modularity-context-efficiency.md)

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

- only the main AIM thread mutates the selected runtime and records actual owner
  decisions; helper availability never grants acceptance authority
- if bounded parallel capability is unavailable, AIM falls back to sequential execution
- deployment and database migration are not parallel by default

## Install and packaging issues

### Symptom

The repository has some AIM files, but start commands, prompt helpers, or adapter packaging are missing or stale.

### Expected AIM behavior

- `Install AIM` should point to the current required files and optional adapter helpers
- `Upgrade AIM` should be the normal recovery path when AIM files are present but helper surfaces or instruction files became stale
- helper prompts are optional convenience surfaces, not the AIM contract
- Codex, Copilot, and Claude packaging may differ, but the canonical workflow contract stays consistent
- generic root instruction files are not required, created, or modified by AIM

## Best reference docs

- [README.md](../../README.md)
- [Install AIM](install-aim-2.0.md)
- [Quick start AIM](quick-start-aim-2.0.md)
- [Agile iteration method](agile-iteration-method.md)
- [AIM adapter guidance](aim-adapter-guidance.md)
