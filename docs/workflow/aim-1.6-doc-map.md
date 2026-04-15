> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.6 document map

Use this guide only when the first three choices are not enough.

The light front door is:
- start: [Quick start AIM 1.6](quick-start-aim-1.6.md)
- continue or check setup: [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)
- install or upgrade: [Install AIM 1.6](install-aim-1.6.md)

This map explains the broader public docs, reference specifications, and internal planning material.

## Choose your path

Use this route first instead of guessing from file names:

- Evaluate AIM:
  - [README.md](../../README.md)
  - [Quick start AIM 1.6](quick-start-aim-1.6.md)
  - [AIM 1.6 interaction examples](aim-1.6-interaction-examples.md)
- Install AIM in a repository:
  - [README.md](../../README.md)
  - [Install AIM 1.6](install-aim-1.6.md)
  - [Quick start AIM 1.6](quick-start-aim-1.6.md)
  - [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)
- Upgrade an AIM 1.5 repository:
  - [Migrate AIM 1.5 to AIM 1.6](migrate-aim-1.5-to-1.6.md)
  - [Quick start AIM 1.6](quick-start-aim-1.6.md)
  - [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)
- Implement or adapt AIM itself:
  - [AGENTS.md](../../AGENTS.md)
  - [Agile iteration method](agile-iteration-method.md)
  - [AIM adapter guidance](aim-adapter-guidance.md)
  - [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

If the goal is only to use AIM in a repo, do not start with `AGENTS.md` or `aim-adapter-guidance.md`.

## Public product docs

Use these first:
- [README.md](../../README.md)
- [Install AIM 1.6](install-aim-1.6.md)
- [Quick start AIM 1.6](quick-start-aim-1.6.md)
- [AIM 1.6 document map](aim-1.6-doc-map.md)
- [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)
- [Migrate AIM 1.5 to AIM 1.6](migrate-aim-1.5-to-1.6.md)
- [Release AIM 1.6](release-aim-1.6.md)
- [Example AIM 1.6 reference run](example-aim-1.6-reference-run.md)
- [AIM 1.6 interaction examples](aim-1.6-interaction-examples.md)
- [AIM 1.6 usage guides](aim-1.6-usage-guides.md)

These docs answer:
- what AIM is now
- how to install and start
- how AIM 1.6 uses cost profiles to control runtime depth
- why AIM treats small scope as behavioral scope instead of minimal file count
- why AIM 1.6 avoids context hogs by preferring cohesive boundaries over oversized all-in-one files
- how adapters differ without changing the method
- how to resume, inspect, troubleshoot, and upgrade

## Reference specification docs

Use these when deeper behavior or contracts matter:
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)
- [Agile iteration method](agile-iteration-method.md)
- [AIM adapter guidance](aim-adapter-guidance.md)
- [docs/features/](../features/README.md)
- [AIM Cost Control Mode](../features/aim-cost-control-mode.md)
- [AIM Light Front Door](../features/aim-light-front-door.md)
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
- `CHANGELOG.md`
- current release and migration docs in `docs/workflow/`

## Recommended production reading order

For a new user:
1. [README.md](../../README.md)
2. [Install AIM 1.6](install-aim-1.6.md)
3. [Quick start AIM 1.6](quick-start-aim-1.6.md)
4. [AIM 1.6 document map](aim-1.6-doc-map.md)
5. [Troubleshoot AIM 1.6](troubleshoot-aim-1.6.md)

For a maintainer or adapter implementer:
1. [AGENTS.md](../../AGENTS.md)
2. [Agile iteration method](agile-iteration-method.md)
3. [AIM adapter guidance](aim-adapter-guidance.md)
4. [AIM Cost Control Mode](../features/aim-cost-control-mode.md)
5. [AIM Light Front Door](../features/aim-light-front-door.md)
6. [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
7. [CLAUDE.md](../../CLAUDE.md) when working on Claude Code support
8. [Copilot layer](copilot-layer.md)
