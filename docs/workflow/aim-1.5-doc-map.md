> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.5 document map

Use this guide to understand which AIM 1.5 documents are public front-door docs, which are reference specifications and which are internal planning material.

## Choose your path

Use this route first instead of guessing from file names:

- Evaluate AIM:
  - [README.md](../../README.md)
  - [Quick start AIM 1.5](quick-start-aim-1.5.md)
  - [AIM 1.5 interaction examples](aim-1.5-interaction-examples.md)
- Install AIM in a repository:
  - [README.md](../../README.md)
  - [Install AIM 1.5](install-aim-1.5.md)
  - [Quick start AIM 1.5](quick-start-aim-1.5.md)
  - [Troubleshoot AIM 1.5](troubleshoot-aim-1.5.md)
- Upgrade an AIM 1.4 repository:
  - [Migrate AIM 1.4 to AIM 1.5](migrate-aim-1.4-to-1.5.md)
  - [Quick start AIM 1.5](quick-start-aim-1.5.md)
  - [Troubleshoot AIM 1.5](troubleshoot-aim-1.5.md)
- Implement or adapt AIM itself:
  - [AGENTS.md](../../AGENTS.md)
  - [Agile iteration method](agile-iteration-method.md)
  - [AIM adapter guidance](aim-adapter-guidance.md)
  - [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

If the goal is only to use AIM in a repo, do not start with `AGENTS.md` or `aim-adapter-guidance.md`.

## Public product docs

Use these first:
- [README.md](../../README.md)
- [Install AIM 1.5](install-aim-1.5.md)
- [Quick start AIM 1.5](quick-start-aim-1.5.md)
- [AIM 1.5 document map](aim-1.5-doc-map.md)
- [Troubleshoot AIM 1.5](troubleshoot-aim-1.5.md)
- [Migrate AIM 1.4 to AIM 1.5](migrate-aim-1.4-to-1.5.md)
- [Release AIM 1.5](release-aim-1.5.md)
- [Example AIM 1.5 reference run](example-aim-1.5-reference-run.md)
- [AIM 1.5 interaction examples](aim-1.5-interaction-examples.md)
- [AIM 1.5 usage guides](aim-1.5-usage-guides.md)

These docs answer:
- what AIM is now
- how to install and start
- why 1.5 treats small scope as behavioral scope instead of minimal file count
- how adapters differ without changing the method
- how to resume, inspect, troubleshoot, and upgrade

## Reference specification docs

Use these when deeper behavior or contracts matter:
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)
- [Agile iteration method](agile-iteration-method.md)
- [AIM adapter guidance](aim-adapter-guidance.md)
- [docs/features/](../features/README.md)
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
- [Copilot layer](copilot-layer.md)
- `.github/agents/`
- `.github/prompts/`
- `.claude/commands/`
- `.claude/agents/`

## Internal planning and historical material

Use these when working on AIM itself rather than just using AIM:
- `docs/epics/`
- `.aim/`
- older release notes and migration docs

## Recommended production reading order

For a new user:
1. [README.md](../../README.md)
2. [Install AIM 1.5](install-aim-1.5.md)
3. [Quick start AIM 1.5](quick-start-aim-1.5.md)
4. [AIM 1.5 document map](aim-1.5-doc-map.md)
5. [Troubleshoot AIM 1.5](troubleshoot-aim-1.5.md)

For a maintainer or adapter implementer:
1. [AGENTS.md](../../AGENTS.md)
2. [Agile iteration method](agile-iteration-method.md)
3. [AIM adapter guidance](aim-adapter-guidance.md)
4. [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
5. [CLAUDE.md](../../CLAUDE.md) when working on Claude Code support
6. [Copilot layer](copilot-layer.md)
