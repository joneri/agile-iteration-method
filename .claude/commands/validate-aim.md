# Validate AIM

Map this command to `/aim validate` from
`docs/workflow/adapter-command-contract.md`.

Run the repository validator when available; otherwise inspect required `.aim`
artifacts and directly affected installer, adapter, profile, canonical-doc, and
public-claim surfaces. Report `healthy`, `recoverable`, `blocked`, or
`contradictory`, plus Structural, Behavioral, Product coherence, and Release
readiness tiers. Do not mutate runtime state.

If command-file routing is unavailable, state that limitation and handle the
same `/aim validate` intent in ordinary Claude chat.
