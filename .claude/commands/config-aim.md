# AIM Config

Map this command to `/aim config` from
`docs/workflow/adapter-command-contract.md`.

Follow [runtime source routing](../../docs/workflow/adapter-command-contract.md#runtime-source-routing)
before selecting state. Report effective mode, cost profile, Ship/Loop
policy, repo profile source, ownership, validation, parallel policy and adapter
fallback. Read only the relevant runtime, profile and current mandate. Native
frozen delivery policy and an explicitly selected legacy workspace retain their
own authority. Never infer configuration from an unrelated root checkpoint.

If command-file routing is unavailable, state that limitation and handle the
same `/aim config` intent in ordinary Claude chat.
