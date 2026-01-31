# Contributing

Thanks for contributing to **Agile iteration method (AIM)**.

This repo is both:
1) a public description of the method, and  
2) a working set of repo files you can copy into your own project.

If you want to *use* AIM in another repo, start with `AGENTS.md`.

---

## What this repo contains

- `workflow/agile-iteration-method.md`  
  The method, mindset and why it exists.

- `AGENTS.md`  
  The operational rules and the Codex “master prompt” for VS Code.

- `docs/runbooks/_template.md`  
  Template for runbooks (feature truth + how to change safely).

- `docs/features-explanations/_template.md`  
  Template for feature explanations (contracts, rules, fallbacks).

---

## Contribution goals

Contributions should improve one of these:

- clarity (people understand the method faster)
- correctness (rules align, no contradictions)
- usability (copy-paste works and the loop is easier to run)
- examples (small, generic examples people can reuse)

Avoid adding large “frameworks” or opinionated extras.

---

## Rules for changes

### Keep changes small
- One focused change per PR.
- Avoid drive-by refactors.

### Keep documents consistent
If you change a rule in one place, update the other place if needed:
- `AGENTS.md` (operational)
- `workflow/agile-iteration-method.md` (explanation)

### Examples must be generic
Avoid referencing personal apps, internal systems or proprietary setups.

### Avoid heavy logging guidance
AIM is about ownership, gates and small increments.  
Logging can be mentioned, but keep it practical and minimal.

---

## Adding or updating documentation

### When to add a feature explanation
Add/update a file in `docs/features-explanations/` when a change introduces:
- a new behaviour or user-visible rule
- a non-obvious fallback or constraint
- a contract change (inputs/outputs, semantics)

### When to add or update a runbook
Add/update a file in `docs/runbooks/` when you introduce or change:
- a workflow for delivering a feature safely
- acceptance checks that should stay stable over time
- “how we avoid misleading output” type rules

---

## How to propose improvements

### Small edits
Open a PR with:
- what you changed
- why it improves clarity/correctness/usability
- what file(s) were touched

### Bigger changes
Open an issue first describing:
- the problem you see
- the smallest change that would solve it
- what you are *not* trying to change

---

## Local checks

No build is required.

Before submitting:
- spell check the changed sections
- ensure headings and terminology match existing style
- confirm there are no contradictions between `AGENTS.md` and `workflow/agile-iteration-method.md`

---

## License

By contributing, you agree that your contribution is licensed under **CC BY 4.0** (same as this repository).