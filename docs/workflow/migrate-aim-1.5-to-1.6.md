> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Migrate AIM 1.5 to AIM 1.6

Use this when a repository already follows AIM 1.5 and needs the AIM 1.6 release framing.

## What changes in 1.6

AIM 1.6 does not redesign the core loop or replace the accepted runtime model.
It adds explicit cost profiles and makes normal AIM cheaper:
- `Standard`, `Cost Control`, and `Deep` define runtime depth
- `Strict` and `Auto` remain approval modes
- Standard AIM uses progressive context loading
- Cost Control preserves gates and escalation while narrowing context and output
- Deep provides a named higher-assurance profile for risky work

## Migration checklist

- update active public docs from 1.5 to 1.6 naming where the repository treats them as the current release surface
- add Cost Control and Deep profile guidance to repository instructions and public docs
- update README, install, quick-start, doc map, troubleshoot, usage, interaction-example, and reference-run docs to point to the 1.6 surface
- update prompt helpers and packaged agent metadata so they present AIM 1.6 consistently
- confirm cost-control guidance is visible in public docs, not only in internal guidance

## Command-surface changes to verify

After migration, the repository should document and expose these AIM 1.6 commands or their explicit adapter-equivalent entrypoints:
- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim cost standard|control|deep`
- `/aim upgrade 1.5-to-1.6`

Migration check:
- if a command is conceptually supported but not packaged in one adapter, document the fallback clearly instead of implying silent support

## Related docs

- [Install AIM 1.6](install-aim-1.6.md)
- [Quick start AIM 1.6](quick-start-aim-1.6.md)
- [AIM 1.6 document map](aim-1.6-doc-map.md)
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
