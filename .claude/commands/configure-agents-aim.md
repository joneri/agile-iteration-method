# Configure AIM Project Specialists

Map this command to `/aim configure-agents` from
`docs/workflow/adapter-command-contract.md` and follow
`docs/workflow/project-agent-configuration.md`.

Read `aim.roles.yaml`, then `aim.profile.yaml`, inspect only freshness-triggered
project evidence, and show proposed role/profile changes before writing. Refresh
the selected supplier-native AIM specialist files without overwriting user edits
silently. Never write `.aim/state.json` or advance a gate.

If literal slash routing is unavailable, preserve the same intent when the user
asks AIM to configure, specialize, refresh, or update project agents.
