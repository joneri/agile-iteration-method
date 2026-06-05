# AIM 2.0 Enterprise And Universal Adoption Strategy

## Purpose

Define AIM 2.0 as the release that makes disciplined, repo-aware, cost-aware agentic coding easy to adopt for individuals, teams, and organizations without requiring large repository mutation.

AIM 2.0 should make two promises true:

- users can adopt AIM without committing the whole method into every repository
- if AIM has already learned a repository, that knowledge can be reused without paying the full bootstrap cost again

## User experience

AIM 2.0 should feel simpler than AIM 1.7 at the moment of adoption.

The user should be able to choose one of three modes:

- Personal AIM: use AIM locally with no required commits
- Team AIM: share a small repo profile with a tiny committed footprint
- Managed AIM: use organization-managed policy and reusable profiles

The first-run question should not be "which files do I copy into this repo?"
It should be "how much of AIM should this repo share?"

## The real problem discovered after AIM 1.7

AIM 1.7 improved runtime cost discipline, but large-repo testing exposed a deeper adoption problem.

In a large existing enterprise monorepo:

- downloading and copying AIM files can collide with existing files and folders
- it is not always clear which AIM files are required, optional, adapter-specific, or reference-only
- a single developer may want AIM discipline without permission to commit method docs into the repository
- repo-aware setup can be expensive when it starts with broad repository discovery
- valuable repo adaptation can be lost when work moves between feature branches
- runtime state, repo profile, adapter files, and reference docs still feel too blended

That problem affects enterprise repositories first because the repos are large, protected, and socially complex.
But it is not only an enterprise problem.

Solo developers and small teams also suffer when adoption requires too many copied files, repeated context loading, or unclear separation between "using AIM" and "installing AIM into the repo."

## What AIM 1.7 solved

AIM 1.7 made cost discipline part of the public product story.

It improved:

- progressive context loading
- state-first resume
- compact gates
- cheap validation before broad inspection
- risk-scaled review
- Cost Control, Standard, and Deep as operational cost profiles
- Copilot AI Credits awareness
- treating context hogs and repeated rereads as budget bugs

This was the right release for making AIM cheaper than undisciplined agentic coding during normal work.

## What AIM 1.7 still does not solve

AIM 1.7 still assumes too much coupling between method adoption and repository mutation.

It does not yet make these concerns cleanly separate:

- AIM runtime
- AIM repo profile
- AIM working state
- AIM docs and reference material
- adapter-specific helper surfaces
- reusable repo adaptation

As a result, users can still feel forced to choose between:

- chaotic vibe coding with no shared discipline
- committing a broad AIM documentation and adapter package into a repository they may not own

AIM 2.0 exists to remove that false choice.

## Why AIM 2.0 is needed

AIM 2.0 is needed because the next cost problem is not only how agents behave after work starts.
It is also how much users pay to adopt, bootstrap, rescan, relearn, and move between branches.

If AIM remains expensive to introduce into existing repositories, some users will choose less disciplined agentic coding because it feels easier in the moment.
If AIM repo awareness is not reusable, teams will keep paying the cold-start cost even after AIM has already learned useful facts.

AIM 2.0 should make the disciplined path the easy path:

- easier for one developer to start
- easier for a team to share what AIM learned
- safer for enterprise repositories with existing governance
- cheaper across repeated sessions and branches

## AIM 2.0 positioning

AIM 2.0 is disciplined, repo-aware, cost-aware agentic coding for everyone, with minimal repository mutation and reusable repo intelligence.

It is not only "enterprise-ready without repo takeover."
That is true, but too narrow.

AIM 2.0 should unify:

- personal simplicity
- team sharing
- enterprise safety
- low repository footprint
- reusable repo adaptation
- cheaper cold start
- cost-aware agentic coding

The product should feel smaller to install and stronger to reuse.

## Non-goals

AIM 2.0 should not:

- redesign the AIM core loop
- weaken ownership, gates, Done Increment discipline, or escalation
- require every repository to commit AIM reference docs
- turn every repository into an AIM template repository
- make exact token, dollar, or AI Credit savings claims without measurement
- optimize only for enterprise monorepos
- optimize only for solo local use
- introduce broad platform governance before the adoption model is clear
- treat command examples in this strategy as final syntax

## Layer separation

AIM 2.0 should treat these as separate product layers.

### AIM runtime

The runtime is installed in the tool, adapter, or user environment.

It owns:

- role and gate execution
- cost profile behavior
- startup and resume behavior
- validation
- adapter integration
- local runtime bookkeeping

The runtime should not require every repository to carry the full AIM method docs.

### AIM repo profile

The repo profile is a small reusable representation of how a repository works.

It may include:

- repo structure
- test commands
- build commands
- coding conventions
- ownership boundaries
- risk zones
- deployment constraints
- migration constraints
- adapter-specific notes
- known context hogs

The repo profile can be local, shared, exported, or managed.

### AIM working state

Working state is the resumable state for the current AIM run or feature branch.

It may include:

- active Epic
- active Done Increment
- current gate
- role handoff state
- concise decision and review artifacts
- branch-local assumptions

Working state should be local by default unless a team intentionally chooses to share it.

### AIM docs and reference material

Docs explain AIM.
They are not the same thing as installing AIM.

Reference docs should be available through:

- the AIM repository
- installed adapter packages
- generated help
- links from a small repo profile

They should not be copied wholesale into every repository by default.

## Adoption modes

### Personal AIM

Personal AIM is for one developer.

Default behavior:

- no commits required
- local runtime
- local working state
- local repo profile
- no repository mutation required by default

Personal AIM is the right starting point when:

- the developer does not own the repository
- the repository is protected or high-friction
- the user wants to compare AIM against normal agentic coding
- the team has not yet agreed to adopt AIM

Personal AIM must preserve repo-aware benefits by saving reusable local repo intelligence instead of forcing repeated cold starts.

### Team AIM

Team AIM is for shared repo adaptation with minimal footprint.

Default behavior:

- tiny committed profile surface
- shared repo profile
- runtime not fully embedded in the repo
- lightweight onboarding for teammates

The committed footprint should be small enough to review as repository metadata, not a method takeover.

The team profile should answer:

- how this repo is built and tested
- which areas are risky
- what conventions matter
- where AIM working state should live
- which adapters are allowed or discouraged

### Managed AIM

Managed AIM is for organization-wide standardization.

Default behavior:

- central policy
- shared profile registry
- reusable repo adaptation
- optional governance and integration layers

Managed AIM should help organizations standardize without requiring every repository to duplicate the same method package.

It may later support:

- approved adapter lists
- profile registry
- policy inheritance
- budget rules
- audit exports
- integration with internal developer platforms

Those are later implementation concerns, not requirements for the first AIM 2.0 strategy increment.

## Footprint rules

AIM 2.0 should define repository footprint levels.

### Zero-footprint use

No committed AIM files are required.

Use this for Personal AIM and early evaluation.

Allowed locations may include:

- local user config
- adapter storage
- ignored local `.aim/` state
- external workspace storage
- `.git/info/exclude` for local runtime artifacts

### Tiny-footprint use

One or two small committed files may describe the repository profile or point to a shared profile.

Use this for Team AIM.

The tiny footprint should avoid copying full method docs.

### Full embedded use

The repository may carry full AIM docs and adapter helper files only when the repo owner intentionally chooses that model.

This remains valid for method repositories, templates, open-source examples, or teams that want AIM fully visible in the repo.

Full embedded use must not be the default adoption path.

## Locality-first repo awareness

AIM 2.0 should make repo-aware setup locality-first, not repo-wide-first.

At startup, AIM should prefer:

1. existing working state
2. existing repo profile
3. directly affected files
4. nearest package or module metadata
5. local tests and scripts for the affected area
6. broader repository docs only when risk or missing evidence requires them

Large monorepos should not pay for full repository discovery when the active work touches one package, service, component, or domain.

Locality-first does not mean shallow.
It means AIM expands only when the approved increment, trust risk, or missing evidence justifies the cost.

## Reusable repo adaptation

Repo adaptation should become a reusable asset.

If AIM has already learned these facts:

- repo structure
- test commands
- coding conventions
- risk zones
- ownership boundaries
- deployment constraints
- migration constraints
- common validation paths

then AIM should be able to reuse that intelligence across:

- branches
- sessions
- developers, when shared intentionally
- adapters, when profile format allows
- future Done Increments

Reusable repo adaptation should include freshness rules.

A profile is useful only if AIM can tell when it may be stale.
Examples:

- lockfile changed
- package scripts changed
- test framework changed
- ownership file changed
- profile timestamp is old
- branch differs from the profile base
- user or repo policy requires revalidation

## Cost observability

AIM 2.0 should extend AIM 1.7 cost discipline beyond the work session itself.

Cost should be visible across:

- install
- scanning
- startup
- resume
- review
- branch switching
- subagent use
- repo profile refresh

AIM 2.0 should help users answer:

- did we reuse known repo intelligence?
- what did we rescan and why?
- did the scope justify the scan depth?
- did review depth match risk?
- did subagents save cost or add overhead?
- did branch switching reuse the profile safely?

The goal is not exact price accounting in the first strategy.
The goal is observable cost discipline: users should see when AIM is avoiding repeat token burn and when it must spend more for safety.

## Possible command direction

These command shapes are strategic direction, not final syntax.

Personal AIM might feel like:

```text
aim init --personal
aim scan repo
aim save-profile
aim start
```

Team AIM might feel like:

```text
aim init --team
aim profile export
```

Managed AIM might later feel like:

```text
aim profile attach <managed-profile>
aim policy check
```

The important design point is not the exact command names.
The important design point is that install, scan, profile reuse, and start are separate actions.

## Migration direction from AIM 1.7

AIM 2.0 should not break AIM 1.7 repositories.

Migration should be additive:

1. Detect existing AIM 1.7 files.
2. Classify them as runtime, repo profile, working state, docs, or adapter helpers.
3. Preserve current behavior.
4. Offer to extract reusable repo profile facts.
5. Offer Personal, Team, or Managed mode.
6. Keep full embedded AIM as a supported option.

For repositories that already committed AIM docs, AIM 2.0 should not require removal.
It should make the smaller model available for new repos and future simplification.

## Key decisions

- AIM 2.0 is universal, not enterprise-only.
- Repository mutation is optional adoption depth, not the definition of using AIM.
- Repo profiles are reusable product assets.
- Working state is branch/run-local by default.
- Reference docs belong in AIM distribution surfaces, not automatically in every repository.
- Cold start should be locality-first.
- Cost discipline includes setup and profile refresh, not only coding and review.
- AIM core role order, gates, ownership, and escalation stay unchanged.

## Inputs and outputs

- Inputs:
  - user adoption mode
  - repository size and structure
  - available local or shared repo profile
  - current branch and task scope
  - adapter capabilities
  - repo policy and trust constraints

- Outputs:
  - selected adoption mode
  - selected footprint level
  - local or shared repo profile
  - resumable working state
  - locality-first scan plan
  - visible cost and freshness assumptions

## Defaults and fallbacks

- Default adoption mode: Personal AIM when repo ownership is unclear.
- Default footprint: zero-footprint until the user or team chooses otherwise.
- Default repo awareness: reuse existing profile before scanning.
- Default scan behavior: locality-first.
- Default sharing: local-only unless the team intentionally exports a profile.
- Fallback when no profile exists: create a minimal local profile from directly relevant files and commands.
- Fallback when profile freshness is uncertain: revalidate the smallest affected area first.
- Fallback when policy conflicts are detected: stop and escalate instead of guessing.

## Edge cases

- Some repositories should still embed AIM fully, especially AIM itself, templates, and public examples.
- Some organizations may require committed policy for audit reasons.
- Some work requires broad discovery because the risk is real.
- Some repo profiles will become stale and must be refreshed.
- A personal local profile must not leak proprietary information into public commits.
- Shared profiles need ownership and review rules.

## Data correctness and trust

AIM 2.0 must not trade trust for lower footprint.

The runtime must still preserve:

- PO ownership of Epic intent
- TDO ownership of Done Increment scope
- Dev responsibility for implementation within approved scope
- Reviewer responsibility for risk and correctness review
- Gate A, B, and E approval semantics
- escalation on unclear intent, trust risk, data correctness risk, security, migration, deployment, or policy conflict

Low-footprint AIM is still AIM.
It changes where knowledge lives, not who owns decisions.

## Debugging

The single best check is whether AIM reused the smallest trustworthy source before expanding context.

- Primary log: the startup or Gate B context-source summary
- What good looks like:
  - AIM states the selected adoption mode
  - AIM states whether a repo profile was reused
  - AIM states what local area was scanned
  - AIM states why any broader scan was needed
  - AIM keeps working state out of commits unless intentionally shared
- What bad looks like:
  - AIM asks users to copy many files before proving value
  - AIM rereads broad docs on every branch
  - AIM loses repo adaptation between sessions
  - AIM cannot explain what it scanned or why
  - AIM treats "using AIM" and "committing AIM docs" as the same thing

## Related files

- `AGENTS.md`
- `docs/features/aim-2-repo-profile-and-footprint-model.md`
- `docs/features/aim-cost-comparison.md`
- `docs/features/aim-cost-control-mode.md`
- `docs/features/aim-cost-saving-method.md`
- `docs/features/aim-github-copilot-cost-reduction-playbook.md`
- `docs/features/aim-modularity-context-efficiency.md`
- `docs/workflow/quick-start-aim-1.7.md`
- `docs/workflow/install-aim-1.7.md`

## Change log

- 2026-06-04: Linked the concrete repo profile and footprint model.
- 2026-06-04: Initial AIM 2.0 strategy for universal, low-footprint, reusable repo-aware adoption.
