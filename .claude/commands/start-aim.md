# Start AIM

Use this command to start a new AIM loop in Claude Code for this repository.
Map it to `/aim start "EPIC: ..."` from
`docs/workflow/adapter-command-contract.md`.

In Claude, AIM is **skill-led** through `.claude/skills/aim/SKILL.md`. These
`.claude/commands/` entrypoints remain supported compatibility routes.
`.claude/agents/` helpers are internal and are not the primary surface. The
canonical cross-adapter entry model is
`docs/workflow/adapter-entry-model.md`.
Command intent and fallback semantics come from
`docs/workflow/adapter-command-contract.md`.

Before starting:
- load `docs/workflow/agile-iteration-method.md`
- load `.aim/state.json` when present
- load `aim.profile.yaml` when present
- apply compatible Personal hints from `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- load `docs/workflow/repo-awareness.md` when repo-awareness or adapter loading needs clarification
- preserve `.aim` as the official AIM runtime workspace

Expected input:
- `EPIC: <desired outcome>`
- `PORTFOLIO` with `Mode: Auto` to preview and authorize one immutable AIM UI Backlog snapshot
- `Mode: Strict` or `Mode: Auto`
- `Cost profile: Standard`, `Cost profile: Cost Control`, or `Cost profile: Deep` when resource use matters

Command behavior:
- for `PORTFOLIO` plus Auto, preview the ordered Backlog, require one bounded
  user mandate, and then run included Epics sequentially through the complete
  AIM loop; after Gate E, separately record mandate-authorized Epic closure,
  complete the active candidate, and activate the next snapshot candidate
  without another user message; checkpoint via trusted
  `scripts/aim_portfolio_run.py` and pause on scope, trust, validation, safety,
  concurrency, user-stop, or stale-state risk. Gate E accepts the Increment only
- if `.aim/state.json` describes an incomplete Epic, resume it instead of silently starting a parallel Epic
- resume its persisted cost profile; when no incomplete Epic exists, select a
  fresh cost profile and never inherit one from `epic_complete`
- use `stateSchemaVersion: "1.0"`; normalize supported legacy aliases read-only
  and stop on conflicts or unsupported versions
- keep model/reasoning effort independent from AIM cost profile
- otherwise initialize a new Epic at Gate A
- keep canonical role order:
  - `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- keep canonical workflow docs authoritative
- keep Claude helper files secondary to canonical workflow docs and `aim.profile.yaml`
- keep the main AIM thread as the only owner of `.aim/state.json`, gate progression, and acceptance
- map repo-awareness verification Epics to `docs/workflow/repo-awareness-calibration.md`

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

Whole-Backlog form:

```text
/aim start "PORTFOLIO" mode:auto
```
