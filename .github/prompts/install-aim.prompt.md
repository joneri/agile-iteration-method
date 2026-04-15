---
mode: agent
---

Install AIM 1.6 in this workspace and add the optional Copilot prompt layer when needed.

Actions:
1. Verify these files exist and create missing ones from templates:
   - `AGENTS.md`
   - `docs/workflow/agile-iteration-method.md`
   - `.github/agents/aim.agent.md`
   - `.github/agents/aim-planner.agent.md`
   - `.github/agents/aim-builder.agent.md`
   - `.github/agents/aim-reviewer.agent.md`
2. Verify optional Copilot prompt files exist when packaged command entrypoints are desired:
   - `.github/prompts/install-aim.prompt.md`
   - `.github/prompts/start-aim.prompt.md`
   - `.github/prompts/help-aim.prompt.md`
   - `.github/prompts/upgrade-aim-1.5-to-1.6.prompt.md`
3. Confirm supporting AIM docs are present:
   - `docs/workflow/install-aim-1.6.md`
   - `docs/workflow/copilot-layer.md`
   - `docs/workflow/migrate-aim-1.5-to-1.6.md`
4. Return a short checklist and tell me the next command to run.

After setup, suggest:
- `/aim start "EPIC: ..."`
- `/aim help`
- `/aim status`
- `/aim validate`
- `/aim config`
- `/aim cost standard|control|deep`
- `/aim upgrade 1.5-to-1.6`

Make clear that `.github/agents/aim*.agent.md` are required AIM instruction-layer files and `.github/prompts/` are optional Copilot prompt helpers.
