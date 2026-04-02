> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 1.3

Use this guide when you want the minimum viable AIM 1.3 setup in a repository.

## One shared mental model

AIM 1.3 has four parts:
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
- `.aim/` created automatically when AIM starts if missing

Required for Codex:
- access to the `agile-iteration-method` skill or another compatible AIM runtime adapter

Required for Copilot:
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.github/prompts/start-aim.prompt.md`

Recommended for Copilot:
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.2-to-1.3.prompt.md`

Recommended for Claude Code support:
- `CLAUDE.md`
- `.claude/agents/`
- `.claude/commands/`

Claude Code rule:
- `AGENTS.md` remains the canonical AIM repo contract
- `CLAUDE.md` and `.claude/` files are adapter helpers, not replacements for the shared runtime contract

## What lives where

Shared runtime guidance lives in repo docs:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- AIM 1.3 runtime feature docs

Repo-local working state lives in:
- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

Adapter-specific entrypoints live in:
- Codex skill packaging outside the repo
- Copilot `.github/agents/` and `.github/prompts/` files inside the repo
- Claude Code `CLAUDE.md`, `.claude/agents/`, and `.claude/commands/` inside the repo

## `.aim` commit and ignore guidance

Recommended default for a normal team repository:
- ignore live `.aim/` runtime state
- commit only intentionally curated examples or templates

Recommended default for the official AIM repository:
- ignore live `.aim/` runtime state
- publish the contract in docs instead of treating the live working directory as release material

## Recommended installation flow

### Codex
1. Confirm the AIM skill is available.
2. Confirm the repository AIM docs are present.
3. Start with:
   - `[$agile-iteration-method](...) Start new AIM Loop with "EPIC: ..."`
   - or another compatible AIM runtime entrypoint
4. Confirm the active skill baseline is AIM 1.3 rather than an older AIM variant.

### Copilot
1. Run the install helper:
   - `Install AIM`
   - or `.github/prompts/install-aim.prompt.md`
2. Verify the `aim` agent and prompt files exist.
3. Start with:
   - `/aim start "EPIC: ..."`
   - or `Start working according to AIM`
4. Confirm the packaged `aim` agent and prompts expose the AIM 1.3 runtime contract.

### Claude Code
1. Ensure `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, and `CLAUDE.md` are present.
2. Add `.claude/commands/` and `.claude/agents/` if the repo wants Claude-specific entrypoints or helpers.
3. Start with either:
   - a repository AIM command exposed through `.claude/commands/`
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
- start upgrade guidance with `/aim upgrade 1.2-to-1.3`

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

- `docs/workflow/quick-start-aim-1.3.md`
- `docs/workflow/migrate-aim-1.2-to-1.3.md`
- `docs/workflow/copilot-layer.md`
- `docs/features/aim-1.3-installation-status-and-configuration.md`
