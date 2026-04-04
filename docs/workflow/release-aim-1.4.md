> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 release and production checklist

## Release summary

AIM 1.4 keeps the established AIM core/runtime model stable and turns Claude Code support into a first-class release outcome.

Main outcomes:
- AIM is still documented as `core + runtime + repo-aware policy + platform adapters`
- `.aim` remains the official repo-local runtime workspace
- `state.json` remains the durable startup and resume checkpoint
- Codex, Copilot, and Claude Code now share one explicit adapter story where parity is possible
- Claude Code bridge and helper layers are documented without weakening the shared ownership model
- this repository now ships a minimal Claude starter layer for real user onboarding
- AIM installation guidance now makes `.github/agents/aim*.agent.md` explicit as shared instruction-layer files while keeping `.github/prompts/` optional Copilot helpers

## Why teams will care immediately

- You get a better product story:
  AIM is easier to position as one operating model across Codex, Copilot, and Claude Code.
- You get Claude support without a forked method:
  `CLAUDE.md`, `.claude/commands/`, and `.claude/agents/` are documented as adapter layers, not as a second AIM contract.
- You get clearer support boundaries:
  Claude helpers are explicitly bounded away from `.aim/state.json`, gate advancement, and acceptance ownership.
- You keep the same trusted runtime model:
  the shared `.aim`, checkpoint, validator, and fallback rules are unchanged.
- You get cleaner selling points:
  the public front door now explains Claude support as part of AIM's value, not as hidden implementation detail.

## Promoted features

### 1) Claude Code as a first-class adapter
- `CLAUDE.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`
- `docs/workflow/agile-iteration-method.md`

### 2) Shared runtime story across three adapters
- `README.md`
- `AGENTS.md`
- `docs/features/aim-1.4-runtime-architecture.md`

### 3) Claude-aware install and quick-start guidance
- `docs/workflow/install-aim-1.4.md`
- `docs/workflow/quick-start-aim-1.4.md`
- `docs/features/aim-1.4-command-surface-and-onboarding.md`
- `.claude/commands/`
- `.claude/agents/`

### 4) Preserved ownership and acceptance boundaries
- `CLAUDE.md`
- `AGENTS.md`
- `docs/features/aim-1.4-repo-aware-runtime-context.md`

## Production readiness checklist

1. Confirm `README.md` presents AIM 1.4 as the current public front door.
2. Confirm `README.md` selling points explicitly include Claude Code support.
3. Confirm `README.md`, `docs/workflow/install-aim-1.4.md`, and `docs/workflow/quick-start-aim-1.4.md` each describe Claude Code as a supported adapter.
4. Confirm `AGENTS.md` and `CLAUDE.md` make `AGENTS.md` canonical and `CLAUDE.md` adapter-specific.
5. Confirm `docs/workflow/agile-iteration-method.md` and `docs/features/aim-1.4-platform-adapters-and-parity.md` document Claude Code without changing AIM core or AIM runtime semantics.
6. Confirm Claude helper boundaries explicitly preserve main-thread ownership of `.aim/state.json`, gates, and acceptance.
7. Confirm `CHANGELOG.md` includes the AIM 1.4 entry.

## Suggested publish text (short)

AIM 1.4 is out.

What is new:
- first-class Claude Code support in the AIM adapter model
- updated install and quick-start guidance for Codex, Copilot, and Claude Code
- explicit Claude bridge/helper layer that keeps `AGENTS.md` canonical
- stronger public positioning for AIM as a cross-environment operating model

## Suggested publish text (promoted)

AIM 1.4 makes AIM easier to explain, adopt, and trust across modern agent environments.

Why this release stands out:
- Claude Code is now part of the supported AIM adapter story, not bolted on afterward
- Codex, Copilot, and Claude Code fit under one shared runtime and ownership model
- the main AIM thread still owns `.aim/state.json`, gate progression, and acceptance everywhere
- the install, quick-start, and public front-door docs now sell AIM as one portable operating model

If your team wants AIM to work and read like a cross-environment product instead of a one-tool workflow, AIM 1.4 is the release to use.
