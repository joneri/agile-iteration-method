# AIM 2.0 Tiny Team Profile Artifact

## Purpose

Define the smallest useful Team AIM profile artifact for sharing repo adaptation without committing full AIM docs or active working state.

This is canonical Team AIM profile-artifact behavior.

The concrete artifact name is:

```text
aim.profile.yaml
```

It lives at the repository root when a team intentionally chooses Team AIM.

## User experience

A team should be able to review the shared AIM footprint as lightweight repository metadata.

The profile should answer:

- what local area AIM should inspect first
- which commands matter
- which files or docs are authoritative
- where risk lives
- when the profile is stale
- what AIM should avoid rereading by default

It should not include active Epic state, role handoffs, review notes, or the full AIM method.

For this repository, the root `aim.profile.yaml` is the working example and the smallest Team AIM artifact.

## How it works

A tiny Team AIM profile is a shared pointer to repo intelligence.

It gives future AIM runs a cheaper starting point:

1. reuse the profile
2. inspect the affected locality
3. run the nearest cheap validation
4. expand only when risk or missing evidence requires it

## Artifact location

Default Team AIM artifact:

```text
aim.profile.yaml
```

Why the repo root:

- easy to find without scanning deep docs
- easy to review in a normal code review
- works across branches
- does not require copying AIM reference docs
- keeps `.aim/` available for local working state instead of shared profile data

Pointer-only Team AIM is allowed when profile details must live elsewhere.
In that case, `aim.profile.yaml` should contain only profile identity, owner, storage pointer, freshness rules, and the minimum local validation hints.

## Minimum content

The minimum useful Team AIM profile contains:

- profile version
- repo identity
- adoption mode, footprint, sharing, and owner
- storage locations for runtime, profile, working state, and docs
- locality-first discovery order
- directly useful validation commands
- ownership and risk zones
- short authoritative docs
- known context hogs or avoid-by-default areas
- freshness triggers
- cost defaults for startup, scan depth, review depth, and subagent policy

## Example shape

This example is intentionally generic.
It should be adapted by a real team before use.

```yaml
aimProfileVersion: 0.1
adoption:
  mode: team
  footprint: tiny
  sharing: committed
  owner: team-name-or-codeowners-group

storage:
  runtime: tool-or-local-adapter
  repoProfile: aim.profile.yaml-or-pointer
  workingState: local-and-ignored
  docs: installed-package-or-canonical-links

locality:
  defaultDiscoveryOrder:
    - active-working-state
    - this-profile
    - directly-affected-files
    - nearest-package-or-service-metadata
    - nearest-validation-command
    - short-authoritative-docs
  primaryAreas:
    - packages/*
    - services/*
  nearestMetadata:
    - package.json
    - pyproject.toml
    - go.mod
    - README.md

commands:
  install: use-repo-standard
  build: nearest-package-build
  test: nearest-package-test
  lint: nearest-package-lint
  validate: cheapest-local-check-first

conventions:
  docs: prefer-short-feature-docs
  review: short-review-by-default-escalate-on-risk
  branching: feature-branch-local-state

risk:
  highRiskAreas:
    - migrations
    - deployment
    - authentication
    - billing
    - public-api
  escalation:
    - security
    - data-correctness
    - unclear-ownership
    - cross-service-change

context:
  shortAuthoritativeDocs:
    - README.md
    - docs/architecture.md
  avoidByDefault:
    - broad-doc-rereads
    - repository-wide-search-before-locality-check
  knownContextHogs:
    - oversized-route-or-service-files

freshness:
  refreshTriggers:
    - lockfile-changed
    - package-scripts-changed
    - ownership-changed
    - validation-command-changed
    - architecture-doc-changed
  revalidate:
    - smallest-affected-area-first

cost:
  startup: reuse-profile-before-scan
  scanDepth: locality-first
  reviewDepth: risk-scaled
  subagents: disabled-by-default-unless-policy-allows
```

## What belongs here

The tiny profile may contain:

- repo locality hints
- validation command hints
- short authoritative docs
- risk zones
- ownership hints
- freshness triggers
- cost-observability defaults

## What does not belong here

The tiny profile must not contain:

- active Epic state
- active Done Increment state
- Gate approval state
- role handoff notes
- review findings for one branch
- secrets or credentials
- proprietary detail that should not be committed
- copied AIM reference docs

The tiny profile also must not claim ownership of:

- AIM role order
- Gate A, B, or E approval semantics
- escalation rules
- `.aim/state.json`
- Epic completion decisions

## Inputs and outputs

- Inputs:
  - team repo conventions
  - local validation commands
  - ownership/risk knowledge
  - known expensive context areas

- Outputs:
  - a tiny shared profile
  - cheaper startup for future AIM runs
  - clearer locality-first scans
  - safer profile reuse across branches and sessions
  - validator readiness status of `ready` only when required knowledge is verified and separate from working state

## Key decisions

- The profile is shared repo intelligence, not working state.
- The profile should be small enough to review in a normal code review.
- The committed profile must be small enough to stay reviewable.
- Pointer-only profiles are valid when sensitive details belong in managed storage.
- Stale profile reuse is worse than no reuse, so freshness triggers are part of the example.
- Personal AIM can keep a similar profile locally without committing it.

## Defaults and fallbacks

- Default working state: local and ignored.
- Default profile sharing: root `aim.profile.yaml` only when the team chooses Team AIM.
- Default validation: cheapest local check first.
- Fallback if profile is missing: inspect directly affected files and nearest metadata.
- Fallback if details should not be committed: use a pointer-only `aim.profile.yaml`.
- Fallback if profile is stale: refresh the smallest affected area.
- Fallback if profile conflicts with repo evidence: trust current repo evidence and escalate.

## Edge cases

- Some teams may prefer a pointer to an internal profile registry instead of committing profile content.
- Some repositories may forbid even a tiny profile; use Personal AIM or Enterprise AIM policy instead.
- Cross-cutting changes may require broader discovery even with a fresh profile.
- Security-sensitive profile facts may need to live outside the repository.

## Data correctness and trust

The tiny profile must not override AIM core.

The main AIM thread still owns:

- `.aim/state.json`
- gate progression
- acceptance decisions
- escalation decisions

If the profile and current repository evidence disagree, AIM must treat the profile as stale or incomplete.

## Debugging

The single best check is whether the profile helps AIM explain its startup context choice.

- Primary log: Gate B profile-source summary
- Summary contract: [AIM 2.0 profile source summary](profile-source-summary.md)
- What "good" looks like:
  - AIM says the team profile was reused
  - AIM states which locality it inspected
  - AIM states why no broad scan was needed
  - AIM states freshness assumptions
  - AIM names any broader docs it intentionally avoided
- What "bad" looks like:
  - AIM treats the profile as active working state
  - AIM trusts stale commands
  - AIM rereads broad docs before checking locality
  - the profile is too large to review

## Related files

- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/profile-source-summary.md`
- `aim.profile.yaml`
- `docs/workflow/aim-2-low-footprint-adoption.md`
- `docs/workflow/aim-adapter-guidance.md`
- `docs/workflow/install-aim-2.0.md`

## Change log

- 2026-06-05: Added profile-first startup expectation for consuming `aim.profile.yaml` before broader docs.
- 2026-06-05: Linked the compact profile-source summary contract.
- 2026-06-05: Promoted the tiny Team AIM profile from example shape to concrete `aim.profile.yaml` artifact/pointer model.
- 2026-06-05: Initial tiny Team AIM profile example.
