---
mode: aim
---

Run `/aim calibrate-repo`.

Follow `docs/workflow/repo-awareness-calibration.md`.
Start with the smallest trustworthy scan, verify uncertain or trust-sensitive facts, and persist structured shared knowledge to `aim.profile.yaml`.
Persist personal preferences only to `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
Never store stable repo-awareness under `.aim/`, and never cite `.aim/reviews`,
`.aim/increments`, `.aim/decisions`, `.aim/archive`, or other runtime artifacts
as durable repository knowledge. Reading `.aim/state.json` to resume active work
is still allowed.

If a remembered fact is too large or nuanced for a short profile entry, create
or update a static memory document under `docs/features/`, `docs/workflow/`,
`docs/architecture/`, or another repo-configured stable docs path, then reference
that static source from `aim.profile.yaml`.

End with the canonical human-visible calibration summary.
