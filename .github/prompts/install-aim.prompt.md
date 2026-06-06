---
mode: agent
---

Install AIM 2.0 in this workspace and add the optional Copilot prompt layer when needed.

Actions:
1. Verify these files exist and create missing ones from templates:
   - `docs/workflow/agile-iteration-method.md`
   - `aim.profile.yaml` when Team repo-awareness is selected
   - `docs/workflow/agile-iteration-method.md`
   - `.github/agents/aim.agent.md`
   - `.github/agents/aim-planner.agent.md`
   - `.github/agents/aim-builder.agent.md`
   - `.github/agents/aim-reviewer.agent.md`
2. Verify optional Copilot prompt files exist when packaged command entrypoints are desired:
   - `.github/prompts/install-aim.prompt.md`
   - `.github/prompts/start-aim.prompt.md`
   - `.github/prompts/help-aim.prompt.md`
   - `.github/prompts/upgrade-aim.prompt.md`
3. Confirm supporting AIM docs are present:
   - `docs/workflow/install-aim-2.0.md`
   - `docs/workflow/quick-start-aim-2.0.md`
   - `docs/workflow/troubleshoot-aim-2.0.md`
   - `docs/workflow/copilot-layer.md`
4. Return a short checklist and tell me the next command to run.

After setup, suggest:
- `/aim start "EPIC: ..."`
- `/aim help`
- `/aim upgrade`
- `/aim status`
- `/aim validate`
- `/aim config`
- `/aim cost standard|control|deep`

Make clear that `.github/agents/aim*.agent.md` are required AIM instruction-layer files and `.github/prompts/` are optional Copilot prompt helpers.
