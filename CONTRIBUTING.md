# Contributing

Thanks for contributing to **Agile iteration method (AIM)**.

This repo is both:
1) the public method definition, and
2) a copyable implementation kit for real projects.

## Versioning policy (AIM 2.0)
- This repository is the source of truth for AIM.
- Documentation updates here are method updates.
- AIM changes should be proposed and reviewed using AIM itself.
- Keep changes incremental: one coherent method change per PR.

---

## What this repo contains

- `docs/workflow/agile-iteration-method.md`  
  The method and principles.
- `docs/workflow/repo-awareness.md`
  The repo-awareness loading and authority model.
- `docs/workflow/copilot-layer.md`  
  Optional Copilot custom-agent layer.
- `docs/workflow/aim-adapter-guidance.md`
  Adapter entrypoints, parity labels and helper-file boundaries.
- `docs/workflow/install-aim-2.0.md`
  Current installation guide.
- `docs/workflow/quick-start-aim-2.0.md`
  Current first-run guide.
- `docs/workflow/troubleshoot-aim-2.0.md`
  Current troubleshooting guide.
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
- `docs/workflow/agile-iteration-method.md` (explanation)
- the relevant canonical behavior document under `docs/workflow/`
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
Behavior-defining AIM documents belong under `docs/workflow/`.
Use `docs/features/` only for support, reference, examples, comparisons, onboarding playbooks, or repo-local patterns that do not define AIM behavior.

### Active Epic state
AIM stores the active Epic in `.aim/epic.md`.
Do not add committed Epic folders under `docs/`; stable AIM behavior belongs in `docs/workflow/`, while non-canonical support/reference material may live in `docs/features/`.

### Copilot layer
Update `docs/workflow/copilot-layer.md` and `.github/agents/` when:
- command flow changes
- gate handling changes
- setup/install UX changes

Canonical source:
- `docs/workflow/agile-iteration-method.md` defines AIM core behavior.
- canonical model documents under `docs/workflow/` define their behavior areas.
- `aim.profile.yaml` is the primary shared repo-awareness source.
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
- confirm canonical workflow docs and adapter packages do not contradict each other

---

## License

By contributing, you agree your contribution is licensed under **CC BY 4.0** (same as this repository).
