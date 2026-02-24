> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Migrate AIM 1.1 to AIM 1.2

Use this when a repository already follows AIM 1.1 but needs AIM 1.2 execution semantics.

## Copy-paste prompt

```text
Upgrade this repository from AIM 1.1 to AIM 1.2.

Required outcomes:
1) Repository profile is first-class and documented in `AGENTS.md`.
2) Layer order is explicit and consistent everywhere:
   AIM base -> `AGENTS.md` -> `.github/agents/aim*.agent.md`.
3) Execution modes are explicit and visible:
   - Strict (default)
   - Auto with Epic flag: Auto-approve until Epic complete
4) Canonical role names are enforced in docs/prompts:
   PO, TDO, Dev, Reviewer.
5) Copilot and Codex startup docs use the same repository-driven behavior.
6) No stale AIM 1.1-only wording remains where AIM 1.2 behavior is expected.

Actions:
1) Update docs, prompt files, and role guidance for AIM 1.2.
2) Add migration notes to changelog.
3) Return checklist of changed files and follow-up risks.
```

## Copilot prompt-file alternative

If your repo includes prompt files, run:
- `/migrate-aim-1.1-to-1.2`

Source file:
- `.github/prompts/migrate-aim-1.1-to-1.2.prompt.md`
