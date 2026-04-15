> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.

# AIM adapter guidance

This document collects adapter-specific AIM guidance that should not live in the canonical `AGENTS.md` master instruction file.

`AGENTS.md` remains the repository contract for AIM behavior.
This file explains how supported adapters expose that contract without redefining AIM core, runtime ownership, gates, role order, or acceptance.

## Purpose

Keep adapter guidance easy to inspect without making `AGENTS.md` carry every platform detail.

Use this file when changing:
- adapter entrypoints
- optional helper file structure
- adapter parity labels
- Codex, Copilot, or Claude Code capability notes
- fallback behavior for adapter-specific tools

## Canonical boundary

Adapter layers may improve UX and discoverability, but they must preserve:
- `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- hard-gate meaning at Gate A, Gate B, and Gate E
- Gate C and Gate D as soft gates
- `.aim/state.json` ownership by the main AIM thread
- repo-aware policy interpretation from `AGENTS.md`
- sequential fallback when controlled parallelism is unavailable

If adapter guidance conflicts with `AGENTS.md`, escalate instead of guessing.

## Optional adapter layers

Copilot layer:
- documented in `docs/workflow/copilot-layer.md`
- uses `.github/agents/aim*.agent.md` as both shared AIM instruction-layer files and native Copilot custom-agent files
- uses `.github/prompts/` for optional Copilot-style prompt helpers

Claude Code layer:
- uses `CLAUDE.md` as the Claude Code bridge
- may add `.claude/commands/` for AIM command entrypoints
- may add `.claude/agents/` for AIM-aligned Claude helpers

Codex layer:
- uses repository instructions plus the available Codex tool surface
- may expose bounded subagent capability where runtime support exists
- treats `/aim`, when available, as a launcher surface rather than the source of method authority

## Quick start phrases

These phrases are valid adapter entrypoint hints when the matching layer supports them:
- `Install AIM`
- `Start working according to AIM`
- `/aim start "EPIC: ..."`
- `/aim upgrade 1.5-to-1.6`
- `Starta en AIM-loop med denna EPIC: ...`

Transport shortcuts and command surfaces are adapter UX.
They do not define the AIM checkpoint contract.

## Optional adapter file structure

Copilot prompt helpers:
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.5-to-1.6.prompt.md`

Claude Code:
- `CLAUDE.md`
- `.claude/commands/`
- `.claude/agents/`

Installation boundary:
- `.github/agents/aim*.agent.md` are part of the AIM repository instruction layer, not Copilot-only decoration.
- `.github/prompts/` are optional Copilot-style prompt helpers, not the canonical AIM contract.
- `CLAUDE.md` bridges canonical AIM behavior into Claude Code; it does not replace `AGENTS.md`.

## Parity classification

Use these labels when comparing adapter behavior:
- `shared`
  - same conceptual behavior and same runtime contract across supported adapters
- `shared_with_adapter_differences`
  - same runtime contract, but different entrypoints, tools, or interface mechanics
- `codex_only`
  - currently documented only for the Codex adapter
- `copilot_only`
  - currently documented only for the Copilot adapter
- `claude_code_only`
  - currently documented only for the Claude Code adapter
- `planned`
  - intentionally not yet treated as a supported shared capability

## Adapter rules

Codex:
- uses repository instructions plus the available Codex tool surface
- may expose bounded subagent capability where runtime support exists
- may expose adapter-specific tools such as MCP-backed browser automation

Copilot:
- uses `.github/agents/aim*.agent.md` as both shared instruction-layer input and native Copilot agent packaging
- uses `.github/prompts/` as optional Copilot command-entry helpers
- may differ in command routing, handoff UI, and prompt-file availability
- must still preserve the shared runtime contract and repo-aware policy interpretation

Claude Code:
- uses `AGENTS.md` as the canonical repository contract and `CLAUDE.md` as the Claude bridge layer
- may expose repository-defined entrypoints through `.claude/commands/` and helper agents through `.claude/agents/`
- may use bounded Claude helpers for analysis, discovery, verification, or option generation only
- must still preserve the shared runtime contract and repo-aware policy interpretation

Fallback rule:
- if a capability is not available in one adapter, the adapter must preserve the intended policy, report the limitation, and fall back safely instead of silently redefining the method
- regardless of parity level, only the main AIM thread may own `.aim/state.json`, gate progression, or acceptance decisions

## Related files

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/copilot-layer.md`
- `CLAUDE.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/`
