---
mode: aim
---

Start AIM 2.0 in this repository.

Before reading major docs, check `.aim/state.json`.
If an incomplete Epic exists, resume that checkpoint instead of rebuilding context or starting over.
If a Personal AIM local profile exists, read it next.
If `aim.profile.yaml` exists, read it after the personal profile as the Team AIM shared baseline.
Use profile facts to choose locality, commands, short authoritative docs, risk zones, freshness triggers, and context to avoid before broader docs.

If no Epic is provided yet:
- ask for one line: `EPIC: ...`
- default to `Mode: Strict`
- suggest `Cost profile: Cost Control` for ordinary low-risk work
- mention that `Deep` is available for trust, data, deployment, migration, security, or API risk
- use `.aim/epic.md` for active Epic state when AIM starts or resumes

If Epic is provided:
- select the `aim` agent flow
- preserve the AIM runtime contract from `AGENTS.md` and `docs/workflow/agile-iteration-method.md`
- load Personal and Team profiles before broader docs when present
- load only the additional context needed for the current state, command, cost profile, and risk
- report whether the profile was reused, which facts were reused, which locality was selected, which broader docs or scans were avoided, and why any expansion was needed
- ensure PO owns Epic definition at Gate A
- ensure TDO owns Done Increment spec at Gate B
- ensure canonical role names are used in reporting: `PO`, `TDO`, `Dev`, `Reviewer`
- apply `Standard` if no cost profile is provided, and suggest `Cost Control` when the work is ordinary and low risk
- run `/aim start "EPIC: ..."`
- remind me that approvals are meaningful at Gate A, B, and E
