# AIM feature guide

This is the short map of what AIM 3.1 does. Follow the links only when you need
the operating detail.

Returning from early 3.0? AIM UI combines clearer workflows with preserved work,
action tracking and verified recovery status. Across Codex, Claude Code and
GitHub Copilot, AIM keeps the same command semantics and resumes saved work when
the next tool has AIM and access to the same current repository and state.
Discuss lets you explore ideas without changing code or starting delivery.
Verified repository knowledge helps each session build on what is already known;
it does not replace checking relevant code or guarantee whole-repository coverage.

## Delivery loop

- Epics describe outcomes.
- One Done Increment is active at a time.
- PO, TDO, Dev, and Reviewer keep planning, implementation, review, validation,
  and acceptance separate.
- Gate A approves the Epic, Gate B approves the increment, and Gate E accepts
  the result.
- Failed review or validation returns the increment for correction.

See the [canonical AIM method](../workflow/agile-iteration-method.md).

## Audience-context integrity

- Generated artifacts communicate their intended current meaning directly.
- Private conversations, rejected drafts, AI mistakes, prompts, and review
  feedback stay out of product copy, UI labels, code comments, and docs.
- Changelogs, decision records, and other intentionally historical artifacts
  retain the history their audience needs.

This makes AIM audience-aware from the first generated artifact. See the
[canonical principle](../workflow/agile-iteration-method.md#audience-context-integrity).

## Control and cost

- `Strict` pauses at all hard gates.
- `Auto` continues until risk, changed scope, uncertainty, or final acceptance
  requires a person.
- `Standard`, `Cost Control`, and `Deep` change context and verification depth;
  they never remove roles, gates, or escalation.

See [cost profiles](../workflow/cost-control-mode.md).

## AIM UI

- `/aim ui` starts or reopens the current repository's local control room;
  `start`, `open`, `status`, and `stop` also accept an explicit repo path.
- Source, adaptive, and public Agent Skill distributions carry the same trusted
  launcher, and a new repo can open truthful onboarding without creating
  `.aim`.
- AIM UI Beta projects several independently authoritative Epic workspaces and
  their Increments into one live five-column Kanban.
- Delivery flow is the primary surface; portfolio summaries, People and agents,
  and complete Closed Increment history live in dedicated tabs.
- The header identifies the exact AIM product release captured when the local
  server started, separately from repository runtime-contract versions.
- Connected Codex control shows whether eligible Start and Approve actions can
  continue in the authoritative task; View-only mode explains setup and keeps a
  reviewed handoff available.
- The Portfolio view teaches the ordered calibration, Discuss, explicit
  Roadmap promotion, review, Portfolio Auto, and mandate journey with a
  state-aware next command.
- The main AIM chat owns portfolio capacity, focus, backlog planning, activation,
  Gates, and runtime state.
- Every card retains its Epic identity and separates canonical role ownership
  from optional bounded helper-agent activity.
- Auto mode appears as automatic card movement because the UI polls canonical
  runtime evidence; the UI itself cannot advance a gate or write `.aim` state.
- Polling stays visually quiet and only genuine workflow movement is animated.
- When connected, eligible Activate and Approve actions dispatch exact,
  freshness-checked intents to the same Codex task. Change and free-form paths
  remain reviewed handoffs; decision buttons appear only after AIM publishes a
  ready handoff.
- Existing single-Epic state remains compatible without migration.

See [AIM UI Beta](aim-ui.md).

## Discuss

- `/aim discuss [question]` explores product direction, architecture,
  tradeoffs, and recent delivery without starting work.
- Explicit skill invocation and plain-language discussion requests preserve the
  same read-only behavior across Codex, Claude Code, and GitHub Copilot.
- AIM selects only relevant repository profile, runtime, decision, delivery,
  code, documentation, and method context under the repository trust boundary.
- Discuss never changes source, `.aim`, Backlog, profiles, durable knowledge,
  Epics, Increments, or Gates.
- AIM UI is an optional visual entry point to the same command contract.
- A conclusion may recommend one separate promotion action but cannot execute
  it.

See the [adapter command contract](../workflow/adapter-command-contract.md#aim-discuss).

## Repository knowledge

- `/aim calibrate-repo` verifies commands, technologies, important areas, and risk.
- `/aim remember-repo` and `/aim forget-repo` maintain reusable facts.
- `aim.profile.yaml` stores compact shared knowledge.
- User hints and protected external memory remain outside the repository.
- `.aim/` stores active work, never durable repository truth.

See [repo awareness](../workflow/repo-awareness.md).

## Reflect

- `/aim reflect` turns completed work in the current AIM project into verified
  knowledge candidates.
- `/aim reflect-all` previews and synthesizes a selected set of local AIM
  projects without changing any of them.
- Candidates carry provenance, current-evidence verification, confidence,
  contradictions, classification, destination, and a promotion action.
- Each completed reflection says whether action is recommended, assigns every
  candidate a disposition, and supplies one concrete next action or an explicit
  no-action conclusion.
- Reports remain temporary under `.aim/analysis/`; durable knowledge changes
  require a separate reviewed promotion.
- Reflect goes beyond memory cleanup for repository work by combining
  consolidation with current-source verification and human-owned promotion.

See [AIM Reflect](../workflow/reflection.md).

## Project specialists and skill matching

- `aim.roles.yaml` defines project-specific expertise for PO, TDO, Dev, and Reviewer.
- Each role has bundled engineering instructions. Additional skills must resolve
  to actual available instructions; a proposed skill is not an installed capability.
- `/aim configure-agents` uses repository evidence to preview affected role and
  supplier-native file updates, preserving user overrides and active work.
- Empty projects can start with provisional skill suggestions from requirements,
  then verify them against the chosen stack.
- Reuse unchanged bindings and update only the roles affected by new evidence.

See [project-agent configuration](../workflow/project-agent-configuration.md).

## Adaptive agent allocation and independent review

- Assign activities according to dependency boundaries, risk and available
  capacity. Parallel implementation requires disjoint ownership and settled interfaces.
- Material changes normally receive a separate permitted reviewer who did not
  implement them. A role switch in the same session is identified as self-review.
- Review evidence covers the actual changed files and their current versions.
  A new edit invalidates affected old evidence.
- Genuinely nonmaterial, understood changes may use an explicit self-review
  exception with direct checks; uncertain or material impact retains separate review.
- Native agent availability and permissions still govern execution. The main
  session owns integration, runtime state and user acceptance; helpers never
  create an independent AIM runtime or grant themselves permission.

See [adaptive execution](../workflow/adaptive-execution.md).

## Scoped knowledge and engineering evidence

- Calibration names what was inspected; a ready locality is not a whole-repo guarantee.
- Reused claims retain sources, scope, freshness and known contradictions.
  Matching file hashes do not certify factual truth.
- Reflection may recommend a focused update, regression check or no action.
  Verified lessons are promoted only within the user's authorization.
- Engineering guidance targets actual failure boundaries and equivalent resource
  workloads. Mixed setup, repository maintenance and delivery time remain visible.

See [engineering delivery](../workflow/engineering-delivery.md) and the
[bounded evaluation results](../features/aim-3.1-evaluation.md).

## Adapters and commands

Codex, Claude Code, and GitHub Copilot each receive a native AIM skill. All map
the same command family:

`start`, `continue`, `status`, `validate`, `help`, `config`, `discuss`,
`configure-agents`, `calibrate-repo`, `remember-repo`, `forget-repo`,
`reflect`, `reflect-all`, `upgrade`, `mode`, `cost`, and `replan`.

If native routing is unavailable, explicit AIM intent preserves the same
semantics. See the [adapter entry model](../workflow/adapter-entry-model.md).

## Installation and upgrades

- The complete, self-contained public Agent Skill installs through
  `npx skills add joneri/agile-iteration-method --skill agile-iteration-method`.
- The public package is generated from canonical AIM sources and is not AIM Lite.
- One adaptive guided installer handles repository-aware setup.
- Footprints control where files may be written.
- Plans classify create, current, and collision states before apply.
- Apply is rollback-protected and safe to rerun.
- Adapter readiness receipts name skill paths, reload steps, and fallbacks.
- `/aim upgrade` refreshes AIM-owned packages without rewriting active state.

See [public Agent Skill distribution](../workflow/version-and-installation.md)
and [adaptive installation](../workflow/install-aim-2.0.md).

## Validation and release safety

- Structural, behavioral, product-coherence, and release-readiness checks are separate.
- Clean-room package closure verifies installed references.
- Documentation links, product versions, feature coverage, and website structure
  are release checks.
- Publication builds a deterministic Pages artifact before deployment.

See [release and publication](../workflow/release-publication-model.md).
