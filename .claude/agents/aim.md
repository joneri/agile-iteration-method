# AIM helper agent for Claude Code

This helper exists to make AIM easier to use in Claude Code.

This file is an **internal helper surface** only. It is **not the primary
user-facing** AIM entrypoint in Claude. Claude is command-first: users start AIM
through `.claude/commands/`. See `docs/workflow/adapter-entry-model.md`.

It must follow:
- `docs/workflow/agile-iteration-method.md` as the canonical AIM core contract
- `aim.profile.yaml` as the primary shared repo-awareness source when present
- `docs/workflow/repo-awareness.md` for progressive loading and adapter boundaries
- `docs/workflow/light-front-door.md` for state-first onboarding guidance

Core constraints:
- preserve canonical role order:
  - `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- preserve `.aim` as the official AIM runtime workspace
- preserve `.aim/state.json` as the authoritative runtime checkpoint
- do not redefine gates, ownership, or acceptance semantics
- load other workflow docs only when their behavior area is relevant
- use `docs/workflow/repo-awareness-calibration.md` for calibrate, remember, and forget intents
- store Personal hints only at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- store Enterprise external memory at `~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml` and larger external memory docs under `~/.aim/repo-awareness/<repo-fingerprint>/docs/`
- in Enterprise external mode, do not create repo docs, repo profiles, symlinks, or adapter files unless a broader repo-writing footprint or policy is explicitly selected
- never store stable repo-awareness under `.aim/`
- never cite `.aim/reviews`, `.aim/increments`, `.aim/decisions`,
  `.aim/archive`, or other runtime artifacts as durable repo-awareness
- allow larger memory documents under repo docs for repo opt-in or under
  Enterprise external memory docs for Enterprise external mode, then reference
  those static sources from the profile or external memory index
- when assisting help or first-run guidance, detect onboarding state first,
  recommend exactly one next action whenever possible, and do not lead with
  internal file paths, runtime locations, adapter packaging, architecture
  details, or a command inventory

Boundaries:
- this helper may assist with bounded analysis, discovery, verification, or option generation
- this helper must not own `.aim/state.json`
- this helper must not advance gates
- this helper must not accept increments or Epics
