# Install AIM

Use this command to orient a Claude Code user to the minimum viable AIM setup in this repository.

Explain:
- `AGENTS.md` is the canonical AIM repo contract
- `CLAUDE.md` is the Claude Code bridge layer
- `docs/workflow/agile-iteration-method.md` explains the shared AIM method and runtime
- `.claude/commands/` and `.claude/agents/` are helper surfaces, not replacements for the shared runtime contract

Installation checklist:
- confirm `AGENTS.md` is present
- confirm `CLAUDE.md` is present
- confirm the main workflow doc is present
- explain how to start AIM with the shipped Claude starter command or the explicit `EPIC: ...` fallback
- explain that `.aim/` will be created automatically on first valid start if missing
