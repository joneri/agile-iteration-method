---
mode: aim
---

Start AIM 1.6 in this repository.

If no Epic is provided yet:
- ask for one line: `EPIC: ...`
- default to `Mode: Strict`
- suggest `Cost profile: Cost Control` for ordinary low-risk work
- mention that `Deep` is available for trust, data, deployment, migration, security, or API risk
- offer Epic-doc-first mode only if I mention an Epic doc or ask for it

If Epic is provided:
- select the `aim` agent flow
- preserve the AIM 1.6 runtime contract from `AGENTS.md` and `docs/workflow/agile-iteration-method.md`
- ensure PO owns Epic definition at Gate A
- ensure TDO owns Done Increment spec at Gate B
- ensure canonical role names are used in reporting: `PO`, `TDO`, `Dev`, `Reviewer`
- apply `Standard` if no cost profile is provided, and suggest `Cost Control` when the work is ordinary and low risk
- run `/aim start "EPIC: ..."`
- remind me that approvals are meaningful at Gate A, B, and E
