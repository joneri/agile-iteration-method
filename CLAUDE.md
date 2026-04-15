# Claude Code bridge for AIM

This file is the Claude Code instruction bridge for AIM.

`AGENTS.md` remains the canonical repository AIM contract.
This file maps that contract onto Claude Code's instruction and command surface. It does not redefine AIM core, AIM runtime, repo-aware policy, gates, ownership or acceptance.

## Recommended layer order

1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`
4. repository `CLAUDE.md`
5. repository `.claude/agents/*`
6. repository `.claude/commands/*`

Later Claude-specific layers may refine execution for Claude Code, but they must not contradict the shared AIM runtime contract.

Keep in mind:
- `.github/agents/aim*.agent.md` remain part of the shared AIM instruction layer.
- Claude-specific files extend the Claude adapter surface on top of that layer.
- `.github/prompts/` remain optional Copilot-style command helpers rather than part of the Claude adapter contract.

## Claude Code adapter rules

- Treat `AGENTS.md` as the source of truth for AIM behavior in this repository.
- Use `docs/workflow/agile-iteration-method.md` for the method and runtime explanation.
- Treat `.aim/` as the official AIM runtime workspace.
- Treat `.aim/state.json` as the authoritative runtime checkpoint.
- Treat small increments as small behavioral scope, not minimal file count.
- Treat cost profile as runtime depth, not approval semantics.
- Use `Cost profile: Cost Control` for low-risk reversible work and escalate to `Standard` or `Deep` when risk appears.
- Prefer cohesive files and clear module boundaries when they reduce future context cost and preserve the approved behavior.
- Do not create context hogs or arbitrary file splits just to satisfy a superficial diff-size goal.
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

## Starting AIM in Claude Code

Before starting AIM in Claude Code, ensure these files are present:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `CLAUDE.md`

Recommended Claude Code helper packaging:
- `.claude/commands/`
- `.claude/agents/`

This repository now ships a small Claude starter layer:
- `.claude/commands/start-aim.md`
- `.claude/commands/install-aim.md`
- `.claude/commands/continue-aim.md`
- `.claude/commands/upgrade-aim-1.5-to-1.6.md`
- `.claude/agents/aim.md`

Start with either:
- a repository AIM command exposed through `.claude/commands/`
- or an explicit start message such as:

```text
EPIC: <desired outcome>
Mode: Strict
Cost profile: Cost Control
```

or:

```text
EPIC: <desired outcome>
Mode: Auto
Cost profile: Standard
```

If command-file invocation differs in the current Claude Code environment, use the explicit `EPIC: ...` fallback and keep the shipped command files as the discoverability layer.
