> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 document map

Use this guide to understand which AIM 1.4 documents are public front-door docs, which are reference specifications and which are internal planning material.

## Choose your path

Use this route first instead of guessing from file names:

- Evaluate AIM:
  - [README.md](../../README.md)
  - [Quick start AIM 1.4](quick-start-aim-1.4.md)
  - [AIM 1.4 interaction examples](aim-1.4-interaction-examples.md)
- Install AIM in a repository:
  - [README.md](../../README.md)
  - [Install AIM 1.4](install-aim-1.4.md)
  - [Quick start AIM 1.4](quick-start-aim-1.4.md)
  - [Troubleshoot AIM 1.4](troubleshoot-aim-1.4.md)
- Upgrade an older AIM repository:
  - [Migrate AIM 1.2 to AIM 1.4](migrate-aim-1.2-to-1.4.md)
  - [Quick start AIM 1.4](quick-start-aim-1.4.md)
  - [Troubleshoot AIM 1.4](troubleshoot-aim-1.4.md)
- Implement or adapt AIM itself:
  - [AGENTS.md](../../AGENTS.md)
  - [Agile iteration method](agile-iteration-method.md)
  - [AIM adapter guidance](aim-adapter-guidance.md)

If the goal is only to use AIM in a repo, do not start with `AGENTS.md` or `aim-adapter-guidance.md`.

## Public product docs

Use these first:
- [README.md](../../README.md)
- [Install AIM 1.4](install-aim-1.4.md)
- [Quick start AIM 1.4](quick-start-aim-1.4.md)
- [AIM 1.4 document map](aim-1.4-doc-map.md)
- [Troubleshoot AIM 1.4](troubleshoot-aim-1.4.md)
- [Migrate AIM 1.2 to AIM 1.4](migrate-aim-1.2-to-1.4.md)
- [Release AIM 1.4](release-aim-1.4.md)
- [Example AIM 1.4 reference run](example-aim-1.4-reference-run.md)
- [AIM 1.4 interaction examples](aim-1.4-interaction-examples.md)

These docs answer:
- what AIM is
- how to start
- what the Codex skill is and when it helps
- when the repo alone is enough
- how to resume
- how to inspect `.aim`
- how to troubleshoot
- how to upgrade

## Reference specification docs

Use these when deeper behavior or contracts matter:
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)
- [Agile iteration method](agile-iteration-method.md)
- [AIM adapter guidance](aim-adapter-guidance.md)
- [docs/features/](../features/README.md)
- [Copilot layer](copilot-layer.md)
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

These docs are useful for maintainers but they are not the recommended first stop for a new user.

## Recommended production reading order

For a new user:
1. [README.md](../../README.md)
2. [Install AIM 1.4](install-aim-1.4.md)
3. [Quick start AIM 1.4](quick-start-aim-1.4.md)
4. [AIM 1.4 document map](aim-1.4-doc-map.md)
5. [Troubleshoot AIM 1.4](troubleshoot-aim-1.4.md)

For a maintainer or adapter implementer:
1. [AGENTS.md](../../AGENTS.md)
2. [Agile iteration method](agile-iteration-method.md)
3. [AIM adapter guidance](aim-adapter-guidance.md)
4. [CLAUDE.md](../../CLAUDE.md) when working on Claude Code support
5. relevant files in [docs/features/](../features/README.md)
6. [Copilot layer](copilot-layer.md)
