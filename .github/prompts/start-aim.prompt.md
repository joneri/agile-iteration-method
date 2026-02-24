---
mode: aim
---

Start working according to AIM.

If no Epic is provided yet:
- ask for one line: `EPIC: ...`
- offer Epic-doc-first mode if I prefer to start from `docs/epics/<feature>.md`
- ask for execution mode: `Strict` (default) or `Auto`

If Epic is provided:
- select the `aim` agent flow
- ensure PO owns Epic definition at Gate A
- ensure TDO owns Done Increment spec at Gate B
- ensure canonical role names are used in reporting: `PO`, `TDO`, `Dev`, `Reviewer`
- run `/aim start "EPIC: ..."`
- remind me that approvals are meaningful at Gate A, B, and E
