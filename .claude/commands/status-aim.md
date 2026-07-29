# AIM Status

Map this command to `/aim status` from
`docs/workflow/adapter-command-contract.md`.

Read `VERSION` and `.aim/state.json`, then report the current AIM product
release separately from the runtime contract in `aimVersion`, followed by the
Epic, active increment, role, mode, cost profile, gate, adapter, and next action.
This command is read-only.

If command-file routing is unavailable, state that limitation and handle the
same `/aim status` intent in ordinary Claude chat.
