# Start AIM

Use this command to start a new AIM loop in Claude Code for this repository.

Before starting:
- load `AGENTS.md`
- load `.github/agents/aim*.agent.md` when present as part of the shared AIM instruction layer
- load `CLAUDE.md`
- load `docs/workflow/agile-iteration-method.md`
- preserve `.aim` as the official AIM runtime workspace

Expected input:
- `EPIC: <desired outcome>`
- `Mode: Strict` or `Mode: Auto`

Command behavior:
- if `.aim/state.json` describes an incomplete Epic, resume it instead of silently starting a parallel Epic
- otherwise initialize a new Epic at Gate A
- keep canonical role order:
  - `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- keep `AGENTS.md` canonical
- keep `.github/agents/aim*.agent.md` as shared repository instruction-layer input when present
- keep the main AIM thread as the only owner of `.aim/state.json`, gate progression, and acceptance

Safe fallback:
- if command-file routing is unavailable in the current Claude Code environment, use the explicit start prompt:

```text
EPIC: <desired outcome>
Mode: Strict
```

or:

```text
EPIC: <desired outcome>
Mode: Auto
```
