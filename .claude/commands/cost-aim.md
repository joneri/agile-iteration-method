# Set AIM Cost Profile

Map this command to `/aim cost standard|control|deep` from
`docs/workflow/adapter-command-contract.md`.

Validate the requested profile, update `costProfile` for the active Epic or
increment, and preserve all gate and approval semantics. Escalate depth when
risk requires it.

If command-file routing is unavailable, state that limitation and handle the
same `/aim cost` intent in ordinary Claude chat.
