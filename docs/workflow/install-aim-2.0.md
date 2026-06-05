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

## Installation boundary model

Before copying files, classify the target surface.

Use [AIM 2.0 repository surface classification](../features/aim-2-repository-surface-classification.md) as the operational boundary model.

Installer actions must follow these defaults:

| Surface class | Default action |
| --- | --- |
| Static AIM product docs and adapter packages | may be copied into an AIM-owned package path selected by the user |
| Repo-aware instruction files | may be created only when absent and explicitly requested; otherwise produce a merge plan |
| Runtime state | never install as product; AIM creates `.aim/` at runtime |
| Team profile | create or update only by explicit Team AIM choice |
| Personal profile | store outside the repository by default |
| Target repo policy files | never overwrite |
| Internal build-memory | do not install by default |

Installation safety matters more than convenience.
If a file is both useful and collision-prone, treat it as a template or merge target, not as a normal copy target.

### Collision-prone root files

These files require explicit handling:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `aim.profile.yaml`
- `.gitignore`

Rules:

- inspect before writing
- create only when absent and requested
- modify only through a reviewed merge or patch
- never blind overwrite
- never store active Epic, gate, role, review, or acceptance state in repo profiles or instruction files

For `.gitignore`, suggest this fragment instead of replacing the target file:

```gitignore
/.aim
```

## Minimum setup for full embedded AIM

Required in the repository:

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.aim/` created automatically when AIM starts if missing

Important:

- the listed instruction files are required for a full embedded AIM repo, but they are not safe blind-overwrite targets in an existing repository
- `.aim/` is runtime state, not an install payload
- `CONTRIBUTING.md` is not part of default AIM installation for target repositories

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
