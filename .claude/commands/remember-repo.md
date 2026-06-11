# Remember AIM Repository Knowledge

Map the request to:

```text
/aim remember-repo <category> "<rule>"
```

Follow `docs/workflow/repo-awareness-calibration.md`.
Preserve the state effect from `docs/workflow/adapter-command-contract.md`.
Resolve shared versus personal scope, use a canonical structured category, show the proposed entry, and persist it to `aim.profile.yaml` or `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
Never store stable repository knowledge under `.aim/`, and never cite
`.aim/reviews`, `.aim/increments`, `.aim/decisions`, `.aim/archive`, or other
runtime artifacts as durable repository knowledge. Reading `.aim/state.json` to
resume active work remains allowed.

If remembered knowledge is too large for a short profile entry, create or update
a static memory document under `docs/features/`, `docs/workflow/`,
`docs/architecture/`, or another repo-configured stable docs path, then point to
that static source from the profile.

If command-file routing is unavailable, state that limitation and handle the
same `/aim remember-repo` intent in ordinary Claude chat.
