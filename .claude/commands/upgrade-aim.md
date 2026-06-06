# Upgrade AIM

Use this command when AIM files, adapter helpers, or packaged prompts were updated and the current repository should begin using the new AIM 2.0 instruction surface.

Explain:
- upgrading AIM refreshes installed AIM-owned files and helper surfaces for this repository
- `calibrate-repo` refreshes repo-awareness after the upgrade
- an existing Claude session may still need a new command run or a fresh session before changed instructions are applied consistently

Upgrade checklist:
- confirm canonical AIM workflow docs are still present
- verify `.claude/commands/` and `.claude/agents/` files are current for the selected footprint
- verify optional Copilot or Codex helper surfaces only when the user relies on them
- report whether the repo is `ready`, `partially_ready`, or `needs_calibration`
- end with the exact next action:
  - `calibrate-repo` when package refresh succeeded
  - `continue-aim` when an active Epic should resume in a fresh session
  - `start-aim` when no active Epic exists

Make clear that upgrade does not silently rewrite active `.aim/` runtime state.