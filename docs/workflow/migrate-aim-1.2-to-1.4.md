> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Migrate AIM 1.2 to AIM 1.4

Use this when a repository already follows AIM 1.2 and needs the AIM 1.4 runtime contract.

## Copy-paste prompt

```text
Upgrade this repository from AIM 1.2 to AIM 1.4.

Required outcomes:
1) AIM core, AIM runtime, repo-aware policy, and platform adapters are documented as separate concerns.
2) `.aim` is treated as the official repo-local AIM runtime workspace.
3) `state.json` is the durable runtime checkpoint for startup, resume, and gate tracking.
4) Migration scenarios are clear for:
   - repos with no `.aim`
   - repos with informal `.aim`
   - Codex-only repos
   - Copilot-layer repos
5) Legacy artifacts are classified as tolerated, migrated, archived, or removed.
6) Startup, resume, and validator behavior remain consistent with AIM 1.4 runtime docs.
7) No stale AIM 1.2-only runtime wording remains where AIM 1.4 behavior is expected.

Actions:
1) Update repository docs and agent guidance to AIM 1.4 runtime terminology.
2) Add or normalize the official `.aim` workspace contract.
3) Keep `AGENTS.md` and `.github/agents/aim*.agent.md` aligned to the same shared runtime model.
4) Document the upgrade checklist and legacy artifact policy.
5) Return a checklist of changed files, migration assumptions, and follow-up risks.
```

## Migration checklist

- confirm the repository profile still loads through `AGENTS.md` and `.github/agents/aim*.agent.md`
- create `.aim` if it does not exist
- normalize active Epic and state data into `.aim/epic.md` and `.aim/state.json`
- review legacy helper artifacts and classify them explicitly
- update workflow docs so startup, resume, validation, and ownership rules match AIM 1.4

## Legacy artifact policy

- tolerated temporarily:
  - `.aim/plan.md`
  - adapter helper files that do not override the official runtime contract
- migrated:
  - active Epic state into `.aim/epic.md`
  - runtime checkpoint state into `.aim/state.json`
- archived:
  - stale logs and analysis artifacts once they are no longer part of the active working set
- removed or replaced:
  - legacy files that try to own current gate, role, or acceptance state outside the official AIM 1.4 checkpoint

## Notes

- AIM 1.4 keeps AIM core semantics from AIM 1.2.
- The migration is runtime-focused, not a rewrite of the role loop.
- If legacy runtime artifacts contradict the official checkpoint or current repo policy, escalate instead of guessing.

## Command-surface changes to verify

After migration, the repository should document and expose these AIM 1.4 commands or their explicit adapter-equivalent entrypoints:
- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim upgrade 1.2-to-1.4`

Migration check:
- if a command is conceptually supported but not packaged in one adapter, document the fallback clearly instead of implying silent support

Related install and operator docs:
- `docs/workflow/install-aim-1.4.md`
- `docs/workflow/quick-start-aim-1.4.md`
- `docs/features/aim-1.4-installation-status-and-configuration.md`
