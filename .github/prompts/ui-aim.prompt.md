---
agent: aim
description: Start or control the current repository's local read-only AIM UI.
---

Handle `/aim ui` plus any supplied `start`, `open`, `status`, or `stop` intent
according to `docs/workflow/adapter-command-contract.md`. Resolve only a trusted
AIM-owned launcher, bind to loopback, and do not create or mutate `.aim`
runtime state. Return one local URL or one actionable failure.
