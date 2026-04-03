> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 document map

Use this guide to understand which AIM 1.4 documents are public front-door docs, which are reference specifications, and which are internal planning material.

## Public product docs

Use these first:
- `README.md`
- `docs/workflow/release-aim-1.4.md`
- `docs/workflow/quick-start-aim-1.4.md`
- `docs/workflow/install-aim-1.4.md`
- `docs/workflow/troubleshoot-aim-1.4.md`
- `docs/workflow/migrate-aim-1.2-to-1.4.md`
- `docs/workflow/example-aim-1.4-reference-run.md`
- `docs/workflow/aim-1.4-interaction-examples.md`

These docs answer:
- what AIM is
- how to start
- how to resume
- how to inspect `.aim`
- how to troubleshoot
- how to upgrade

## Reference specification docs

Use these when deeper behavior or contracts matter:
- `AGENTS.md`
- `CLAUDE.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/`
- `docs/workflow/copilot-layer.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/commands/`
- `.claude/agents/`

These docs define:
- operational rules
- runtime contracts
- adapter boundaries
- validation and fallback behavior
- role interaction behavior
- adapter packaging and entrypoint wiring
- Claude Code bridge and helper-layer boundaries
- shipped Claude starter surfaces for real user onboarding

## Internal planning and historical material

Use these when working on AIM itself rather than just using AIM:
- `docs/epics/`
- `.aim/`

These docs are useful for maintainers, but they are not the recommended first stop for a new user.

## Recommended production reading order

For a new user:
1. `README.md`
2. `docs/workflow/release-aim-1.4.md`
3. `docs/workflow/quick-start-aim-1.4.md`
4. `docs/workflow/install-aim-1.4.md`
5. `docs/workflow/troubleshoot-aim-1.4.md`

For a maintainer or adapter implementer:
1. `AGENTS.md`
2. `docs/workflow/agile-iteration-method.md`
3. `CLAUDE.md` when working on Claude Code support
4. relevant files in `docs/features/`
5. `docs/workflow/copilot-layer.md`
