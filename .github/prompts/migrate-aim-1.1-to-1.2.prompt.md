---
mode: agent
---

Upgrade this repository from AIM 1.1 to AIM 1.2.

Required outcomes:
1. Repository profile is first-class and documented in `AGENTS.md`.
2. Layer order is explicit and consistent everywhere:
   AIM base -> `AGENTS.md` -> `.github/agents/aim*.agent.md`.
3. Execution modes are explicit and visible:
   - `Strict` (default)
   - `Auto` with Epic flag `Auto-approve until Epic complete`
4. Canonical role names are enforced in docs and prompts:
   `PO`, `TDO`, `Dev`, `Reviewer`.
5. Copilot and Codex startup docs use the same repository-driven behavior.
6. No stale AIM 1.1-only wording remains where AIM 1.2 behavior is now expected.

Actions:
1. Update docs and prompt files for AIM 1.2 semantics.
2. Add/adjust migration docs and changelog entries.
3. Return a checklist with changed paths and any follow-up risks.
