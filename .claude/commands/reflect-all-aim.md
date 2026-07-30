---
description: Safely inventory selected local AIM projects and produce a cross-project knowledge-candidate report.
---

# AIM reflect-all

Run the `/aim reflect-all` intent from
`docs/workflow/reflection.md`, preserving
`docs/workflow/adapter-command-contract.md`.

Resolve only explicit or configured discovery roots, or the current repository's
parent fallback. Preview the cheap repository inventory and workload before
unapproved content analysis. Never scan the home directory or filesystem root
implicitly, never modify discovered repositories, and write only a temporary
candidate report in the initiating repository's `.aim/analysis/`.

If literal routing is unavailable, execute the same intent in ordinary
Claude chat.
