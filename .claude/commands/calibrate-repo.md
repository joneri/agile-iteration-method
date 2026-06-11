# Calibrate AIM Repo Awareness

Run the canonical `/aim calibrate-repo` flow from `docs/workflow/repo-awareness-calibration.md`.
Its command state effect and fallback are defined in
`docs/workflow/adapter-command-contract.md`.

- start with the smallest trustworthy repository scan
- read Enterprise external memory when Enterprise external mode is active
- read `aim.profile.yaml` as the shared baseline when present
- apply compatible hints from `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml`
- verify uncertain or trust-sensitive facts before persistence
- save structured shared facts to `aim.profile.yaml` for Team/repo opt-in or `~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml` for Enterprise external
- save personal preferences only to the user-level hints file
- never create repo docs, repo profiles, symlinks, or adapter files in Enterprise external mode unless a broader repo-writing footprint or policy is explicitly selected
- never store stable repo-awareness under `.aim/`
- never cite `.aim/reviews`, `.aim/increments`, `.aim/decisions`,
  `.aim/archive`, or other runtime artifacts as durable repository knowledge
- create or update static memory documents under repo docs only for repo opt-in,
  or under `~/.aim/repo-awareness/<repo-fingerprint>/docs/` for Enterprise
  external, when a short profile entry is not enough
- finish with the canonical calibration summary

If command-file routing is unavailable, state that limitation and handle the
same `/aim calibrate-repo` intent in ordinary Claude chat.
