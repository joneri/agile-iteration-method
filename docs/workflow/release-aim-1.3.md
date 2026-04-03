> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.3 release and production checklist

## Release summary

AIM 1.3 keeps the AIM core loop stable and makes the runtime explicit, inspectable, and portable.

Main outcomes:
- AIM is documented as `core + runtime + repo-aware policy + platform adapters`
- `.aim` is the official repo-local runtime workspace
- `state.json` is the durable startup and resume checkpoint
- Codex and Copilot share one conceptual runtime model where parity is possible
- migration, validation, fallback, and parity behavior are documented explicitly

## Why teams will care immediately

- You get less mystery:
  AIM no longer depends on undocumented runtime behavior.
- You get stronger session continuity:
  `.aim` and `state.json` make active Epic state visible and resumable.
- You get clearer cross-platform behavior:
  Codex and Copilot differences are treated as adapter differences, not hidden method drift.
- You get safer automation:
  controlled parallelism, validation, and fallback behavior are bounded by one shared ownership model.
- You get a practical upgrade path:
  AIM 1.2 to AIM 1.3 migration is documented without rewriting AIM core.

## Promoted features

### 1) Explicit runtime model
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-1.4-runtime-architecture.md`

### 2) Official `.aim` workspace and durable checkpoint
- `docs/features/aim-1.4-runtime-workspace.md`
- `docs/features/aim-1.4-state-transition-model.md`

### 3) Shared startup, resume, and validator behavior
- `docs/features/aim-1.4-bootstrap-and-resume.md`
- `docs/features/aim-1.4-validator-support.md`

### 4) Shared repo-aware policy model
- `docs/features/aim-1.4-repo-aware-runtime-context.md`

### 5) Migration and parity coverage
- `docs/workflow/migrate-aim-1.2-to-1.4.md`
- `docs/features/aim-1.4-migration-support.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`

## Production readiness checklist

1. Confirm `README.md` presents AIM 1.3 as the current public front door.
2. Confirm `README.md` and `docs/workflow/quick-start-aim-1.4.md` each show one preferred start path for Codex and one for Copilot.
3. Confirm `AGENTS.md` and `docs/workflow/agile-iteration-method.md` distinguish retained AIM 1.2 core semantics from AIM 1.3 runtime additions.
4. Confirm `docs/workflow/aim-1.4-doc-map.md` clearly separates public, reference, and internal material.
5. Confirm the official `.aim` workspace contract is documented.
6. Confirm `.aim` commit-ignore guidance is documented for the official AIM repo and normal team repos.
7. Confirm `AGENTS.md` and `docs/workflow/agile-iteration-method.md` both state that hard-gate requirements are conceptual minimums, not mandatory visible section headings.
8. Confirm role-specific interaction rules explicitly override any older generic visible gate-template interpretation.
9. Confirm bootstrap, resume, validator, migration, and parity docs are present and cross-linked.
10. Confirm support boundaries, planned capability labels, and out-of-contract behavior are explicit in adapter docs.
11. Confirm Copilot packaging describes official `.aim` artifacts as authoritative and helper files as secondary.
12. Confirm `CHANGELOG.md` includes the AIM 1.3 entry.

## Suggested publish text (short)

AIM 1.3 is out.

What is new:
- official `.aim` runtime workspace
- durable `state.json` checkpoint for startup and resume
- shared runtime model across Codex and Copilot
- explicit validator, migration, and parity contracts

## Suggested publish text (promoted)

AIM 1.3 turns AIM into a clearer product.

Why this release stands out:
- the AIM core stays stable while runtime behavior becomes explicit
- `.aim` is now official repo-local runtime state instead of adapter-specific magic
- Codex and Copilot share one runtime model where parity is possible, with documented fallback where it is not
- validation, migration, and controlled parallelism are all documented with clear ownership boundaries

If your team wants AIM to be easier to explain, resume, troubleshoot, and adopt across environments, AIM 1.3 is the release to use.
