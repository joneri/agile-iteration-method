# AIM 2.0 Migration Classification Checks

## Purpose

Explain how AIM 2.0 classifies existing AIM 1.7 repository artifacts before moving toward lower-footprint adoption.

The goal is to make migration concrete without moving files automatically.

## User experience

When a user runs the AIM validator, the output includes an AIM 2.0 migration classification.

It groups known artifacts into:

- runtime
- repo profile
- working state
- docs
- adapter helpers

This helps a developer or team understand what could stay local, what could become a tiny shared profile, and what is only reference material.

## How it works

`scripts/validate_aim_runtime.py` checks for known AIM 1.7 paths and reports which ones exist in each category.

The check is informational.
It does not move, rewrite, delete, or require files.

The only related enforcement is the profile/state separation check:

- if an optional repo profile file exists and contains active working-state markers, the validator reports a recoverable issue
- if an optional repo profile file exists but does not expose recognizable repo-intelligence sections, the validator reports a recoverable issue
- if no optional repo profile file exists, the validator reports `not_ready` without failing AIM 1.7 validation
- otherwise, classification alone does not affect health

The immediate product consequence is that AIM can distinguish:

- AIM 1.7 repositories that are valid but not yet ready for AIM 2.0 profile reuse
- repositories that have an incomplete or unsafe profile artifact
- repositories that have a reusable Personal or Team AIM profile candidate

## Repo-profile readiness

The validator reports `AIM 2.0 repo profile readiness` after migration classification.

Readiness statuses:

- `not_ready`: no AIM 2.0 profile artifact exists yet
- `incomplete_profile`: a profile artifact exists but lacks recognizable repo-intelligence markers
- `repair_profile`: a profile artifact exists but contains active AIM working-state markers
- `profile_ready`: a profile artifact exists, looks like reusable repo intelligence, and does not contain active working-state markers

`not_ready` is informational because AIM 1.7 repositories remain valid during migration.
`incomplete_profile` and `repair_profile` are recoverable because they would make reuse misleading or unsafe.

## Classification buckets

### Runtime

Runtime support is executable or tool-owned behavior that helps AIM run.

Current example:

- `scripts/validate_aim_runtime.py`

### Repo profile

Repo profile artifacts contain reusable repo intelligence or point to it.

Current examples:

- `AGENTS.md`
- `aim.profile.*`
- `.aim/profile.*`
- `.aim/repo-profile.*`

In AIM 2.0, a team may move reusable facts from broad embedded instructions into a smaller profile or pointer.

### Working state

Working state is active or historical AIM run state.

Current examples:

- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`
- `.aim/handoffs/`
- `.aim/logs/`
- `.aim/archive/`
- `.aim/runtime-context.md`
- `.aim/analysis/`

Working state should not be confused with reusable repo profile data.

### Docs

Docs are reference material.

Current examples:

- `README.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `docs/features/`
- `docs/workflow/`

Docs may remain in AIM itself, templates, or fully embedded repositories.
They should not be copied wholesale into every repository by default in AIM 2.0.

### Adapter helpers

Adapter helpers expose AIM to a specific tool or platform.

Current examples:

- `CLAUDE.md`
- `.claude/`
- `.github/agents/`
- `.github/prompts/`
- `adapters/codex/agile-iteration-method/SKILL.md`

Adapter helpers may improve user experience, but they do not own gate progression or acceptance.

## Inputs and outputs

- Inputs:
  - existing repository files
  - optional AIM 2.0 repo profile files
  - current `.aim` workspace

- Outputs:
  - migration classification report
  - repo-profile readiness status
  - recoverable issue when profile files contain active working-state markers
  - recoverable issue when profile files do not contain recognizable repo-intelligence sections

## Key decisions

- Classification is non-mutating.
- Classification does not mean AIM 2.0 migration is complete.
- Repo-profile readiness is the first validator-backed checkpoint for Personal/Team AIM reuse.
- Working state remains separate from repo profile.
- Adapter helpers remain separate from AIM core.
- Full embedded AIM remains valid by explicit repository choice.

## Defaults and fallbacks

- Default classification: report known artifacts only.
- Fallback for unknown files: leave them unclassified.
- Fallback when no optional repo profile exists: report `not_ready` without failing AIM 1.7 validation.
- Fallback when a profile is present but too empty to reuse: report `incomplete_profile`.
- Fallback when profile/state blending is detected: report recoverable and tell the user to move active state back to `.aim`.
- Fallback when required AIM files are missing: keep existing validator result behavior.

## Edge cases

- `AGENTS.md` may contain both repo profile information and embedded AIM behavior during the AIM 1.7-to-2.0 transition.
- Some adapter helper files also contain instructional text; classification still treats them as adapter helpers.
- Some repositories may intentionally remain full embedded AIM repositories.
- A tiny Team AIM profile may be a pointer rather than a full local file.

## Data correctness and trust

Migration classification must not change AIM authority.

Only the main AIM thread owns:

- `.aim/state.json`
- gate progression
- increment acceptance
- Epic completion

The validator reports what exists and what appears mixed.
It does not perform migration.

## Debugging

The single best check is whether the validator can explain where each current AIM 1.7 artifact belongs.

- Primary log: `AIM 2.0 migration classification`
- Reuse checkpoint: `AIM 2.0 repo profile readiness`
- What "good" looks like:
  - runtime support is separate from docs
  - repo profile is separate from working state
  - adapter helpers are visible as tool-specific surfaces
  - `.aim` active state is not treated as reusable profile data
  - profile readiness is `profile_ready` before AIM relies on profile reuse
- What "bad" looks like:
  - active Epic or gate fields appear in `aim.profile.*`
  - `aim.profile.*` exists but contains no commands, locality, ownership, risk, freshness, or cost hints
  - adapter helper files are treated as gate owners
  - docs are treated as mandatory install payload for every repository

## Related files

- `scripts/validate_aim_runtime.py`
- `docs/features/aim-2-repo-profile-and-footprint-model.md`
- `docs/features/aim-2-working-state-boundaries.md`
- `docs/workflow/aim-2-low-footprint-adoption.md`

## Change log

- 2026-06-05: Added repo-profile readiness checks as the first reusable profile migration checkpoint.
- 2026-06-05: Initial migration classification checks for AIM 1.7-to-2.0 transition.
