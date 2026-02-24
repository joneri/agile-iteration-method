---
mode: agent
---

Install AIM in this workspace using the optional Copilot layer.

Actions:
1. Verify these files exist and create missing ones from templates:
   - `.github/agents/aim.agent.md`
   - `.github/agents/aim-planner.agent.md`
   - `.github/agents/aim-builder.agent.md`
   - `.github/agents/aim-reviewer.agent.md`
2. Verify prompt files exist:
   - `.github/prompts/install-aim.prompt.md`
   - `.github/prompts/start-aim.prompt.md`
   - `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`
   - `.github/prompts/migrate-aim-1.1-to-1.2.prompt.md`
3. Confirm AIM docs are present:
   - `AGENTS.md`
   - `docs/workflow/agile-iteration-method.md`
   - `docs/workflow/copilot-layer.md`
   - `docs/workflow/migrate-aim-1.0-to-1.1.md`
   - `docs/workflow/migrate-aim-1.1-to-1.2.md`
4. Return a short checklist and tell me the next command to run.

After setup, suggest:
- `/start-aim`
- `/aim start "EPIC: ..."`
- `/migrate-aim-1.0-to-1.1`
- `/migrate-aim-1.1-to-1.2`
