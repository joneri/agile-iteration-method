---
agent: aim
description: Preview and explicitly approve one rollback-safe AIM catalog-history repair.
---

Handle `/aim repair-catalog <candidate-id>` according to
`docs/workflow/adapter-command-contract.md`. Resolve one exact completed
runtime-linked candidate, Epic, Increment, non-root workspace, state timestamp,
and contained Gate E acceptance file. Use trusted packaged
`scripts/aim_catalog_repair.py` first for a no-write preview, show every digest
and archive/audit destination, and require separate explicit approval for the
digest-matched apply. Never infer repair or give AIM UI write authority.
