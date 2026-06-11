---
mode: aim
---

Run `/aim calibrate-repo`.

Follow `docs/workflow/repo-awareness-calibration.md`.
Start with the smallest trustworthy scan, verify uncertain or trust-sensitive facts, and persist structured shared knowledge to `aim.profile.yaml` for Team/repo opt-in or `~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml` for Enterprise external mode.
Persist personal preferences only to `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`.
In Enterprise external mode, do not create repo docs, repo profiles, symlinks, or adapter files unless the repo owner explicitly selected a broader repo-writing footprint or policy.
Never store stable repo-awareness under `.aim/`, and never cite `.aim/reviews`,
`.aim/increments`, `.aim/decisions`, `.aim/archive`, or other runtime artifacts
as durable repository knowledge. Reading `.aim/state.json` to resume active work
is still allowed.

If a remembered fact is too large or nuanced for a short profile entry, create
or update a static memory document in the selected durable store: repo docs under
`docs/features/`, `docs/workflow/`, `docs/architecture/`, or another
repo-configured stable docs path only for repo opt-in, or
`~/.aim/repo-awareness/<repo-fingerprint>/docs/` for Enterprise external. Then
reference that static source from `aim.profile.yaml` or the external memory
index.

End with the canonical human-visible calibration summary.
