# Replan AIM

Map this command to `/aim replan` from
`docs/workflow/adapter-command-contract.md`.

For legacy Epic/DI work, record the reason and return only the active unaccepted
increment to Gate B planning. Preserve accepted increments and Epic scope.
Story deliveries have no approved-scope replan transition: preserve the commitment
and use the block/rework limitations in `docs/workflow/user-stories.md`.

If command-file routing is unavailable, state that limitation and handle the
same `/aim replan` intent in ordinary Claude chat.
