# AIM UI

Map this command and its arguments to `/aim ui` from
`docs/workflow/adapter-command-contract.md`.

Bare invocation means start-or-open for the current repository. Support
`start`, `open`, `status`, and `stop` with an optional explicit repository.
Resolve only a trusted AIM-owned launcher, keep the server loopback-only, and
never create or mutate `.aim` runtime state as a launch side effect. Report one
local URL or one actionable failure.

If command-file routing is unavailable, state that limitation and handle the
same `/aim ui` intent in ordinary Claude chat.
