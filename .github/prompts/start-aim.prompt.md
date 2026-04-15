---
mode: aim
---

Start AIM 1.6 in this repository.

If no Epic is provided yet:
- ask for one line: `EPIC: ...`
- offer Epic-doc-first mode if I prefer to start from `docs/epics/<feature>.md`
- ask for execution mode: `Strict` (default) or `Auto`
- ask for cost profile when resource use matters: `Standard` (default), `Cost Control`, or `Deep`

If Epic is provided:
- select the `aim` agent flow
- preserve the AIM 1.6 runtime contract from `AGENTS.md` and `docs/workflow/agile-iteration-method.md`
- ensure PO owns Epic definition at Gate A
- ensure TDO owns Done Increment spec at Gate B
- ensure canonical role names are used in reporting: `PO`, `TDO`, `Dev`, `Reviewer`
- apply `Standard` cost profile unless I choose `Cost Control` or `Deep`
- run `/aim start "EPIC: ..."`
- remind me that approvals are meaningful at Gate A, B, and E
