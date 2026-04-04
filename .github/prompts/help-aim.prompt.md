---
mode: aim
---

Show AIM 1.4 help for this repository.

Explain:
1. the quickest supported way to begin:
   - preferred Copilot path: `/aim start "EPIC: ..."`
   - secondary natural-language path: `Start working according to AIM`
2. the difference between:
   - Epic
   - Done Increment
   - status
   - config
3. the main commands:
   - `/aim continue`
   - `/aim status`
   - `/aim validate`
   - `/aim config`
   - `/aim upgrade 1.2-to-1.4`
4. where AIM runtime state lives:
   - shared AIM 1.4 runtime docs in the repository
   - repo-local working state in `.aim/`
5. how installation layers differ:
   - required shared AIM files: `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, `.github/agents/aim*.agent.md`
   - optional Copilot prompt helpers: `.github/prompts/`
   - optional Claude adapter bridge: `CLAUDE.md` plus `.claude/`
6. how `Strict` and `Auto` differ

If no active Epic exists, end by telling me the exact next start command to run.
