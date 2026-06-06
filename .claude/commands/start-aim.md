# Start AIM

Use this command to start a new AIM loop in Claude Code for this repository.

Before starting:
- load `docs/workflow/agile-iteration-method.md`
- load `.aim/state.json` when present
- load `aim.profile.yaml` when present
- load `docs/workflow/repo-awareness.md` when repo-awareness or adapter loading needs clarification
- preserve `.aim` as the official AIM runtime workspace

Expected input:
- `EPIC: <desired outcome>`
- `Mode: Strict` or `Mode: Auto`
- `Cost profile: Standard`, `Cost profile: Cost Control`, or `Cost profile: Deep` when resource use matters

Command behavior:
- if `.aim/state.json` describes an incomplete Epic, resume it instead of silently starting a parallel Epic
- otherwise initialize a new Epic at Gate A
- keep canonical role order:
  - `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- keep canonical workflow docs authoritative
- keep Claude helper files secondary to canonical workflow docs and `aim.profile.yaml`
- keep the main AIM thread as the only owner of `.aim/state.json`, gate progression, and acceptance

Safe fallback:
- if command-file routing is unavailable in the current Claude Code environment, use the explicit start prompt:

```text
EPIC: <desired outcome>
Mode: Strict
Cost profile: Cost Control
```

or:

```text
EPIC: <desired outcome>
Mode: Auto
Cost profile: Standard
```
