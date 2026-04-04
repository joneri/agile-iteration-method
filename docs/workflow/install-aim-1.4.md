> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 1.4

Use this guide when you want the minimum viable AIM 1.4 setup in a repository.

## One shared mental model

AIM 1.4 has four parts:
- AIM core:
  - the role loop and gate semantics
- AIM runtime:
  - `.aim`, startup, resume, validation, and state transitions
- repo-aware policy:
  - repository-specific verification, deployment, migration, reviewer, and approval rules
- platform adapter:
  - Codex, Copilot, or Claude Code entrypoints and packaging

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
- `.github/prompts/upgrade-aim-1.2-to-1.4.prompt.md`

Recommended for Claude Code support:
- `CLAUDE.md`
- `.claude/agents/aim.md`
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`

Claude Code rule:
- `AGENTS.md` remains the canonical AIM repo contract
- `.github/agents/aim*.agent.md` remain part of the shared AIM instruction layer
- `CLAUDE.md` and `.claude/` files are adapter helpers, not replacements for the shared runtime contract

## What lives where

Shared runtime guidance lives in repo docs:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- AIM 1.4 runtime feature docs

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
- Claude Code `CLAUDE.md`, `.claude/agents/`, and `.claude/commands/` inside the repo

Recommended user-facing adapter choice:
- Codex:
  - use the AIM skill when you want the `/aim` command surface
- Copilot:
  - use the packaged `aim` agent and add prompt helpers when you want Copilot-style command entrypoints
- Claude Code:
  - use `CLAUDE.md` plus the shipped starter files under `.claude/`

## Codex product model

- The repository is the source of truth for repo-aware AIM.
- The Codex skill is a bootstrap and convenience layer.
- `/aim` is the normal Codex start path when the skill is available.
- A prepared repo can still run AIM in Codex without the skill, but that path should use explicit AIM start language instead of `/aim`.
- The skill stays valuable even in a prepared repo because it gives a cleaner launcher plus help, status, config, validate, and upgrade entrypoints.

## `.aim` commit and ignore guidance

Recommended default for a normal team repository:
- ignore live `.aim/` runtime state
- commit only intentionally curated examples or templates

Recommended default for the official AIM repository:
- ignore live `.aim/` runtime state
- publish the contract in docs instead of treating the live working directory as release material

## Recommended installation flow

### Codex
1. Install or enable the AIM skill if you want `/aim`.
2. Confirm the repository AIM docs and `.github/agents/aim*.agent.md` are present.
3. Start with:
   - `/aim start "EPIC: ..."`
4. If the skill is unavailable but the repo already carries the full AIM contract, start with:
   - `EPIC: <desired outcome>`
   - `Mode: Strict` or `Mode: Auto`
5. Confirm the repo remains the source of truth and the skill acts as the launcher rather than hidden authority.

### Copilot
1. Run the install helper:
   - `Install AIM`
   - or `.github/prompts/install-aim.prompt.md`
2. Verify the required `.github/agents/aim*.agent.md` files exist.
3. Add `.github/prompts/` if you want packaged Copilot prompt entrypoints.
4. Start with:
   - `/aim start "EPIC: ..."`
   - or `Start working according to AIM`
5. Confirm the packaged `aim` agent exposes the AIM 1.4 runtime contract and the prompt files remain optional helpers.

### Claude Code
1. Ensure `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, and `CLAUDE.md` are present.
2. Confirm the shipped Claude starter files exist:
   - `.claude/commands/start-aim.md`
   - `.claude/commands/install-aim.md`
   - `.claude/commands/continue-aim.md`
   - `.claude/agents/aim.md`
3. Start with either:
   - the shipped Claude starter command under `.claude/commands/start-aim.md`
   - or an explicit start prompt:
     - `EPIC: <desired outcome>`
     - `Mode: Strict` or `Mode: Auto`
4. Confirm the Claude-specific files point back to the shared AIM runtime contract instead of redefining gates, ownership, or acceptance.

## First-run checks

After installation, a user should be able to:
- start AIM
- resume AIM
- inspect status with `/aim status`
- inspect config with `/aim config`
- validate runtime state with `/aim validate`
- read help with `/aim help`
- start upgrade guidance with `/aim upgrade 1.2-to-1.4`

## Runtime status and configuration

`/aim status` should answer:
- what Epic is active
- which Done Increment is active
- which role is current
- which mode is active
- which gate is current or last passed
- which adapter is active
- whether controlled parallelism is available or enabled

`/aim config` should explain:
- what AIM core requires
- which repo-aware rules are active
- what the current runtime checkpoint says
- which adapter limits apply

## If installation is imperfect

Friendly fallback rule:
- if the user starts AIM in recognizable language, treat it as a start intent
- if a helper prompt is missing, explain the equivalent manual command
- if `.aim` is missing, create it before continuing
- if repo policy is contradictory, stop and escalate instead of guessing

## Next documents

- `docs/workflow/quick-start-aim-1.4.md`
- `docs/workflow/migrate-aim-1.2-to-1.4.md`
- `docs/workflow/copilot-layer.md`
- `docs/features/aim-1.4-installation-status-and-configuration.md`
