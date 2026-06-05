# AIM 2.0 Repo Profile And Footprint Model

## Purpose

Define the first concrete AIM 2.0 model for low-footprint adoption and reusable repo intelligence.

This model turns the AIM 2.0 strategy into a practical product surface:

- Personal AIM can run without committed AIM files.
- Team AIM can share repo adaptation through a tiny committed profile surface.
- Managed AIM can later attach organization policy and shared profile registries.
- Repo-aware context can be reused across branches and sessions without repeating broad cold-start scans.

## User experience

AIM 2.0 should start by asking how much the repository should share, not which AIM files should be copied.

The user-facing adoption depths are:

| Mode | Default footprint | Primary user | Shared by default | Best for |
| --- | --- | --- | --- | --- |
| Personal AIM | zero-footprint | one developer | no | trying AIM, protected repos, personal feature work |
| Team AIM | tiny-footprint | one team | yes, intentionally | shared repo conventions and validation paths |
| Managed AIM | managed footprint | organization | yes, governed | standard policy, profile registry, larger rollout |
| Full embedded AIM | full repository footprint | repo owner | yes | AIM itself, templates, public examples |

Personal and Team AIM are first-class product modes.
Managed AIM is a direction that should remain possible without making simple adoption heavy.

## How it works

AIM 2.0 separates four layers.

### AIM runtime

The runtime lives in the tool, adapter, or user environment.

It owns:

- role and gate execution
- mode and cost-profile behavior
- startup and resume rules
- validation
- local runtime bookkeeping

The runtime is not copied wholesale into every repository by default.

### AIM repo profile

The repo profile is reusable repo intelligence.

It describes how this repository works, independent of any one Epic or branch.

For Team AIM, the default tiny artifact is:

```text
aim.profile.yaml
```

It lives at the repository root and may either contain the small shared profile directly or point to managed/internal profile storage.

For Personal AIM, the default local artifact is outside the repository:

```text
~/.aim/profiles/<repo-fingerprint>/profile.yaml
```

The ignored repo-local fallback is:

```text
.aim/profile.yaml
```

The smallest useful profile should capture:

- repo identity and profile version
- adoption mode and footprint level
- profile storage location and sharing intent
- package, service, or module boundaries
- build, test, lint, and validation commands
- coding conventions and local norms
- ownership boundaries
- risk zones
- migration, deployment, and security constraints
- known context hogs
- locality-first discovery hints
- freshness markers
- cost-observability hints

### AIM working state

Working state is branch/run-local execution state.

It includes:

- active Epic
- active Done Increment
- current gate
- role handoff state
- concise decisions and review artifacts
- branch-local assumptions

Working state should not be shared by default.
Sharing active state is a team decision, not a requirement for using AIM.

### AIM docs and reference material

AIM docs explain the method.

They should be available through the AIM repository, installed adapter package, generated help, or links from a repo profile.

They should not be copied into every repository by default.

## Repo profile shape

This is the first practical model, not a final file format.

Future implementations may express it as Markdown, JSON, YAML, or adapter-managed storage.
The semantic sections should remain stable.

```text
aimRepoProfile:
  profileVersion:
  repoIdentity:
    name:
    root:
    remote:
    defaultBranch:
  adoption:
    mode: personal | team | managed | full-embedded
    footprint: zero | tiny | managed | full
    sharing: local | committed | registry
    profileOwner:
  storage:
    runtimeLocation:
    profileLocation:
    workingStateLocation:
    docsSource:
  locality:
    primaryAreas:
    packageBoundaries:
    nearestMetadata:
    defaultDiscoveryOrder:
  commands:
    install:
    build:
    test:
    lint:
    typecheck:
    validate:
  conventions:
    codeStyle:
    docs:
    branching:
    review:
  risk:
    highRiskAreas:
    migrationRules:
    deploymentRules:
    securityRules:
    dataCorrectnessRules:
  ownership:
    owners:
    approvalNotes:
  context:
    knownContextHogs:
    shortAuthoritativeDocs:
    avoidByDefault:
  freshness:
    generatedAt:
    baseBranch:
    baseCommit:
    refreshTriggers:
    lastValidated:
  cost:
    startupBudget:
    scanDepth:
    reusedProfile:
    refreshReason:
    reviewDepth:
    subagentPolicy:
```

## Storage and footprint rules

### Personal AIM

Default storage:

- runtime: installed tool or local adapter
- repo profile: `~/.aim/profiles/<repo-fingerprint>/profile.yaml`
- working state: local and ignored
- docs: AIM distribution or links

Repository mutation:

- none required by default

Fallback storage:

- `.aim/profile.yaml` only when the adapter cannot use the user-level profile store
- fallback remains ignored by the repository-level `/.aim` rule

Use this when:

- the developer does not own the repo
- the repo is protected
- the team has not adopted AIM
- the user wants a cheap first trial

### Team AIM

Default storage:

- runtime: installed tool or local adapter
- repo profile: root `aim.profile.yaml` as a tiny committed profile or pointer
- working state: local by default
- docs: AIM distribution or links

Repository mutation:

- one small `aim.profile.yaml` profile surface, or one small pointer to shared profile storage

Use this when:

- teammates should reuse commands, conventions, risk zones, and validation paths
- the team wants shared AIM behavior without copying full docs
- adoption should be reviewable as repo metadata

The Team AIM profile must not contain active Epic state, current Done Increment state, gate approval state, review findings for one branch, secrets, or copied AIM reference docs.

When both Personal and Team profiles exist, use Personal profile facts as local reuse hints and Team profile facts as the shared baseline.
Personal facts must not silently contradict Team commands, ownership, risk, or policy.

### Managed AIM

Default storage:

- runtime: approved adapter or organization environment
- repo profile: managed registry or governed shared profile
- working state: local or approved team storage
- docs: managed distribution or canonical links

Repository mutation:

- optional pointer to managed policy/profile

Use this when:

- an organization needs central policy
- repo profiles need ownership and lifecycle rules
- shared profiles need governance

Managed AIM is not required for AIM 2.0 to be useful.

### Full embedded AIM

Default storage:

- runtime: repository docs and adapter helpers may be included
- repo profile: committed
- working state: still local or runtime-owned unless intentionally shared
- docs: committed

Repository mutation:

- full AIM footprint by explicit repo-owner choice

Use this for:

- AIM itself
- templates
- training repos
- public examples
- repos that intentionally want AIM fully visible

Full embedded use remains supported, but it is not the default definition of adoption.

## Locality-first discovery

AIM 2.0 startup should expand context in this order:

1. current working state
2. personal local profile when present
3. reusable team repo profile, normally root `aim.profile.yaml`
4. directly affected files
5. nearest package, module, or service metadata
6. nearest build/test/lint commands
7. short authoritative repo docs named by the profile
8. broader repository docs only when risk or missing evidence requires them

This keeps large repositories from paying for repo-wide rediscovery when the active work is local and low-risk.

Operational startup behavior:

- read `.aim/state.json` first when it exists
- read the Personal AIM local profile next when it exists
- read `aim.profile.yaml` after the personal profile when it exists
- use the profile to select locality, commands, short authoritative docs, risk zones, freshness checks, and avoid-by-default context
- read broader docs only after profile/state evidence shows they are needed
- report profile reuse and avoided broad context at startup or Gate B

Escalate discovery depth when:

- the profile is missing or stale
- the affected area crosses ownership boundaries
- migrations, deployment, security, data correctness, or public API behavior are involved
- commands or conventions are contradictory
- Gate B cannot define a safe Done Increment from local evidence

## Reuse and freshness rules

Reusable repo intelligence must be safe enough to trust.

Before AIM treats a profile as reusable, the validator should report repo-profile readiness.

Repo-profile readiness has four states:

- `not_ready`: no AIM 2.0 profile artifact exists yet; `AGENTS.md` can still bridge runtime behavior, but Personal/Team profile reuse is not ready.
- `incomplete_profile`: a profile file exists, but it does not yet contain recognizable repo intelligence such as commands, locality, ownership, risk, freshness, or cost fields.
- `repair_profile`: a profile file exists, but it appears to contain active AIM working state and must be repaired before reuse.
- `profile_ready`: a profile file exists, contains repo-intelligence markers, and does not contain active working-state markers.

AIM may reuse a profile when:

- profile ownership is clear
- the profile applies to the current repo identity
- branch or base commit differences are understood
- the validator reports `profile_ready`
- no refresh trigger has fired
- the active work is inside a known locality boundary
- the selected cost profile allows profile reuse

AIM should refresh or revalidate the smallest affected area when:

- lockfiles changed
- package scripts changed
- test framework or build tooling changed
- ownership metadata changed
- relevant docs changed
- the profile is older than the team threshold
- current branch differs materially from the profile base
- the user asks for Deep or trust-sensitive work

Profile refresh should be partial by default.
Do not rescan the whole repository when one package-level check is enough.

## Cost observability

AIM 2.0 should explain the main cost drivers without pretending to provide exact price accounting.

At startup or Gate B, AIM should be able to report:

- adoption mode
- footprint level
- whether a repo profile was reused
- what profile facts were reused
- profile freshness result
- scan depth used
- locality selected from the profile or current task
- reason for any profile refresh
- docs or scans avoided because the profile was enough
- review depth expected
- whether subagents are disabled, allowed, or escalated
- which docs or areas were intentionally avoided

At Gate E, AIM should be able to report:

- what repo intelligence was reused
- what had to be rescanned
- whether review depth matched risk
- whether branch switching caused profile refresh
- whether any context hogs were found

## Inputs and outputs

- Inputs:
  - adoption mode
  - repository identity
  - current branch
  - current task scope
  - existing repo profile, if any
  - active working state, if any
  - cost profile
  - repo policy and trust constraints

- Outputs:
  - selected footprint level
  - repo profile or profile pointer
  - working-state location
  - locality-first scan plan
  - freshness decision
  - visible cost-observability summary

## Key decisions

- Repo profile is a product asset, not a one-run note.
- Working state is not the repo profile.
- Runtime is not repository documentation.
- Docs are reference material, not mandatory install payload.
- Personal AIM defaults to zero committed files.
- Team AIM defaults to a tiny shared profile surface.
- Managed AIM stays possible without making Personal AIM heavy.
- Full embedded AIM remains valid only by explicit repo-owner choice.

## Defaults and fallbacks

- Default adoption mode: Personal AIM when ownership is unclear.
- Default footprint: zero-footprint.
- Default profile sharing: local-only.
- Default working state: local and ignored.
- Default discovery: locality-first.
- Default cost reporting: short startup or Gate B summary.
- Fallback if no profile exists: report `not_ready`, then create a minimal local profile from directly affected files and nearest commands when profile reuse is needed.
- Fallback if a profile is incomplete: report `incomplete_profile` and add the smallest missing repo-intelligence sections before relying on reuse.
- Fallback if a profile contains active state: report `repair_profile` and move active Epic, gate, role, review, or acceptance state back to `.aim` working-state artifacts.
- Fallback if profile is stale: refresh the smallest affected locality.
- Fallback if policy conflicts: stop and escalate before continuing.
- Fallback if a team wants sharing: export or commit only the tiny profile surface, not full AIM docs.
- Team AIM artifact: use root `aim.profile.yaml` unless a managed policy explicitly chooses another pointer path.
- Personal AIM artifact: use `~/.aim/profiles/<repo-fingerprint>/profile.yaml`; use `.aim/profile.yaml` only as an ignored adapter fallback.

## Edge cases

- A repo may intentionally use full embedded AIM.
- A security-sensitive repo may forbid local profile persistence.
- A managed organization may require profile storage outside developer machines.
- A stale profile may be more dangerous than no profile.
- A profile can accidentally leak proprietary architecture if exported publicly.
- Cross-cutting work may legitimately require broad discovery.

## Data correctness and trust

Low footprint must not weaken AIM.

The model preserves:

- PO ownership of Epic intent
- TDO ownership of Done Increment scope
- Dev ownership of implementation inside approved scope
- Reviewer ownership of correctness and risk review
- Gate A, B, and E semantics
- escalation on trust, data correctness, security, migration, deployment, public API, unclear scope, or policy conflict

If profile reuse conflicts with trust, trust wins.

## Debugging

The single best check is whether AIM can answer:

> What did you reuse, where did it come from, and why was it fresh enough?

- Primary log: startup or Gate B profile-source summary
- Validator check: `AIM 2.0 repo profile readiness`
- Summary shape: [AIM 2.0 profile source summary](aim-2-profile-source-summary.md)
- What "good" looks like:
  - adoption mode is explicit
  - footprint level is explicit
  - profile location is explicit
  - working-state location is explicit
  - reused repo facts are listed briefly
  - refresh reason is stated when scanning expands
- What "bad" looks like:
  - AIM asks users to copy full docs before proving value
  - AIM rereads broad docs on every branch
  - AIM cannot distinguish profile from working state
  - AIM shares local state accidentally
  - AIM trusts stale repo facts without a freshness check

## Related files

- `docs/features/aim-2-enterprise-and-universal-adoption-strategy.md`
- `docs/features/aim-2-migration-classification-checks.md`
- `docs/features/aim-2-personal-local-profile-storage.md`
- `docs/features/aim-2-profile-source-summary.md`
- `docs/features/aim-2-tiny-team-profile-example.md`
- `docs/features/aim-2-working-state-boundaries.md`
- `docs/features/aim-cost-comparison.md`
- `docs/features/aim-cost-control-mode.md`
- `docs/features/aim-cost-saving-method.md`
- `docs/features/aim-modularity-context-efficiency.md`
- `docs/workflow/install-aim-2.0.md`
- `docs/workflow/quick-start-aim-2.0.md`

## Change log

- 2026-06-05: Added profile-first startup behavior so adapters consume `aim.profile.yaml` before broader docs.
- 2026-06-05: Linked the compact startup/Gate B profile-source summary.
- 2026-06-05: Added Personal AIM local profile storage path and Team profile layering rules.
- 2026-06-05: Defined root `aim.profile.yaml` as the concrete tiny Team AIM profile artifact/pointer.
- 2026-06-05: Added repo-profile readiness states for validator-backed Personal/Team profile reuse.
- 2026-06-05: Linked the tiny Team AIM profile example.
- 2026-06-05: Linked the working-state boundary model.
- 2026-06-05: Linked current migration classification checks.
- 2026-06-04: Initial concrete AIM 2.0 repo profile and footprint model.
