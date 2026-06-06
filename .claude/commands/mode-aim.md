# Set AIM Mode

Map this command to `/aim mode strict|auto` from
`docs/workflow/adapter-command-contract.md`.

Validate the requested value, update only the active Epic's mode in
`.aim/state.json`, and report the new mode. Changing mode never approves or
skips a gate.

If command-file routing is unavailable, state that limitation and handle the
same `/aim mode` intent in ordinary Claude chat.
