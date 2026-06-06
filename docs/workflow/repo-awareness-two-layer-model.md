# AIM 2.0 Two-Layer Repo Awareness

## Purpose

Keep repository startup cheap without flattening rich operational policy.

## Layer 1: structured profile

`aim.profile.yaml` is the compressed operational map.

It contains:

- short facts and summary rules
- commands and localities
- risk and freshness markers
- confidence, source, and verified state
- document pointers
- structured loading triggers

Profile values must remain concise.
If a rule needs rationale, multiple steps, edge cases, blockers, debugging, evidence expectations, or several commands, it belongs in an operational document.

## Layer 2: operational documents

AIM-owned repo-specific operational docs live under:

```text
docs/workflow/repo-<area>.md
```

They contain the full repository-specific truth for areas such as:

- UI and Playwright verification
- deployment
- migrations
- reviewer evidence
- release handling
- security-sensitive workflows

An operational doc must state:

- purpose
- applicability and triggers
- exact procedure and commands
- evidence expectations
- blockers and escalation
- edge cases
- debugging
- related surfaces

## Pointer contract

Profile pointers use:

- `kind: operational`
- `path`
- `loading`
- `when`
- `triggers`
  - `workTypes`
  - `rolesOrGates`
  - `risks`
  - `commands`
  - `calibration`

`loading` uses the canonical document-loading states.
Repo operational docs normally use `load_when_relevant`.
Only pointers marked `kind: operational` are subject to the operational-doc contract.
Their paths must stay inside the AIM-owned `docs/workflow/repo-<area>.md` namespace.

Load a pointed document when any declared trigger matches the active work.
Do not load it merely because it exists.

## Placement decision

Keep knowledge in the profile when it is:

- short
- atomic
- structured
- independently verifiable
- useful during cheap startup

Move knowledge into a repo operational doc when it contains:

- multi-step procedures
- role or gate obligations
- evidence contracts
- exceptions or blockers
- troubleshooting
- multiple related commands
- policy rationale needed for safe execution

Keep a compressed summary and pointer in the profile after moving it.

## Calibration and updates

Calibration must:

1. classify new knowledge as structured fact or operational policy
2. update short facts directly in the profile
3. create or refine `docs/workflow/repo-<area>.md` for rich policy
4. add or update a structured profile pointer
5. assign explicit load triggers
6. validate that the profile did not become a prose dump

Remember operations follow the same boundary.
A long or procedural remembered rule must be proposed as an operational-doc update rather than inserted as profile prose.

## Example

The profile says that rendered UI work requires Playwright evidence and points to `docs/workflow/repo-playwright-verification.md`.
The deeper document loads for UI work, Reviewer or Gate E verification, visual-regression risk, Playwright commands, or calibration of UI-testing policy.

## Related files

- `aim.profile.yaml`
- `docs/workflow/repo-awareness-calibration.md`
- `docs/workflow/repo-playwright-verification.md`
- `scripts/validate_aim_runtime.py`
