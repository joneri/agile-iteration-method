> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 low-footprint adoption

Use this guide when you want the AIM 2.0 adoption model without copying the full AIM method package into a repository.

AIM 2.0 is not released as a final runtime yet.
This guide defines the practical product path that future runtime and installer work should follow.

## What changes in AIM 2.0

AIM 2.0 separates four things that AIM 1.7 still blends too much:

- AIM runtime: how the loop runs
- AIM repo profile: reusable knowledge about the repository
- AIM working state: the current Epic, increment, gate, and handoff state
- AIM docs: reference material

Using AIM should not require committing all AIM docs and adapter files into every repository.

## Choose an adoption depth

### Personal AIM

Use Personal AIM when one developer wants AIM discipline without repository mutation.

Default behavior:

- no committed AIM files
- local runtime from the tool or adapter
- local working state
- local repo profile
- AIM docs read from the installed package or canonical AIM repository

Best for:

- trying AIM in a large existing repo
- protected enterprise repos
- feature branches where the developer does not own repository policy
- comparing AIM against normal agentic coding

### Team AIM

Use Team AIM when a team wants to share repo adaptation without copying the full method.

Default behavior:

- tiny committed profile surface or pointer
- shared repo profile facts
- local working state by default
- runtime still supplied by the tool or adapter
- AIM docs linked, not copied wholesale

Best for:

- shared commands and validation paths
- known risk zones
- team coding conventions
- avoiding repeated cold-start scans across teammates

### Managed AIM

Use Managed AIM later when an organization wants central policy and governed shared profiles.

Default behavior:

- approved runtime or adapter
- shared profile registry
- central policy
- optional repository pointer

Managed AIM should not block Personal AIM or Team AIM.
It is the later standardization path, not the starting requirement.

### Full embedded AIM

Use Full embedded AIM only when the repo owner intentionally wants AIM inside the repo.

Best for:

- AIM itself
- templates
- training repositories
- public examples

Full embedded AIM remains valid, but it is not the default definition of adoption.

## Where things live

| Layer | Personal AIM | Team AIM | Managed AIM |
| --- | --- | --- | --- |
| Runtime | tool or local adapter | tool or local adapter | approved org adapter |
| Repo profile | local user/adapter storage | tiny committed profile or pointer | managed registry |
| Working state | local and ignored | local by default | local or approved shared store |
| Docs | installed package or links | installed package or links | managed docs or canonical links |

The important rule is simple:

> Repo profile is reusable knowledge. Working state is current work. Docs are reference material. Runtime is how AIM runs.

Do not blend them by default.

## Practical startup flow

These command shapes are conceptual direction, not final CLI syntax.

### Personal start

```text
aim init --personal
aim scan repo --locality <area>
aim save-profile --local
aim start "EPIC: <goal>"
```

What the runtime should do:

1. avoid committed AIM files by default
2. create or reuse a local repo profile
3. create local working state
4. scan only the affected area first
5. load broader docs only when risk requires it

### Team start

```text
aim init --team
aim profile export --tiny
aim start "EPIC: <goal>"
```

What the runtime should do:

1. create or reuse a small shared repo profile
2. keep active working state local unless the team chooses otherwise
3. avoid copying full AIM docs into the repo
4. let teammates reuse commands, conventions, risk zones, and validation paths

### Managed direction

```text
aim profile attach <managed-profile>
aim policy check
aim start "EPIC: <goal>"
```

What the runtime should eventually do:

1. attach an approved profile or policy
2. validate local work against managed rules
3. preserve locality-first scanning
4. avoid making every repository duplicate organization policy

## Locality-first discovery

At startup, AIM should load context in this order:

1. active working state
2. reusable repo profile
3. directly affected files
4. nearest package, service, or module metadata
5. nearest commands for build, test, lint, or validation
6. short authoritative docs named by the profile
7. broader repository docs only when risk or missing evidence requires them

This is the main cold-start cost reduction.

AIM should not scan a large monorepo broadly when the work is local, low-risk, and covered by a fresh profile.

## Reusing repo intelligence

AIM can reuse a repo profile across branches and sessions when:

- the repo identity matches
- the profile owner is clear
- the branch difference is understood
- no freshness trigger has fired
- the active work is inside a known locality boundary
- the selected cost profile allows reuse

AIM should refresh the smallest affected area when:

- lockfiles changed
- package scripts changed
- build or test tooling changed
- ownership metadata changed
- relevant docs changed
- the work crosses risk or ownership boundaries
- the user selected Deep for trust-sensitive work

## Cost observability

AIM 2.0 should make adoption cost visible.

At startup or Gate B, the runtime should report:

- adoption mode
- footprint level
- whether a repo profile was reused
- profile freshness result
- scan depth
- reason for any profile refresh
- expected review depth
- whether broader docs were avoided

At Gate E, the runtime should report:

- what profile facts were reused
- what was rescanned
- whether review depth matched risk
- whether branch switching changed the profile decision
- whether any context hogs were found

Exact dollar or token accounting is not required for the first implementation path.

## Migration from AIM 1.7

Existing AIM 1.7 repositories should continue to work.

When AIM 2.0 sees existing AIM files, it should classify them:

- runtime: adapter or tool behavior
- repo profile: reusable facts about the repository
- working state: active Epic, increment, gate, and handoff artifacts
- docs: reference material
- adapter helpers: optional platform surfaces

Migration should:

1. preserve current behavior
2. extract reusable repo-profile facts where possible
3. offer Personal, Team, or Managed adoption depth
4. keep Full embedded AIM available by explicit choice

Do not require teams to remove committed AIM docs if they already chose that model.

## Safety rules

Low-footprint AIM is still AIM.

It must preserve:

- `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- Gate A, B, and E semantics
- Done Increment discipline
- ownership boundaries
- escalation rules

If repo profile reuse conflicts with trust, trust wins.

## Next implementation slices

Good follow-up increments:

1. define a tiny committed profile example
2. define local working-state placement for Personal AIM
3. update install docs with Personal and Team AIM paths
4. update adapter guidance with profile reuse expectations
5. add validator checks for profile/state separation

## Related files

- `docs/features/aim-2-enterprise-and-universal-adoption-strategy.md`
- `docs/features/aim-2-repo-profile-and-footprint-model.md`
- `docs/features/aim-cost-comparison.md`
- `docs/workflow/aim-1.7-doc-map.md`
