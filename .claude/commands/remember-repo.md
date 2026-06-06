# Remember AIM Repository Knowledge

Map the request to:

```text
/aim remember-repo <category> "<rule>"
```

Follow `docs/workflow/repo-awareness-calibration.md`.
Preserve the state effect from `docs/workflow/adapter-command-contract.md`.
Resolve shared versus personal scope, use a canonical structured category, show the proposed entry, and persist it to `aim.profile.yaml` or `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
Never store stable repository knowledge under `.aim/`.

If command-file routing is unavailable, state that limitation and handle the
same `/aim remember-repo` intent in ordinary Claude chat.
