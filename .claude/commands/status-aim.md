# AIM Status

Map this command to `/aim status` from
`docs/workflow/adapter-command-contract.md`.

Read `.aim/state.json` and report the Epic, active increment, role, mode, cost
profile, gate, adapter, and next action. This command is read-only.

If command-file routing is unavailable, state that limitation and handle the
same `/aim status` intent in ordinary Claude chat.
