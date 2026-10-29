# AIM feature guide

This is the short map of what AIM does. Follow the links only when you need
the operating detail.

AIM combines clearer workflows with preserved work,
action tracking and verified recovery status. Across Codex, Claude Code and
GitHub Copilot, AIM keeps the same command semantics and resumes saved work when
the next tool has AIM and access to the same current repository and state.
Discuss lets you explore ideas without changing code or starting delivery.
Verified repository knowledge helps each session build on what is already known;
it does not replace checking relevant code or guarantee whole-repository coverage.

## Delivery loop

- Ship is the default: complete the agreed product before final acceptance.
- Choose Loop for useful Done Increments with recurring owner feedback.
- Recommend Graph engineering to connect ownership, dependencies and proof.
- Start with intent; PO discovers one or more Epics and their user perspectives.
- PO owns Epics and product priority; TDO owns User Stories, criteria and the coherent increment.
- Each Story has an identity and lifecycle independent of its delivery plan.
- TDO selects ready Stories across Epics and plans implementation and verification.
- Dev, Reviewer and TDO supply implementation, review and criterion-level evidence.
- The user or an explicitly delegated agent owner accepts the verified selection.
  Separate Epic closure remains human-owned.
- The integrated working result is an increment. A Sprint is an optional timebox.
- Existing Epic/Increment records retain their original semantics without migration.

See [User Stories and product backlog](../workflow/user-stories.md) and the
[canonical AIM method](../workflow/agile-iteration-method.md).

## Prove the important behavior early

- Agree Story criteria and the relevant product quality goals before building.
- Measure the first working core before expanding it. A separate reviewer
  challenges a material core with an independent example while correction is
  still small.
- Check the actual delivered entry point and important user journeys, including
  complete-result time when it matters to the product.
- Keep raw observations behind the quality assessment. Missing, failed or stale
  evidence calls for correction or an explicit owner decision.
- Maintain a map from user journeys to a runnable verification entry so future
  changes can repeat the right checks.
- Reuse unchanged results and compact checkpoints when scope and dependencies
  still match; recheck the affected behavior after changes or new risks.

See [engineering delivery](../workflow/engineering-delivery.md).

## Audience-context integrity

- Generated artifacts communicate their intended current meaning directly.
- Private conversations, rejected drafts, AI mistakes, prompts, and review
  feedback stay out of product copy, UI labels, code comments, and docs.
- Changelogs, decision records, and other intentionally historical artifacts
  retain the history their audience needs.

This makes AIM audience-aware from the first generated artifact. See the
[canonical principle](../workflow/agile-iteration-method.md#audience-context-integrity).

## Control and cost

- `Strict` asks the designated owner for plan approval and delivery acceptance; combined proposals
  avoid separate routine Epic approvals.
- `Auto` continues within the actual mandate; changed scope, uncertainty and
  reserved decisions return to the designated owner. Strict/Auto controls
  approval behavior independently of Ship/Loop delivery style.
- `Standard`, `Cost Control`, and `Deep` guide context and verification depth;
  they preserve required quality, roles, gates and escalation.
- Existing approvals, relevant answers and confirmed checkpoints are reused
  within their exact scope. Necessary questions are grouped only when independent.
- These controls are designed to avoid repeated work; they do not establish a
  general speed, token or cost saving.

See [cost profiles](../workflow/cost-control-mode.md).

## AIM Graph

Use `/aim graph` to inspect the selected recorded execution view, activity attempts,
current proof and bounded next assignments. For native deliveries without an
execution plan it shows lifecycle checkpoints. Imported observations remain attributed evidence,
not native approval or acceptance. Failed or stale inputs identify affected work;
obsolete attempts cannot unlock dependants.

AIM UI's **Graph** tab shows Story dependencies. Select a Story to inspect its
user need, criteria, evidence and external inputs. It complements the command's
execution view; it does not display the same activity graph or launch agents.
The host runs agents; native review, validation and actual owner acceptance
still apply. See [AIM Graph](../workflow/adaptive-execution.md#aim-graph).

## AIM UI

- `/aim ui` starts or reopens the current repository's local control room;
  `start`, `open`, `status`, and `stop` also accept an explicit repo path.
- Source, adaptive, and public Agent Skill distributions carry the same trusted
  launcher, and a new repo can open truthful onboarding without creating
  `.aim`.
- The User Stories board projects the product backlog into moving Story cards,
  each retaining its Epic, user perspective, priority and criteria.
- Existing Epic workspaces and Increment history remain in the legacy delivery surface.
- Increment is the default view of the selected delivery, its proof and next
  checkpoint. User Stories shows the full requirements board; Graph exposes
  dependencies and bounded assignments. Planning uses ready Story selection.
- The header identifies the exact AIM product release captured when the local
  server started, separately from repository runtime-contract versions.
- Current Story controls produce reviewed chat handoffs. The main AIM chat
  mutates runtime and records actual decisions; viewing never grants authority.
- The legacy delivery surface retains Portfolio summaries, People and agents,
  Closed Increment history and eligible connected Codex Start/Approve dispatch.
  View-only mode retains reviewed handoffs.
- Legacy Portfolio/Roadmap controls retain their separate calibration, Discuss,
  explicit promotion and bounded mandate journey; they do not plan or approve
  native Story deliveries.
- Every Story retains its Epic identity and individual acceptance evidence.
  Legacy cards keep their canonical role and bounded helper-agent details.
- Card movement reflects persisted lifecycle evidence. Polling, filtering and
  viewing never advance a Story or accept work.
- Polling stays visually quiet and only genuine workflow movement is animated.
- In the legacy surface, connected eligible Activate and Approve actions
  dispatch exact, freshness-checked intents to the same Codex task. Change and
  free-form paths remain reviewed handoffs; buttons require a published ready
  handoff.
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

## Startup preparation

Give AIM the intent with `/aim start`. In that same agent-led flow, AIM reuses
current project context, calibrates missing or stale knowledge, then configures
missing or stale project agents and available role skills before Epics and
Stories. Empty projects start with explicitly provisional facts and bundled
skills. Existing footprints, overrides and actual authority remain binding.

Use `/aim calibrate-repo` or `/aim configure-agents` for separate later refreshes.
See [intent startup preparation](../workflow/skill-command-runtime.md#intent-led-start-and-story-continuation).

## Repository knowledge

- `/aim calibrate-repo` verifies commands, technologies, important areas, and risk.
- `/aim remember-repo` and `/aim forget-repo` maintain reusable facts.
- `aim.profile.yaml` stores compact shared knowledge.
- User hints and protected external memory remain outside the repository.
- `.aim/` stores active work, never durable repository truth.

See [repo awareness](../workflow/repo-awareness.md).

## Shared learning during delivery

- Ordinary delivery recalls relevant shared advice and contributes new verified
  reusable corrections or independently confirmed failures with existing proof;
  unverified remedies stay proposed. No reflection command or routine report.
- The old `reflect` and `reflect-all` names are retired compatibility aliases
  for bounded read-only registry views; they are not a normal learning step.
- A named stale fact, contradiction or missing lesson can trigger the smallest
  authorized source audit. Profiles and other maintained project facts retain
  their own sources and reviewed write paths.
- Registry entries preserve applicability, proof fingerprints and revision
  history; their presence does not establish truth, complete capture or benefit.
See [learning and targeted knowledge review](../workflow/reflection.md).

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
- A targeted knowledge review may recommend a focused update, regression check
  or no action. Verified lessons are shared only within the user's authorization.
- Engineering guidance targets actual failure boundaries and equivalent resource
  workloads. Mixed setup, repository maintenance and delivery time remain visible.

The [retained Enigma M3 results](../features/aim-enigma-evaluation.md) compare
GPT-6 Luna with AIM (**96.5/100** in the latest assessment) with the
[historical Luna-only delivery](../features/aim-3.2-enigma-m3-case.md)
(**49.8/100**). The earlier AIM result was **93.5/100**. The same model, high
reasoning effort, brief and scoring weights were used on different dates under
different delivery conditions. This is not a fresh paired experiment or proof
of general superiority, lower development cost, or the quality of later AIM
changes. The assessed native delivery remained unfinished. Exact frozen
versions, scope and sanitized evidence are retained in the evaluation report.

The earlier [AIM 3.2 paired study](../features/aim-3.2-enigma-case.md),
[M3 result](../features/aim-3.2-enigma-m3-case.md) and
[resource-efficiency results](../features/aim-3.1-evaluation.md) preserve their
own tested versions, workloads and limitations.

## Adapters and commands

Codex, Claude Code, and GitHub Copilot each receive a native AIM skill. All map
the same command family:

`start`, `continue`, `status`, `graph`, `validate`, `help`, `config`, `discuss`,
`ui`, `to-backlog`, `repair-catalog`, `configure-agents`, `calibrate-repo`, `remember-repo`, `forget-repo`,
`upgrade`, `mode`, `cost`, and `replan`.

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

See [combined decisions and Continue](../workflow/streamlined-decisions.md) for
chat/CLI operation, partial acceptance, recovery and legacy compatibility.
