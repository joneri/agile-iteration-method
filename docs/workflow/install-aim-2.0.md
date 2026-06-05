> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 2.0

Use this guide when repository setup is still missing and you want a current AIM 2.0 installation path.

This guide is about repository setup.
Use [Quick start AIM 2.0](quick-start-aim-2.0.md) for the first run after setup.

## Choose the installation footprint

- Personal AIM:
  - no committed AIM files are required by default
  - repo profile lives at `~/.aim/profiles/<repo-fingerprint>/profile.yaml`
  - working state stays local
- Team AIM:
  - share a small root `aim.profile.yaml`
  - working state stays local by default
  - teammates reuse commands, locality hints, risk zones, and validation paths
- Full embedded AIM:
  - commit the AIM contract into the repository only when the repo owner intentionally wants AIM inside the repo

All three footprints are current AIM 2.0 choices.

## Minimum setup for full embedded AIM

Required in the repository:

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.aim/` created automatically when AIM starts if missing

Optional Copilot prompt helpers:

- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`

Recommended for Claude Code support:

- `CLAUDE.md`
- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`

## Adapter packaging

### Codex

Use the shipped skill when you want the `/aim` command surface and Codex bootstrap help.

Required for `/aim` in Codex:

- `adapters/codex/agile-iteration-method/SKILL.md`

If the local skill is missing or stale, install the repo-bundled skill before relying on `/aim` command routing:

```sh
mkdir -p ~/.codex/skills/agile-iteration-method
cp -R adapters/codex/agile-iteration-method/. ~/.codex/skills/agile-iteration-method/
```

Copy the whole directory, not just `SKILL.md`.

### Copilot

1. Verify the required `.github/agents/aim*.agent.md` files exist.
2. Add `.github/prompts/` when you want packaged Copilot prompt entrypoints.
3. Start with `/aim start "EPIC: ..."` or `Start working according to AIM`.

### Claude Code

1. Ensure `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, and `CLAUDE.md` are present.
2. Confirm the shipped Claude starter files exist.
3. Start with the shipped Claude starter command or the explicit `EPIC: <desired outcome>` fallback.

## First-run checks

After setup, a user should be able to:

- start AIM
- resume AIM
- inspect status with `/aim status`
- inspect config with `/aim config`
- validate runtime state with `/aim validate`
- read help with `/aim help`
- select runtime depth with `/aim cost standard|control|deep`

## If setup is incomplete

- if the user starts AIM in recognizable language, treat it as a start intent
- if a helper prompt is missing, explain the equivalent manual command
- if `.aim` is missing, create it before continuing
- if repo policy is contradictory, stop and escalate instead of guessing

## Next documents

- [Quick start AIM 2.0](quick-start-aim-2.0.md)
- [Troubleshoot AIM 2.0](troubleshoot-aim-2.0.md)
- [AIM 2.0 low-footprint adoption](aim-2-low-footprint-adoption.md)
- [AIM adapter guidance](aim-adapter-guidance.md)