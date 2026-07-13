---
mode: agent
---

Upgrade AIM 2.0 in this workspace after AIM instruction files, adapter helpers, or packaged prompts changed.

Actions:
1. Verify whether AIM-owned instruction, adapter, and helper files are present but stale for the selected footprint.
2. Refresh the installed AIM package surface when needed:
   - `.github/agents/aim.agent.md`
   - `.github/agents/aim-po.agent.md`
   - `.github/agents/aim-tdo.agent.md`
   - `.github/agents/aim-dev.agent.md`
   - `.github/agents/aim-reviewer.agent.md`
   - `.codex/agents/aim-*.toml`
   - `.claude/agents/aim-*.md`
   - `aim.roles.yaml`
   - optional `.github/prompts/*.prompt.md`
   - optional adapter helper files for the active platform
3. Re-check supporting AIM docs:
   - `docs/workflow/install-aim-2.0.md`
   - `docs/workflow/quick-start-aim-2.0.md`
   - `docs/workflow/troubleshoot-aim-2.0.md`
4. Tell me whether a new session, agent re-selection, or local skill reinstall is required before new instructions take effect.
5. End with the exact next command to run:
   - `/aim calibrate-repo`
   - `/aim continue`
   - `/aim start "EPIC: ..."`

Make clear that upgrading AIM is different from continuing an Epic:
- upgrade refreshes installed AIM surfaces
- calibration refreshes repo-awareness
- a new chat or adapter session may still be required before changed instructions are loaded
