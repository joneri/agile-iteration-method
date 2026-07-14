<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/repo-awareness-two-layer-model.md
-->

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

## Layer 2: static memory and operational documents

Repo-specific memory and operational docs live under stable documentation paths,
for example:

```text
docs/features/
docs/workflow/
docs/architecture/
```

or another repository-configured static docs path. They contain the full
repository-specific truth for areas such as:

- product context
- architecture notes
- UI verification
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

- `kind: operational` for procedural policy with the full contract below
- another explicit `kind` such as `memory` for richer supporting context that
  does not need the operational procedure contract
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
Their paths must stay inside a repo-approved static docs path such as
`docs/workflow/`, `docs/features/`, `docs/architecture/`, or another configured
docs source.
No durable pointer may target `.aim/`; `.aim/` is runtime state and trace
history, not stable repo-awareness documentation.

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

Move knowledge into a static memory doc when it contains:

- larger product or domain context
- architecture notes
- nuanced language or tone guidance
- cross-feature rationale
- maintained examples or evidence that are too large for a profile entry

Keep a compressed summary and pointer in the profile after moving it.

## Calibration and updates

Calibration must:

1. classify new knowledge as structured fact or operational policy
2. update short facts directly in the profile
3. create or refine a static memory or operational doc for rich policy or
   larger supporting context
4. add or update a structured profile pointer
5. assign explicit load triggers
6. validate that the profile did not become a prose dump

Remember operations follow the same boundary.
A long or procedural remembered rule must be proposed as an operational-doc update rather than inserted as profile prose.

## Example

This is a schema example only. It does not require an operational document in every AIM repository:

```yaml
- id: repo-policy-area
  kind: operational
  path: docs/workflow/repo-policy-area.md
  loading: load_when_relevant
  when: the named repository policy affects the active work
  triggers:
    workTypes: [relevant-work-type]
    rolesOrGates: [relevant-role-or-gate]
    risks: [relevant-risk]
    commands: [relevant-command]
    calibration: relevant-policy-area
```

Static memory and operational docs are repo-specific and optional.
A repository should create one only when its own context or complex policy cannot be represented safely as a short structured profile rule.
AIM itself does not require any particular technology-specific operational doc.

## Related files

- `aim.profile.yaml`
- `repo-awareness-calibration.md`
- `source-only validator tooling`
