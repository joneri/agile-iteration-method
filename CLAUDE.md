# Claude Code bridge for AIM

This file is the Claude Code instruction bridge for AIM.

`AGENTS.md` remains the canonical repository AIM contract.
This file maps that contract onto Claude Code's instruction and command surface without redefining AIM core, AIM runtime, repo-aware policy, gates, ownership, or acceptance.

## Recommended layer order

1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`
4. repository `CLAUDE.md`
5. repository `.claude/agents/*`
6. repository `.claude/commands/*`

Later Claude-specific layers may refine execution for Claude Code, but they must not silently contradict the shared AIM runtime contract.

Important:
- `.github/agents/aim*.agent.md` remain part of the shared AIM instruction layer.
- Claude-specific files extend the Claude adapter surface on top of that layer.
- `.github/prompts/` remain optional Copilot-style command helpers rather than part of the Claude adapter contract.

## Claude Code adapter rules

- Treat `AGENTS.md` as the source of truth for AIM behavior in this repository.
- Use `docs/workflow/agile-iteration-method.md` for the method and runtime explanation.
- Treat `.aim/` as the official AIM runtime workspace.
- Treat `.aim/state.json` as the authoritative runtime checkpoint.
- Keep the main AIM thread as the only owner of:
  - `.aim/state.json`
  - gate progression
  - increment acceptance
  - Epic acceptance or completion

## Claude helper boundaries

Claude Code helper agents or subagents may assist with bounded work only:
- analysis
- discovery
- verification
- option generation

They must not:
- own `.aim/state.json`
- advance gates
- redefine acceptance semantics
- replace `AGENTS.md` as the repo contract

## Practical Claude Code start

Before starting AIM in Claude Code, ensure these files are present:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `CLAUDE.md`

Recommended Claude Code helper packaging:
- `.claude/commands/`
- `.claude/agents/`

This repository now ships a minimal Claude starter layer:
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`
- `.claude/agents/aim.md`

Start with either:
- a repository AIM command exposed through `.claude/commands/`
- or an explicit start message such as:

```text
EPIC: <desired outcome>
Mode: Strict
```

or:

```text
EPIC: <desired outcome>
Mode: Auto
```

If command-file invocation differs in the current Claude Code environment, use the explicit `EPIC: ...` fallback and keep the shipped command files as the discoverability layer.
