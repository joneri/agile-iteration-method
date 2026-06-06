> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 low-footprint adoption

Use this guide when you want the AIM 2.0 adoption model without copying the full AIM method package into a repository.

AIM 2.0 is not released as a final runtime yet.
This guide defines the practical product path that future runtime and installer work should follow.

## What changes in AIM 2.0

AIM 2.0 separates four things that older embedded AIM docs blended too much:

- AIM runtime: how the loop runs
- AIM repo profile: reusable knowledge about the repository
- AIM working state: the current Epic, increment, gate, and handoff state
- AIM docs: reference material

Using AIM should not require committing all AIM docs and adapter files into every repository.

## Choose an operating mode

### Personal AIM

Use Personal AIM when one developer wants AIM discipline without repository mutation.

Default behavior:

- no committed AIM files
- local runtime from the tool or adapter
- local working state
- local repo profile at `~/.aim/profiles/<repo-fingerprint>/profile.yaml`
- AIM docs read from the installed package or canonical AIM repository

Best for:

- trying AIM in a large existing repo
- protected enterprise repos
- feature branches where the developer does not own repository policy
- comparing AIM against normal agentic coding

### Team AIM

Use Team AIM when a team wants to share repo adaptation without copying the full method.

Default behavior:

- root `aim.profile.yaml` as a tiny committed profile surface or pointer
- shared repo profile facts
- local working state by default
- runtime still supplied by the tool or adapter
- AIM docs linked, not copied wholesale

Best for:

- shared commands and validation paths
- known risk zones
- team coding conventions
- avoiding repeated cold-start scans across teammates

### Enterprise AIM

Use Enterprise AIM when safe isolation is the default and AIM-internal artifacts must not be committed or pushed by accident.

Default behavior:

- approved runtime or adapter
- local/private working state and repo-awareness by default
- Enterprise ignore baseline for AIM-internal artifacts
- shared profile registry or policy pointer only by explicit approval
- no overwrite assumptions for root instruction files

Enterprise AIM should not block Personal AIM or Team AIM.
It is the stricter safety mode, not a requirement for ordinary adoption.

### Full embedded AIM

Use Full embedded AIM only when the repo owner intentionally wants AIM inside the repo.

Best for:

- AIM itself
- templates
- training repositories
- public examples

Full embedded AIM remains valid, but it is a footprint choice rather than an operating mode.

## Where things live

| Layer | Personal AIM | Team AIM | Enterprise AIM |
| --- | --- | --- | --- |
| Runtime | tool or local adapter | tool or local adapter | approved local or org adapter |
| Repo profile | `~/.aim/profiles/<repo-fingerprint>/profile.yaml` | root `aim.profile.yaml` profile or pointer | local/private by default; governed shared profile only by approval |
| Working state | local or user-chosen | local by default | local/private and ignored by default |
| Docs | installed package or links | installed package, links, or reviewed shared docs | installed package, canonical links, or approved internal package |

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
2. create or reuse `~/.aim/profiles/<repo-fingerprint>/profile.yaml`
3. create local working state
4. scan only the affected area first
5. load broader docs only when risk requires it

Adapter fallback:

```text
.aim/profile.yaml
```

Use the fallback only when the adapter cannot use the user-level profile store.
It remains local because `.aim/` is ignored.

### Team start

```text
aim init --team
aim profile export --tiny
aim start "EPIC: <goal>"
```

Until a final CLI exists, the concrete Team AIM artifact is:

```text
aim.profile.yaml
```

What the runtime should do:

1. create or reuse root `aim.profile.yaml` as a small shared repo profile or pointer
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
2. Team AIM profile, normally root `aim.profile.yaml`
3. compatible Personal AIM local profile hints when present
4. directly affected files
5. nearest package, service, or module metadata
6. nearest commands for build, test, lint, or validation
7. short authoritative docs named by the profile
8. broader repository docs only when risk or missing evidence requires them

This is the main cold-start cost reduction.

AIM should not scan a large monorepo broadly when the work is local, low-risk, and covered by a fresh profile.

For Team AIM, profile-first startup means:

- read `.aim/state.json` first when it exists
- read `aim.profile.yaml` before broader workflow or adapter docs
- use profile locality and command hints to plan the smallest safe scan
- use profile `shortAuthoritativeDocs` only when needed
- use profile `avoidByDefault` and `knownContextHogs` as budget guidance
- escalate when profile freshness, trust, or current repo evidence is uncertain

For Personal AIM, profile-first startup means:

- read `.aim/state.json` first when it exists
- read `~/.aim/profiles/<repo-fingerprint>/profile.yaml` next when it exists
- fall back to ignored `.aim/profile.yaml` only when user-level storage is unavailable
- reuse profile facts across branches after a freshness check
- keep personal profile facts out of commits
- layer personal hints over the Team profile only when they do not contradict shared commands, ownership, risk, or policy

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
- what profile facts were reused
- profile freshness result
- scan depth
- selected locality
- reason for any profile refresh
- broader docs or scans avoided
- expansion reason when broader context is loaded
- expected review depth
- whether broader docs were avoided

At Gate E, the runtime should report:

- what profile facts were reused
- what was rescanned
- whether review depth matched risk
- whether branch switching changed the profile decision
- whether any context hogs were found

Exact dollar or token accounting is not required for the first implementation path.

## Migration from older embedded AIM repositories

Existing embedded AIM repositories should continue to work.

When AIM 2.0 sees existing AIM files, it should classify them:

- runtime: adapter or tool behavior
- repo profile: reusable facts about the repository
- working state: active Epic, increment, gate, and handoff artifacts
- docs: reference material
- adapter helpers: optional platform surfaces

Migration should:

1. preserve current behavior
2. extract reusable repo-profile facts where possible
3. offer Personal, Team, or Enterprise operating mode
4. keep Full embedded AIM available as an explicit footprint choice

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

1. make a runtime helper emit the profile-source summary from personal and team profile sources
3. prepare README/front-door wording when AIM 2.0 release scope is clearer

For the concrete tiny Team AIM profile artifact, see [AIM 2.0 tiny Team profile artifact](team-profile-artifact.md).
For Personal AIM local storage, see [AIM 2.0 Personal local profile storage](personal-local-profile-storage.md).
For the compact startup/Gate B summary, see [AIM 2.0 profile source summary](profile-source-summary.md).
For active state boundaries, see [AIM 2.0 working-state boundaries](working-state-boundaries.md).

## Related files

- `docs/workflow/repo-profile-and-footprint-model.md`
- `docs/workflow/team-profile-artifact.md`
- `docs/workflow/working-state-boundaries.md`
- `docs/features/aim-cost-comparison.md`
- `docs/workflow/quick-start-aim-2.0.md`
