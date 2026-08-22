---
mode: aim
---

Start AIM 2.0 in this repository.

Before reading major docs, check `.aim/state.json`.
If an incomplete Epic exists, resume that checkpoint instead of rebuilding context or starting over.
If `aim.profile.yaml` exists, read it next as the shared baseline.
If Personal AIM hints exist at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`, apply compatible hints after the shared profile.
Use profile facts to choose locality, commands, short authoritative docs, risk zones, freshness triggers, and context to avoid before broader docs.

If no Epic is provided yet:
- ask for one line: `EPIC: ...`, or offer `/aim start "PORTFOLIO" mode:auto`
  when the user wants one approved run over the visible AIM UI Backlog
- default to `Mode: Strict`
- suggest `Cost profile: Cost Control` for ordinary low-risk work
- mention that `Deep` is available for trust, data, deployment, migration, security, or API risk
- use `.aim/epic.md` for active Epic state when AIM starts or resumes

If Epic is provided:
- select the `aim` agent flow
- preserve the AIM runtime contract from `docs/workflow/agile-iteration-method.md`
- load Personal and Team profiles before broader docs when present
- load only the additional context needed for the current state, command, cost profile, and risk
- report whether the profile was reused, which facts were reused, which locality was selected, which broader docs or scans were avoided, and why any expansion was needed
- ensure PO owns Epic definition at Gate A
- ensure TDO owns Done Increment spec at Gate B
- ensure canonical role names are used in reporting: `PO`, `TDO`, `Dev`, `Reviewer`
- apply `Standard` if no cost profile is provided, and suggest `Cost Control` when the work is ordinary and low risk
- resume an incomplete Epic with its persisted cost profile; for a genuinely
  new Epic select cost afresh and never inherit an `epic_complete` profile
- read canonical `stateSchemaVersion: "1.0"`; use a read-only in-memory
  normalization for documented legacy state and stop on conflicts or
  unsupported versions
- keep supplier model/reasoning effort independent from AIM cost profile
- run `/aim start "EPIC: ..."`
- remind me that approvals are meaningful at Gate A, B, and E

If `PORTFOLIO` with `mode:auto` is provided, preview an immutable ordered
Backlog snapshot and require one bounded user mandate. Then keep the main AIM
thread as sole orchestrator, run one included Epic at a time through the full
role/Gate loop, and checkpoint only through trusted
`scripts/aim_portfolio_run.py`. Record delegated approvals with mandate
provenance. Pause on scope expansion, unsafe effects, ambiguous evidence,
failed validation, concurrency conflict, user stop/change, or malformed/stale
state; `/aim continue` must revalidate before resuming.
