# AIM Config

Map this command to `/aim config` from
`docs/workflow/adapter-command-contract.md`.

Report effective mode, cost profile, repo profile source, ownership, validation,
parallel policy, and adapter fallback. Read from `.aim/state.json`,
`aim.profile.yaml`, and current adapter policy without changing them.

If command-file routing is unavailable, state that limitation and handle the
same `/aim config` intent in ordinary Claude chat.
