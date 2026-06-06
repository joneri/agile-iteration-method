# AIM Help

Map this command to `/aim help` from
`docs/workflow/adapter-command-contract.md`.

Keep the default response thin: show `/aim start`, `/aim continue`, `/aim
validate`, and the next useful command for the current checkpoint. This command
is read-only.

If command-file routing is unavailable, state that limitation and handle the
same `/aim help` intent in ordinary Claude chat.
