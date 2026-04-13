> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Migrate AIM 1.4 to AIM 1.5

Use this when a repository already follows AIM 1.4 and needs the AIM 1.5 release framing.

## What changes in 1.5

AIM 1.5 does not redesign the core loop or replace the accepted runtime model.
It makes three things more visible and operational:
- small increments are measured by behavioral scope, not minimal file count
- focused file boundaries are treated as part of delivery quality and review quality
- the public onboarding path now makes the latest adapter and release guidance obvious to users

## Migration checklist

- update active public docs from 1.4 to 1.5 naming where the repository treats them as the current release surface
- keep older 1.4 release and migration docs as historical references
- update README, install, quick-start, doc map, troubleshoot, usage, interaction-example, and reference-run docs to point to the 1.5 surface
- update prompt helpers and packaged agent metadata so they present AIM 1.5 consistently
- confirm the modularity guidance is visible in public docs, not only in internal guidance

## Command-surface changes to verify

After migration, the repository should document and expose these AIM 1.5 commands or their explicit adapter-equivalent entrypoints:
- `/aim start "EPIC: ..."`
- `/aim continue`
- `/aim status`
- `/aim help`
- `/aim validate`
- `/aim config`
- `/aim upgrade 1.4-to-1.5`

Migration check:
- if a command is conceptually supported but not packaged in one adapter, document the fallback clearly instead of implying silent support

## Related docs

- [Install AIM 1.5](install-aim-1.5.md)
- [Quick start AIM 1.5](quick-start-aim-1.5.md)
- [AIM 1.5 document map](aim-1.5-doc-map.md)
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)
