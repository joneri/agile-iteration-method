# Contributing

Thanks for contributing to **Agile iteration method (AIM)**.

This repo is both:
1) the public method definition, and
2) a copyable implementation kit for real projects.

## Versioning policy (AIM 1.7)
- This repository is the source of truth for AIM.
- Documentation updates here are method updates.
- AIM changes should be proposed and reviewed using AIM itself.
- Keep changes incremental: one coherent method change per PR.

---

## What this repo contains

- `docs/workflow/agile-iteration-method.md`  
  The method and principles.
- `AGENTS.md`  
  Operational rules for Codex execution.
- `docs/workflow/copilot-layer.md`  
  Optional Copilot custom-agent layer.
- `docs/workflow/aim-adapter-guidance.md`
  Adapter entrypoints, parity labels and helper-file boundaries.
- `docs/workflow/install-aim-1.7.md`
  Current installation front door.
- `docs/workflow/quick-start-aim-1.7.md`
  Current first-run front door.
- `docs/workflow/aim-1.7-doc-map.md`
  Current navigation map.
- `docs/workflow/install-aim-1.6.md`
  Stable runtime-family installation guide.
- `docs/workflow/quick-start-aim-1.6.md`
  Stable runtime-family first-run guide.
- `docs/workflow/aim-1.6-doc-map.md`
  Stable runtime-family navigation map.
- `docs/workflow/migrate-aim-1.5-to-1.6.md`
  Current supported upgrade bridge for older AIM 1.5 repositories.
- `docs/workflow/release-aim-1.7.md`
  Current release notes.
- `docs/features/_template.md`  
  Feature explanation template (contracts, rules, fallbacks).
- `CONTRIBUTORS.md`  
  Creator and contributors acknowledgment.

---

## Contribution goals

Contributions should improve one of these:
- clarity
- correctness
- usability
- examples

Avoid large frameworks or opinionated extras unless explicitly requested.

---

## Rules for changes

### Keep changes small
- One focused change per PR.
- Avoid drive-by refactors.

### Keep documents consistent
If you change a rule in one place, update the others if needed:
- `AGENTS.md` (operational)
- `docs/workflow/agile-iteration-method.md` (explanation)
- `docs/workflow/copilot-layer.md` (Copilot interface, if relevant)
- `.github/agents/aim*.agent.md` and `.github/prompts/` (adapter packaging, if relevant)

### Examples must be generic
Avoid personal apps, internal systems, or proprietary setups.

### Logging guidance must stay lightweight
AIM is about ownership, gates, and increments.
Mention logging only when it helps verify a hypothesis.

---

## Documentation updates

### Feature explanations
Add/update a file in `docs/features/` when a change introduces:
- new user-visible behavior or rule
- non-obvious fallback or constraint
- contract changes (inputs/outputs/semantics)

### Active Epic state
AIM stores the active Epic in `.aim/epic.md`.
Do not add committed Epic folders under `docs/`; stable feature contracts belong in `docs/features/`.

### Copilot layer
Update `docs/workflow/copilot-layer.md` and `.github/agents/` when:
- command flow changes
- gate handling changes
- setup/install UX changes

Canonical source:
- `AGENTS.md` and `docs/workflow/agile-iteration-method.md` define AIM behavior.
- `.github/agents/` and `.github/prompts/` package Copilot entrypoints.

---

## How to propose improvements

### Small edits
Open a PR with:
- what changed
- why it improves AIM
- files touched

If the change is substantial and from a new contributor:
- add/update `CONTRIBUTORS.md` in the same PR.

### Larger method changes
Open an issue first describing:
- the problem
- the smallest viable fix
- explicit non-goals

---

## Local checks

No build is required.

Before submitting:
- spell-check changed sections
- keep terms consistent (Epic, Done Increment, Gate A-E)
- confirm no contradictions between `AGENTS.md` and `docs/workflow/agile-iteration-method.md`

---

## License

By contributing, you agree your contribution is licensed under **CC BY 4.0** (same as this repository).
