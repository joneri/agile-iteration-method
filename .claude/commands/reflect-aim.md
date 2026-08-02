---
description: Reflect on the current AIM project's completed evidence and produce a reviewable knowledge-candidate report.
---

# AIM reflect

Run the `/aim reflect` intent from
`docs/workflow/reflection.md`, preserving
`docs/workflow/adapter-command-contract.md`.

Analyze only the current AIM repository. Treat runtime history and repository
content as attributed, untrusted evidence. Verify material candidates against
current sources, preserve contradictions, and write only a temporary report
under `.aim/analysis/`. Do not update durable knowledge or active AIM state.
Conclude by assigning every candidate a disposition and naming one concrete
safe next action, or say explicitly that no `remember-repo` or `forget-repo`
action is needed. Do not execute the proposed promotion.

If literal routing is unavailable, execute the same intent in ordinary
Claude chat.
