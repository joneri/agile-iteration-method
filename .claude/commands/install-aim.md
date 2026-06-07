# Install AIM

Use this command to orient a Claude Code user to the minimum viable AIM setup in this repository.

First check whether AIM was already installed, including AIM 1.x-era files,
older helper prompts, command files, adapter packages, or an existing `.aim/`
runtime. If so, recommend `upgrade-aim` before start, continue, or calibration.
Explain that upgrade refreshes installed AIM-owned surfaces through the reviewed
installer plan and preserves active `.aim/` runtime state.

Explain:
- `docs/workflow/agile-iteration-method.md` is the canonical AIM core contract
- `aim.profile.yaml` is the primary shared repo-awareness source when Team repo-awareness is selected
- `.claude/commands/` and `.claude/agents/` are native Claude entrypoints and optional secondary policy surfaces

Installation checklist:
- confirm the main workflow doc is present
- confirm `.claude/agents/aim.md` or the desired `.claude/commands/` entrypoint is present
- mention `upgrade-aim` when AIM was already installed, when older AIM 1.x-era files are present, or when helper or instruction files changed
- explain how to start AIM with the shipped Claude starter command or the explicit `EPIC: ...` fallback
- explain that `Cost profile: Cost Control` is available for low-risk work and `Cost profile: Deep` for high-risk work
- explain that `.aim/` will be created automatically on first valid start if missing
- report repo-awareness as `ready`, `partially_ready`, or `needs_calibration`
- direct incomplete setups to the shipped `calibrate-repo` command
- keep Personal hints at `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
