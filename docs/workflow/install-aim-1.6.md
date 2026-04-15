> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 1.6

Use this guide for the minimum viable AIM 1.6 setup in a repository.

This guide is about repository setup.
Use [Quick start AIM 1.6](quick-start-aim-1.6.md) for the first Epic once the files are in place.
Use [AIM 1.6 document map](aim-1.6-doc-map.md) if you need the broader front-door reading path.

## What is new in 1.6

AIM 1.6 keeps the accepted AIM core and runtime model from 1.4.
The main public change is that AIM becomes budget-aware:
- `Standard` is normal AIM with progressive context loading
- `Cost Control` keeps gates and ownership intact while reducing runtime depth
- `Deep` is available when higher risk justifies broader inspection
- a small Done Increment means small behavioral scope, not minimal file count
- focused files are allowed when they keep responsibilities clearer, avoid context hogs, and make future changes cheaper
- adapter guidance and onboarding now make cost profile selection visible to users

## AIM still has four parts

AIM 1.6 still uses these four parts:
- AIM core:
  - the role loop and gate semantics
- AIM runtime:
  - `.aim`, startup, resume, validation and state transitions
- repo-aware policy:
  - repository-specific verification, deployment, migration, reviewer and approval rules
- platform adapter:
  - Codex, Copilot or Claude Code entrypoints and packaging

`.aim/` is repo-local runtime state.
It is created on first valid AIM start or resume if it does not already exist.

## Minimum viable setup

Required in the repository:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.aim/` created automatically when AIM starts if missing

Required for `/aim` in Codex:
- the `agile-iteration-method` skill installed and enabled

Repo-aware Codex without the skill:
- the repo can still operate as AIM in Codex when the required AIM files are present and the user starts with explicit AIM intent in plain language

Optional Copilot prompt helpers:
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.5-to-1.6.prompt.md`

Recommended for Claude Code support:
- `CLAUDE.md`
- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`
- `.claude/commands/upgrade-aim-1.5-to-1.6.md`

Claude Code rule:
- `AGENTS.md` remains the canonical AIM repo contract
- `.github/agents/aim*.agent.md` remain part of the shared AIM instruction layer
- `CLAUDE.md` and `.claude/` files are adapter helpers, not replacements for the shared runtime contract

## What lives where

Shared runtime guidance lives in repo docs:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-cost-control-mode.md`
- `docs/features/aim-modularity-context-efficiency.md`
- AIM 1.6 public workflow docs

Repo-local working state lives in:
- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

Adapter-specific entrypoints live in:
- Codex skill packaging outside the repo
- repository `.github/agents/aim*.agent.md` as shared AIM instruction-layer files
- Copilot `.github/prompts/` files as optional Copilot entry helpers
- Claude Code `CLAUDE.md`, `.claude/agents/` and `.claude/commands/` inside the repo

## Adapter choice

- Codex:
  - use the AIM skill when you want the `/aim` command surface
- Copilot:
  - use the packaged `aim` agent and add prompt helpers when you want Copilot-style command entrypoints
- Claude Code:
  - use `CLAUDE.md` plus the shipped starter files under `.claude/`

## Install flow

### Codex
1. Install or enable the AIM skill if you want `/aim`.
2. Confirm the repository AIM docs and `.github/agents/aim*.agent.md` are present.
3. Start with `/aim start "EPIC: ..."`.
4. If the skill is unavailable but the repo already carries the full AIM contract, start with `EPIC: <desired outcome>` and `Mode: Strict` or `Mode: Auto`.
5. Confirm the repo remains the source of truth and the skill acts as the launcher rather than hidden authority.

### Copilot
1. Run the install helper: `Install AIM` or `.github/prompts/install-aim.prompt.md`.
2. Verify the required `.github/agents/aim*.agent.md` files exist.
3. Add `.github/prompts/` if you want packaged Copilot prompt entrypoints.
4. Start with `/aim start "EPIC: ..."` or `Start working according to AIM`.
5. Confirm the packaged `aim` agent exposes the AIM 1.6 runtime contract and the prompt files remain optional helpers.

### Claude Code
1. Ensure `AGENTS.md`, `docs/workflow/agile-iteration-method.md` and `CLAUDE.md` are present.
2. Confirm the shipped Claude starter files exist.
3. Start with the shipped Claude starter command or the explicit `EPIC: <desired outcome>` fallback.
4. Confirm the Claude-specific files point back to the shared AIM runtime contract instead of redefining gates, ownership or acceptance.

After the files and adapter packaging are in place, continue with [Quick start AIM 1.6](quick-start-aim-1.6.md) for the first run.

## First-run checks

After installation, a user should be able to:
- start AIM
- resume AIM
- inspect status with `/aim status`
- inspect config with `/aim config`
- validate runtime state with `/aim validate`
- read help with `/aim help`
- select runtime depth with `/aim cost standard|control|deep`
- start upgrade guidance with `/aim upgrade 1.5-to-1.6`

Claude Code parity note:
- when repository command-file routing is available, the packaged Claude upgrade helper should expose the same `1.5-to-1.6` upgrade path explicitly

## If setup is incomplete

Fallback rules:
- if the user starts AIM in recognizable language, treat it as a start intent
- if a helper prompt is missing, explain the equivalent manual command
- if `.aim` is missing, create it before continuing
- if repo policy is contradictory, stop and escalate instead of guessing

## Next documents

- [Quick start AIM 1.6](quick-start-aim-1.6.md)
- [AIM 1.6 document map](aim-1.6-doc-map.md)
- [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)
- [Migrate AIM 1.5 to AIM 1.6](migrate-aim-1.5-to-1.6.md)
