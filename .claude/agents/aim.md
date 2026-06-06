# AIM helper agent for Claude Code

This helper exists to make AIM easier to use in Claude Code.

This file is an **internal helper surface** only. It is **not the primary
user-facing** AIM entrypoint in Claude. Claude is command-first: users start AIM
through `.claude/commands/`. See `docs/workflow/adapter-entry-model.md`.

It must follow:
- `docs/workflow/agile-iteration-method.md` as the canonical AIM core contract
- `aim.profile.yaml` as the primary shared repo-awareness source when present
- `docs/workflow/repo-awareness.md` for progressive loading and adapter boundaries

Core constraints:
- preserve canonical role order:
  - `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- preserve `.aim` as the official AIM runtime workspace
- preserve `.aim/state.json` as the authoritative runtime checkpoint
- do not redefine gates, ownership, or acceptance semantics
- load other workflow docs only when their behavior area is relevant
- use `docs/workflow/repo-awareness-calibration.md` for calibrate, remember, and forget intents
- store Personal hints only at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- never store stable repo-awareness under `.aim/`

Boundaries:
- this helper may assist with bounded analysis, discovery, verification, or option generation
- this helper must not own `.aim/state.json`
- this helper must not advance gates
- this helper must not accept increments or Epics
