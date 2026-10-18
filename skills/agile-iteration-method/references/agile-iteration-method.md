<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/agile-iteration-method.md
-->

> License: CC BY 4.0 (documentation).<br>
> Author: Jonas Eriksson.<br>
> You may share and adapt this document for any purpose, including commercial use, as long as you provide attribution and indicate changes.

# Agile iteration method

## Version

This document describes the current **AIM** product method. Product releases, the
product-backlog schema and the preserved legacy runtime contract are separate
versions.

## Overview

AIM turns a product intent into explicit user needs, then delivers selected
needs through planning, implementation, independent review, validation and
human-owned acceptance. Requirements remain visible before, during and after
implementation.

## Requirements and delivery

Read [User Stories and product backlog](user-stories.md) for new intent-led work.
The model is **Intent → Epics → User Stories → delivery selection → increment**.
PO owns Epic intent, outcomes, audience, scope, overall quality and product
priority, including priority between Stories. TDO owns Story creation, refinement,
acceptance criteria and dependencies, and the coherent increment commitment. A delivery can select Stories from different Epics.
A Sprint is an optional timebox; an increment is the working product result.
Neither is a requirement or a synonym for a Story.

User Stories are the moving board cards. Epics supply outcome context and
filtering. Each Story has its own stable identity and acceptance evidence.
Accepting Stories does not automatically close their Epics.

Existing `.aim/state.json` and catalogued `DI-*` workspaces keep their original
runtime semantics. The legacy protocol sections below apply only to those
workspaces. Never relabel `DI-*` or `INC-*` as User Stories, derive acceptance
from their status, or migrate them during start, validation, UI polling or
upgrade. New work uses `.aim/product-backlog.json`; these stores can coexist.

## Core idea

1. The user describes an **intent**, problem or desired outcome.
2. **PO** identifies affected users and one or more outcome-focused **Epics**.
3. **TDO** creates and refines **User Stories** and their acceptance criteria
   from the Epics. PO and TDO resolve conflicts between product intent and
   delivery; technical sequencing cannot silently change priority or quality.
4. PO prioritizes the product backlog across Epics. **TDO** proposes a bounded
   delivery selecting ready Stories, stating its coherent usable result, why
   the selection suffices, dependencies and capacity.
5. Gate A confirms the relevant direction and Story requirements. Gate B
   confirms the exact selected Stories and delivery plan. An explicitly scoped
   response can cover both; existing authorized scope remains authorized.
6. **Dev** implements the entire commitment. **Reviewer** independently checks
   decomposition against the agreed contribution to Epic intent, actual product
   behavior and selected criteria. **TDO** owns integration and validates the
   result and consolidated evidence.
7. **PO** presents verified results for user acceptance at Gate E. Acceptance
   names the Stories and criteria proved; failures remain unfinished.
8. The accepted working improvement is an **increment**. PO assesses remaining
   needs and separately proposes Epic closure only when its outcome is proven.
9. Reprioritize the remaining Stories and select the next delivery when authorized.

A Story need not approximate its entire Epic or be deployable independently.
Different user perspectives can share one coherent commitment. Technical tasks
support Stories; they do not silently replace user requirements. AIM does not expand approved
scope or turn automatic execution into automatic product acceptance.

## Coherent delivery and bounded autonomy

The delivery run is the work toward the selected increment, not an agent session
or context window. All committed Stories must be implemented, integrated and
verified. Session endings, partial checks or closed Stories cannot make an
incomplete increment finished. Preserve decisions, completed work and remaining
commitments on interruption. Distinguish verified implementation from user
acceptance; waiting for acceptance neither repeats implementation nor grants it.

TDO chooses sequential or parallel work from dependencies, integration risk and
existing resources and authority. Verify parts and review consequential risks
early; integrate as soon as relevant parts can work together. The final review
and validation cover the increment outcome and every selected criterion. A full
role and acceptance cycle is not required per Story. Corrections require affected
re-review and verification; unchanged relevant evidence can be reused.

Preserve agreed outcomes and selected criteria as the review baseline. Technical
choices may change within mandate; requirements must not be rewritten to fit the
result. Changed scope, outcome or lowered requirements require the applicable
owner decision. Preserve original commitments, decisions, reasons and remaining
needs in existing history; accepted requirements and results are never overwritten.
Follow the actual ledger's supported transitions in `user-stories.md`.

Reuse mature requirements, prior decisions, relevant skills and durable project
knowledge; supplement consequential gaps instead of restarting onboarding each
increment. Before substantial implementation, make decisive quality observable
through characteristics, references or failure examples in existing planning.
Judge the working product's function, clarity, visual expression and interactions,
alongside relevant maintainability, performance and security. Fix material in-scope
quality defects and verify again; green tests alone do not prove good experience.
Mark qualities that available evidence cannot show as unverified. Apply the useful
copy and contextual review contract in `engineering-delivery.md`.

Choose routine technical details and relevant verification autonomously within
the mandate. Before a material deviation, assess cumulative time, cost, product,
quality, external effects and reversibility across all steps and agents. Better
quality intentions, reversible files and complexity labels grant no extra scope,
agents, cost profile or product reprioritization. Explicit limits remain binding;
no numeric budget means proportionate work, not unlimited resources. Resource
limits do not silently lower agreed quality. If a real blocker or conflict arises,
state completed and remaining work and recommend a concrete path with consequences;
stop the dependent expansion and continue independent authorized work. Use existing
plan and decision surfaces, not a new form or gate. See `autonomous-interaction.md`
and `source-only/cost-control-mode.md` for mandate and resource boundaries.

## Audience-context integrity

AIM-generated product content must stand on its own inside the intended
audience's present context. Human-AI conversation history, rejected drafts,
prompts, corrections, and review feedback may shape the result, but they must
not leak into user-facing copy, UI labels or headlines, code comments,
documentation, or other product artifacts when the audience did not witness
that process.

Write the intended current meaning directly. Do not reassure an audience about
an earlier mistake they never saw with unexplained phrases such as “this time,”
“no longer,” “still,” or “not too long anymore.” Do not leave comments that
explain what the AI previously tried, or headings that argue with a discarded
version. Review from the audience's point of view and remove drafting residue,
private conversational callbacks, and comparisons that require unavailable
context.

History is valid when history is part of the artifact's actual purpose.
Changelogs, migration notes, decision records, audit trails, retrospectives, and
explicitly requested comparisons may describe prior states for an audience that
needs them. The test is not whether past context exists; it is whether the
intended audience needs that context to understand or use the artifact.

## Stable runtime architecture

AIM keeps the same architecture split and uses an explicit runtime-depth layer.

- `AIM core`:
  - the canonical role sequence
  - gates A-E
  - intent-led discovery, PO-owned Epics and priority, and TDO-owned Stories
  - Story acceptance and coherent integrated increments
  - `Strict` and `Auto` mode semantics
- `AIM runtime depth`:
  - `Standard`, `Cost Control`, and `Deep` cost profiles
  - progressive context loading
  - compact gate reporting
  - risk-scaled verification
- `AIM runtime`:
  - startup and resume flow
  - `.aim` workspace ownership
  - persistent state and gate bookkeeping
  - validation and fallback behavior
- `repo-aware policy`:
  - repository-specific verification, deployment, migration and tool rules
  - any repository restrictions on automation or parallel execution
- `platform adapters`:
  - Codex, Copilot, Claude Code or another compatible environment
  - entry behavior and capability differences
  - fallback behavior when exact parity is impossible

Rule:
- AIM core must stay tool-agnostic.
- AIM runtime must stay inspectable.
- Repo-aware policy stays repo-owned.
- Platform adapters may differ, but must not silently change the method.

## `.aim` runtime workspace

`.aim` is the repo-local AIM runtime workspace.

It exists so AIM state is visible and resumable across sessions and, where supported, across environments.

At the architectural level, users should be able to trust that:
- `.aim` belongs to AIM runtime, not to one vendor-specific integration
- the current Epic, active increment, gate and mode can be inspected there
- gate progression and acceptance decisions are owned by the main AIM thread
- auxiliary or parallel work, when allowed, produces scoped outputs only and does not take ownership of shared state

The full `.aim` file contract, schema and lifecycle rules belong to the runtime specification.

### Official `.aim` contract

For new Story work, `.aim/product-backlog.json` is the authoritative requirements
and delivery ledger; see `user-stories.md`. The following files describe the
**preserved legacy Epic/DI workspace protocol** only. They are not required to
create a product backlog and are not a substitute for Story records.


Required artifacts:
- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

Optional artifacts:
- `.aim/handoffs/`
- `.aim/logs/`
- `.aim/archive/`
- `.aim/runtime-context.md`
- `.aim/analysis/`

Adapter helper artifacts may also exist when needed, but they must not replace the official runtime contract.

### Ownership and lifecycle

The runtime must keep ownership explicit:
- only the main AIM thread may update `.aim/state.json`
- only the main AIM thread may advance gates or change increment or Epic status
- `PO` owns Epic intent updates
- `TDO` owns planning, synthesis and decision records
- `Dev` owns implementation trace artifacts
- `Reviewer` owns review findings and readiness signals
- permitted subagents may implement assigned product files under disjoint ownership; within `.aim/`, only assigned `.aim/analysis/` output is writable, never state or gates

The runtime must also keep `.aim` clean enough to inspect:
- active artifacts stay in place while the increment is in progress
- completed or stale artifacts may move to `.aim/archive/` when they are no longer active working context
- logs and analysis notes are temporary unless they remain useful for audit or resume
- secrets, credentials and unrelated application data must never be stored in `.aim`

### Active state model

`state.json` is the durable runtime checkpoint for the current Epic and active increment.

The canonical file declares `stateSchemaVersion: "1.0"`. This schema version is
separate from the AIM product release and the `aimVersion` runtime contract.
Validation may construct a read-only normalized view of documented legacy
state that lacks the field or uses a supported alias, but it must never rewrite
the source. Conflicting aliases or an unsupported schema version stop resume.

At minimum, it should answer:
- which AIM version is active
- which mode is active
- which Epic is active
- which increment is active
- which role owns the current handoff
- which gate was last passed
- whether parallel capability is available and enabled
- when the state was last updated

Markdown artifacts remain important for human inspection, but `state.json` is the runtime checkpoint the adapter should use when resuming.

## Bootstrap and resume flow

Dispatch intent-led starts and Story continuation through `user-stories.md`
before applying the following **legacy Epic workspace bootstrap**. Resume an
explicitly targeted legacy checkpoint unchanged; do not silently convert it.


AIM defines one shared conceptual startup sequence across adapters:

1. detect repo root
2. detect or create `.aim`
3. read `.aim/state.json` first when it exists
4. resume the active checkpoint or initialize a new Epic
5. read `aim.profile.yaml` when present as the primary shared repo-awareness source
6. apply compatible Personal profile hints when present
7. load only directly relevant repository evidence and canonical AIM docs
8. load active-adapter policy only when adapter mechanics matter
9. resolve execution mode, cost profile, and platform capability limits
10. enter the AIM role sequence

### Profile-first startup

Team AIM can provide a root `aim.profile.yaml` profile.
When it exists, adapters should read it before broad workflow docs, adapter guides, or repository-wide discovery.

The profile may guide:

- affected locality
- nearest validation commands
- short authoritative docs
- risk zones
- freshness triggers
- known context hogs
- areas to avoid by default

The profile must not own:

- AIM core semantics
- `.aim/state.json`
- current Epic or Done Increment state
- gate progression
- approval or acceptance decisions
- escalation decisions

If the profile conflicts with current repository evidence, AIM treats it as stale or incomplete and escalates or refreshes the smallest affected area.

At startup or Gate B, AIM should show a compact profile-source summary when profile reuse affects context selection:

```text
Profile source: aim.profile.yaml (ready)
Reused facts: commands, locality, risk zones, short docs, freshness, avoid-by-default context
Selected locality: <directly affected area or nearest known area>
Avoided context: <broad docs, adapter docs, repo-wide scan, or none>
Expansion reason: <none | missing evidence | stale profile | risk | ownership | user requested Deep>
Cheap validation first: <command or nearest check>
```

This summary is not a new gate.
It explains why AIM stayed local or expanded context.

### Cost-first bootstrap

AIM should spend the first tokens or AI Credits on deciding whether it can resume cheaply.
The runtime must check durable state before broad rereads:

- read `.aim/state.json` before rereading large method docs
- read `aim.profile.yaml`, when present and profile-ready, before broader docs or repo-wide scanning
- run the validator, when available, before manual artifact sweeps
- load the shortest authoritative context that can answer the current command
- reuse normalized runtime context from `.aim/runtime-context.md` when it is present and still coherent
- expand context only when the current state, risk, missing artifact, or user request requires it

This does not change AIM core.
It preserves role order, gate ownership, and escalation, but it makes waste visible as a runtime defect.

Budget bugs include:
- rebuilding the whole Epic context when state already points to a live checkpoint
- rereading major docs on every `continue`
- writing long low-risk markdown artifacts where a compact trace would satisfy audit needs
- treating large mixed-responsibility files as harmless just because they reduce file count

### Resume behavior

If `.aim/state.json` exists and points to an incomplete Epic:
- the runtime resumes from that checkpoint
- the runtime does not silently create a new Epic
- the active Epic, increment, gate, and mode come from the checkpoint unless repo policy or explicit user direction requires a stop-and-ask decision
- the persisted cost profile remains authoritative unless the user explicitly
  changes it or Gate B records a justified change within existing authority

If no active checkpoint exists:
- the runtime starts a new Epic at Gate A
- cost profile is selected afresh from an explicit user choice, applicable
  authorized repository minimum or the `Standard` default; concrete risk informs
  a recommendation within mandate. A completed Epic's persisted profile is
  history and must not be inherited

### Fallback behavior

If startup cannot proceed cleanly:
- missing repo-aware context:
  - stop and escalate instead of guessing
- missing `.aim`:
  - create `.aim` and continue with startup
- partially missing but recoverable runtime artifacts:
  - recreate the missing artifacts, report the assumption, and continue only if trust is preserved
- conflicting runtime state or contradictory repo policy:
  - stop and ask before continuing
- unsupported platform capability:
  - keep the same runtime contract and continue sequentially

## State transition model

The states below belong to the **legacy Epic/DI runtime**. New Story states and
delivery transitions are defined in `user-stories.md`; do not write them into
legacy `state.json` or use legacy Gates to accept Stories.


AIM gives `state.json` a formal runtime meaning instead of treating it as a loose status note.

### Canonical runtime states

- `epic_initialized`
- `gate_a_pending`
- `gate_b_pending`
- `increment_in_progress`
- `review_in_progress`
- `tdo_validation_in_progress`
- `po_approval_pending`
- `done_increment_accepted`
- `epic_paused`
- `blocked`
- `epic_complete`

### Normal transition path

The normal path for one increment is:
1. `epic_initialized`
2. `gate_a_pending`
3. `gate_b_pending`
4. `increment_in_progress`
5. `review_in_progress`
6. `tdo_validation_in_progress`
7. `po_approval_pending`
8. `done_increment_accepted`

From there:
- if the Epic continues, prepare the next increment and publish one direct
  transition to `gate_b_pending`
- if the Epic is complete, transition to `epic_complete`

Runtime writers must serialize the complete candidate state, validate it
against the shipped runtime-state schema and transition coherence rules, bind
the write to the observed source bytes, and atomically replace `state.json`.
Validation or freshness failure leaves the prior file unchanged. Internal
planning labels such as `increment_planning` are not observable runtime states.

### Exceptional states

- `epic_paused`:
  - work is intentionally paused without being abandoned
- `blocked`:
  - the runtime cannot safely continue without escalation or new input

These states are not acceptance states.
They must resume back into an active runtime state through an explicit main-thread decision.

### Transition ownership

Only the main AIM thread may persist a transition in `state.json`.

Role responsibility:
- `Dev` and `Reviewer` provide evidence that a transition is ready
- `TDO` synthesizes the transition into the next gate-ready runtime state
- `PO` owns the evidence-based recommendation for acceptance and Epic
  disposition; the ordinary user, or a separately revalidated Portfolio
  mandate, authorizes transitions into `done_increment_accepted` and
  `epic_complete`

### Observable phase-entry rule

The main AIM thread must persist the next runtime state and canonical role
before that role's visible work begins. State is an observable phase boundary,
not a summary written after the work:

- before Dev work begins, persist `increment_in_progress` with `currentRole: Dev`
- before Reviewer work begins, persist `review_in_progress` with
  `currentRole: Reviewer` and Gate C as the latest passed gate
- before post-review TDO validation begins, persist
  `tdo_validation_in_progress` with `currentRole: TDO` and Gate D as the latest
  passed gate
- only after TDO validation is complete may the runtime enter
  `po_approval_pending` with `currentRole: PO`

Writing review or decision evidence after a phase has completed does not replace
the required phase-entry transition. Read-only observers such as AIM UI must be
able to render the role that is working from authoritative runtime state while
that work is happening.

### Relationship to gates

The state model does not replace Gate A-E.
It makes the runtime meaning of those gates durable:
- Gate A approval moves the runtime from `gate_a_pending` to `gate_b_pending`
- Gate B approval moves the runtime into `increment_in_progress`
- Gate B may change cost depth within existing authority or an applicable owner
  decision when its visible rationale and persisted `costProfile` agree
- Gate D review output supports transition into `tdo_validation_in_progress`
- Gate E approval moves the runtime into `done_increment_accepted`; a subsequent
  separately authorized disposition based on the PO recommendation moves the
  Epic into `epic_complete`

### Resume rule

Resume behavior must read the persisted runtime state, not infer status from partial artifacts alone.

Resume cases:
- if `state.json` says `blocked`, AIM resumes in blocked mode and asks for input
- if `state.json` says `epic_paused`, AIM resumes as paused until the main thread reactivates the Epic
- if `state.json` says `po_approval_pending`, AIM resumes at Gate E rather than replaying earlier steps

## Repo-awareness loading model

`aim.profile.yaml` is the primary shared repo-awareness source.

The runtime uses it to select locality, validation, ownership, risk, freshness, and the smallest relevant repository evidence.
Personal profile data may add compatible local hints.
Adapter-specific policy is optional, secondary, and loaded only for the active adapter.

Generic root files are not AIM control surfaces.

The detailed load order, profile behavior, native adapter continuity, and failure rules live in:

- `repo-awareness.md`

When the profile points to richer repo-specific policy, use the two-layer contract in `repo-awareness-two-layer-model.md` and load the pointed operational doc only when one of its triggers matches.

The core rule is simple: load state first, profile second, affected evidence third, and deeper AIM or adapter docs only when the current role, gate, command, or risk needs them.

## Validator support

AIM should provide one quick integrity check for the active runtime state before or during startup, resume, or troubleshooting.

### What the validator checks

The validator should check:
- `.aim` structure
- required versus optional runtime artifacts
- `state.json` syntax and semantic coherence
- active increment alignment with increment, review and decision artifacts
- normalized repo-aware context availability
- ownership-rule violations, especially around shared state and subagent outputs
- representative installer and adapter behavior
- product coherence across canonical docs, public claims, manifests, generated
  plans, and packaged adapter surfaces

The tiered coherence and release-readiness contract lives in
`product-coherence-validation.md`.

### Result classes

Validator results should be reported using one of these classes:
- `healthy`
  - safe to continue
- `recoverable`
  - safe to repair automatically or with a reported assumption
- `blocked`
  - not safe to continue without explicit input
- `contradictory`
  - authoritative artifacts disagree and must be escalated

### Quick-check behavior

The quick check should report:
- what was checked
- the result class
- validation status for Structural, Behavioral, Product coherence, and Release
  readiness tiers
- release readiness as `PASS`, `CONDITIONAL`, or `FAIL`
- the specific failing artifact or rule, if any
- the best next action

### Relationship to runtime behavior

The validator does not replace runtime contracts.
It checks them.

This means:
- startup may run a quick check before trusting an existing checkpoint
- resume should treat `blocked` and `contradictory` results as stop-and-ask states
- recoverable results may allow repair only when trust is preserved
- validator output may recommend repair actions, but only the main AIM thread may mutate shared runtime state

## Migration support

AIM 2.0 must define a practical upgrade path for repositories that already use earlier AIM runtime models.
Older migration hops may live outside the active shipped file set.

### Supported migration scenarios

- no `.aim` yet:
  - startup creates the official `.aim` workspace before continuing
  - the runtime initializes `.aim/epic.md` and `.aim/state.json` from the active Epic context
- informal `.aim` already in use:
  - legacy helper artifacts may remain temporarily
  - the official AIM workspace contract becomes the authoritative runtime layout
- Codex-only repository:
  - the repo can adopt AIM runtime behavior without also adopting the optional Copilot layer
- Claude Code repository:
  - the repo can adopt AIM through `.claude/` entrypoints without a root `CLAUDE.md` AIM bridge
- Copilot-layer repository:
  - existing `.github/agents/aim*.agent.md` files may remain, but they must align with the shared AIM runtime contract

### Upgrade checklist

A safe AIM migration should:
- migrate reusable repository facts into `aim.profile.yaml`
- migrate adapter mechanics into the active adapter's AIM-owned helper surface
- remove AIM dependency on generic root instruction files
- create or normalize the official `.aim` workspace
- make `state.json` the durable runtime checkpoint for startup and resume
- update documentation so AIM core, AIM runtime, repo-aware policy, and platform adapters are separated explicitly
- keep validator behavior, startup behavior, and resume behavior aligned with the shared runtime model

### Legacy artifact handling

Legacy artifacts should be classified like this:
- tolerated temporarily:
  - helper files such as `.aim/plan.md`
  - adapter helper files that remain secondary to the official runtime contract
- migrated:
  - active Epic context into `.aim/epic.md`
  - active runtime checkpoint into `.aim/state.json`
  - older runtime wording in repo docs into current AIM terminology
- archived:
  - stale logs, analysis notes, and superseded helper artifacts after their decision value is preserved elsewhere
- removed or replaced:
  - legacy files that try to own gate or acceptance state outside `state.json`
  - stale instructions that contradict bootstrap, resume, ownership, or validator rules

### Relationship to startup, resume, and validation

Migration does not create a second runtime path.

During migration:
- startup follows the same shared bootstrap sequence during and after migration
- resume still trusts the active official checkpoint instead of guessing from scattered legacy artifacts
- validator quick checks should distinguish recoverable legacy gaps from contradictory legacy state
- only the main AIM thread may repair shared state during migration

## Documentation and repo-aware policy

AIM core behavior lives in this document.
Canonical supporting behavior lives under `docs/workflow/`.
Repository facts live in `aim.profile.yaml`.
Runtime state lives in `.aim/`.
Active-adapter helpers are optional and secondary.

Do not preload the workflow family.
Load a supporting document only when its behavior area becomes relevant.

The detailed documentation hierarchy lives in `source-only/documentation-model.md`.
The repo-awareness load order lives in `repo-awareness.md`.

Startup triggers (no manual bootstrap expected):
- `Install AIM`
- `Start working according to AIM`
- `Starta en AIM-loop med denna EPIC: ...`
- `/aim start "<desired outcome>"` (new intent-led work)
- `/aim start "EPIC: ..."` (explicit legacy compatibility)
- explicit Claude Code AIM start with:
  - `EPIC: <desired outcome>`
  - `Mode: Strict` or `Mode: Auto`

### Portfolio-aware normal start

This is the compatibility route for explicit legacy `EPIC:` starts and existing
Portfolio runs. Plain intent starts use the product backlog in `user-stories.md`.


Before the first write for a genuinely new Epic, normal `/aim start "EPIC:
..."` must inspect `.aim/ui-portfolio.json`. When that catalog is present,
starting in root `.aim/state.json` is forbidden even if root remains registered
for historical compatibility. The main thread resolves the trusted packaged
`scripts/aim_start.py`, previews one contained `.aim/portfolio/<EPIC-ID>/`
workspace and canonical `DI-*` reservation, then explicitly applies the same
plan. The helper stages the full workspace, rechecks catalog bytes and identity
allocation, publishes workspace and registration with bounded rollback, and
verifies the Epic and reserved Increment through AIM UI's read model before
success is reported.

Invalid, stale, colliding, active-capacity-full, traversing, escaped, or symlinked catalogs stop
without a root checkpoint or retained partial workspace. A checkpoint outside
the active catalog, or one carrying legacy status, Gate, or `INC-*` runtime
identity, is evidence to diagnose—not authority to normalize. `/aim validate`
and AIM UI name the Epic, state path, failed relation, and explicit repair or
migration route. They never mutate it.

When the operator explicitly approves retirement of one completed catalog
relation, the main thread uses the trusted packaged
`scripts/aim_catalog_repair.py`. It previews the exact candidate, Epic,
Increment, contained workspace, acceptance evidence, archive destination, and
source digests before apply. A digest-matched apply moves the workspace
unchanged, removes the catalog entry, retires the runtime-linked Backlog record,
and writes audit evidence as one rollback-safe transaction. Observation alone
never authorizes repair; root, active, ambiguous, stale, escaped, symlinked, or
unaccepted relations remain fail-closed and AIM UI remains read-only.

Front-door rule:
- show the user the next action before the full method
- first route to start, continue, or validate
- keep adapter details, runtime internals, and full gate explanations behind help or reference docs unless needed

## Execution modes

Two execution modes are defined:
- `Strict` (default): manual approvals per Done Increment at hard gates.
- `Auto` (optional): `Auto-approve until Epic complete`.

In Auto mode:
- roles and gates still execute and are reported
- current mode is shown in gate output (`Mode: Strict` or `Mode: Auto`)
- manual pauses between Done Increments are skipped unless escalation is required
- final full review is required before Epic completion; ordinary Auto then
  returns final Epic acceptance to the user
- all generated Done Increments must remain traceable

Portfolio Auto is a bounded specialization selected with `/aim start
"PORTFOLIO" mode:auto`. It previews one immutable ordered AIM UI Backlog
snapshot containing only candidates without runtime Increment links and
requires one explicit user mandate. Within that mandate, the main
AIM thread may record Gate and Epic-closure decisions as `auto-approved by
portfolio mandate` and continue sequentially through included Epics. Every Epic
still runs the complete canonical role loop in its own authoritative workspace.
This specialization makes the active, revalidated mandate the explicit PO
authority for a separate Epic-closure decision; it does not turn Gate E into
Epic closure. After Gate E accepts the Increment, the main thread records
`Epic closure` with `portfolio_mandate` authority and mandate provenance,
preserves the accepted workspace, evidence, Backlog runtime link, and UI
catalog entry, then completes the active candidate. It selects the next
candidate only as `activation_pending`. That candidate remains Planned until
its contained workspace, canonical state, and `runtimeIncrementId` validate;
only then does the run checkpoint advance to the exact workspace status. This
restart-safe sequence needs no additional user message. Missing or mismatched
relations after the pending checkpoint fail closed. The per-Epic review is a
required execution checkpoint, not an additional operator pause.
The mandate never authorizes scope expansion, later Backlog additions, unsafe
effects, or completion without review and validation. Those conditions pause
at a durable checkpoint for the user. `/aim continue` resumes only after the
snapshot, checkpoint, workspace, Backlog link, UI catalog containment, and
admission state are revalidated.

A terminal `completed` or `stopped` Portfolio run may be archived only through
an explicit helper transition that matches its observed timestamp. The exact
validated run moves to a collision-safe contained `.aim/archive/` evidence
path, after which a new user mandate may create a new canonical run. Active,
paused, stale, malformed, symlinked, and colliding runs remain fail-closed;
Portfolio start never archives automatically.

## Cost profiles

Cost profile is separate from execution mode.

- execution mode controls whether AIM pauses for manual approvals
- cost profile controls how much context, narration, verification, and parallel help AIM spends

Defined cost profiles:

- `Standard`:
  - default AIM behavior
  - progressive context loading instead of broad rereads
  - durable-state resume before full context rebuilds
  - compact gates unless risk requires detail
  - validator and direct evidence before manual artifact sweeps
- `Cost Control`:
  - lower-cost AIM for low-risk, reversible work
  - same roles, gates, acceptance, and escalation rules
  - no implementation subagents by default; material final review follows
    `adaptive-execution.md`, including explicit capability exceptions
  - narrow file reads and short visible checkpoints
  - short trace artifacts by default
  - recommend deeper effort for concrete risk; change profile only within
    existing authority or an applicable owner decision
- `Deep`:
  - high-assurance AIM for trust, data correctness, migration, deployment, security, API, or broad public-method changes
  - broader context loading and stronger review evidence are expected

Cost Control is not "AIM Lite".
It is full AIM with a smaller runtime budget.

Safe Cost Control candidates:
- docs cleanup
- spelling or wording fixes
- low-risk copyable-kit maintenance
- narrow adapter helper updates
- reversible local changes with obvious verification

Assess whether the existing mandate and depth can cover concrete risks in:
- trust or user-facing meaning
- data correctness
- deployment or migration
- public API or security behavior
- unclear Epic intent or uncertain acceptance

## Delegated execution

After applicable Gate A/B authority covers:
- the PO-owned Epic direction, and
- the TDO-owned selected Stories and delivery plan,

the roles **TDO → Dev → Reviewer → TDO** may execute the full loop without further PO involvement.

This mode is called **delegated execution**.

### Rules for delegated execution

During delegated execution:

- The AI may proceed through Gate C and Gate D autonomously.
- The TDO may validate and prepare release notes.
- Stop the dependent action and resolve with PO when existing authority is
  insufficient and:
  - scope needs to change
  - the Epic intent is unclear or contradicted
  - feature-doc rules or runtime context conflict
  - a blocking issue requires a value judgment
  - a new Done Increment would materially change direction

Delegated execution accelerates delivery,
but **never replaces PO ownership of value or the user’s acceptance authority**.

## Interaction model

AIM replaces the generic visible approval template with a role-specific, step-specific interaction model.

Core method stays the same:
- role order stays the same
- gate order stays the same
- one bounded approved delivery selection is active at a time; it may contain several Stories from several Epics

What changes is the visible response shape.
Each role should sound like that role and should ask only for the decision that belongs at that step.

### Interaction authority

For visible output, the role-specific, step-specific interaction model is authoritative.

That means:
- visible output should match the current role and checkpoint
- visible output should include only the information needed for that step
- AIM should not force all checkpoints into one reusable visible approval template
- the user should not have to infer meaning from repeated boilerplate when the role context can say it directly

### Hard-gate conceptual minimums

At a hard gate, AIM still needs four things to be clear:
- what decision is being proposed or has been made
- what will change or has changed
- which files are relevant
- how the step should be evaluated

These are conceptual minimums, not mandatory universal section headings.
The visible response may satisfy them through role-specific wording instead of fixed labels.

When AIM UI is active, reaching the hard-gate column and publishing its decision
controls are distinct transitions. The main thread may persist an optional
`uiDecision` extension with `visibility: preparing`, the exact Gate, and target
identity while it completes evidence and handoff work. Changing that marker to
`ready` with a fresh `updatedAt` must be the final runtime mutation immediately
before the gate is presented. The UI may use this marker only to time control
visibility; it cannot infer approval or advance state from it. Missing markers
retain legacy behavior for existing workspaces.

`/aim discuss [question]` is an analysis-only AIM capability, not a delivery
phase or Gate. It may use the complete AIM method plus progressively selected
repository profile, current runtime, decision, and accepted-delivery evidence
to explore product direction. It never creates or edits runtime state, source,
Backlog, profiles, durable knowledge, Epics, Increments, or Gate decisions. A
discussion may recommend one separate explicit promotion action but cannot
execute it. AIM UI may provide a visual entry point, while the shared command
contract remains the semantic owner across adapters.

### Role-specific response patterns

- `PO` at Gate A:
  - frames the Epic
  - explains why the Epic exists and what is being approved now
- `TDO` before development:
  - proposes a delivery selection of ready Stories across relevant Epics
  - explains why this is the right slice now
- `Dev`:
  - reports what was implemented and verified
  - defaults to an informational update, not an approval-shaped checkpoint
- `Reviewer`:
  - reports findings, risk and verification status
  - defaults to a verification update, not an approval-shaped checkpoint
- `TDO` after review:
  - turns implementation and review into a demo, test and feedback checkpoint
- `PO` after accepted increment:
  - evaluates the Epic goal, acceptance criteria, accepted evidence, non-goals,
    and remaining gaps
  - recommends exactly one disposition: `close`, `continue`, or `split`, with
    rationale and the consequence for remaining scope
  - never substitutes an undirected choice for the PO recommendation
  - leaves the resulting ordinary Strict/Auto decision to the user

### Step-specific approval semantics

Different approvals mean different things:
- Epic approval:
  - approve Epic framing and scope
- delivery plan approval:
  - approve the exact selected Stories, their requirements and delivery plan
- increment acceptance:
  - accept the demonstrated increment or request adjustment
- Epic continuation:
  - continue the Epic, close it or separate new scope

Dev and Reviewer should not feel like approval gates in normal flows.
They provide evidence and readiness signals unless escalation is required.

### Language

Visible responses should:
- make the current speaker explicit
- explain what happened in the previous step when that context matters
- explain what the user is expected to do now
- explain what AIM will do next if the user continues

Prefer explicit actors over ambiguous pronouns when clarity would otherwise suffer.
Use `you` only when the meaning is obvious.

### Response minimalism

Do not force every response into the same section list.
Include only what is necessary for the current step.

This does not weaken the gate contract.
It means the gate contract is satisfied through the information made clear, not through one fixed visible layout.

Use a visible `handoff` label only when it helps.
Often a short next-step sentence is more natural and more obviously role-specific.

Short transport inputs such as `approve` or `change:` may still be supported at hard gates.
They are routing helpers, not proof that visible checkpoint wording should reuse the same generic CTA everywhere.

For example:
- `Dev` usually needs:
  - what changed
  - what was verified
  - any open risk or escalation
- `Reviewer` usually needs:
  - findings
  - what is already verified
  - any recommended user test
- post-review `TDO` usually needs:
  - practical summary of the increment
  - what was already verified
  - how the user can test or demo it now
  - what decision is needed next

## Canonical roles and aliases

Canonical AIM role names are:
- `PO`
- `TDO`
- `Dev`
- `Reviewer`

Aliases may exist in tooling but are non-canonical:
- `Planner` maps to `TDO` (or a `PO+TDO` wrapper)
- `Builder` maps to `Dev`

Method-level docs and gate reporting should use canonical names.

## Roles and responsibilities

Each role applies its bundled engineering skill and any relevant project skill
whose instructions are actually available. See
`engineering-delivery.md` for independent correctness evidence,
runtime performance/resource measurement, security applicability, readable
responsibility boundaries and source-bound knowledge freshness. These checks
belong inside the existing role work and add no approval gate. Empty projects
start from provisional capabilities inferred from requirements, then verify
them against the selected stack. Do not copy temporary feature status into
native agent instructions.

### Product owner (PO)

PO owns Epics: product intent, outcomes, audience, scope, overall quality and
product priority, including priority between Stories. PO preserves requirement
provenance and decides which product needs come next. TDO owns Story detail and
criteria within that intent. PO assesses the integrated product outcome and
recommends acceptance or correction. The user retains final
acceptance authority unless an explicit bounded mandate supplies it. PO
assesses each Epic separately and cannot close it merely because a delivery ended.

### Technical delivery owner (TDO)

TDO owns Story creation, refinement, acceptance criteria, dependencies and the
coherent increment commitment. The plan names ready Story IDs from one or several
Epics, the usable result, why the selection suffices, boundaries, integration
checks and remaining scope. TDO sequences work within mandate, preserving PO
product priority, and owns integration and consolidated evidence for all selected
Stories across sessions. Resolve intent/delivery conflicts with PO; do not remove
necessary content or lower quality through Story wording. Implementation tasks
never replace the backlog.

### Developer (Dev)

Dev implements the approved Story selection and records checks against each
Story. Keep scope bounded, use focused code responsibilities, handle failures
and avoid unrelated changes. Dev does not set priority, advance shared state,
accept Stories or close Epics.

### Reviewer

Reviewer independently checks whether the decomposition covers the agreed
contribution to Epic intent, then current code, regressions, the integrated
product and each selected Story’s preserved criteria. Findings identify affected Story IDs. Defects return
to implementation and affected evidence is refreshed. Material review follows
`adaptive-execution.md`. Review supplies evidence, not acceptance authority.

## EPIC

An EPIC describes a **complete piece of user value**.

An EPIC must include:
- goal
- outcome class: `Product`, `Pilot`, or `POC`
- non-goals
- acceptance criteria with stable numbered or explicit `AC-*` identities
- rollback notes (if relevant)

An EPIC is a contract between PO and TDO.
It is not a technical design document.

An EPIC is complete only after PO assesses its full outcome and actual acceptance
authority is recorded under the applicable Story or preserved legacy protocol.

The outcome class is a truth boundary, not a maturity label that may be changed
at closure. `POC` permits synthetic or fixture-backed evidence only for the
explicitly bounded proof. `Pilot` and `Product` require representative evidence
from the declared operating context. A successful POC must not be described as
a delivered Pilot or Product.

---

## User Stories

A User Story expresses a particular user's need and its value. It has a stable
`US-*` identity, one primary Epic, persona, need, benefit, priority and stable
acceptance criteria. It lives independently of any delivery plan. See
[user-stories.md](user-stories.md) for readiness, lifecycle, evidence and examples.

## Done Increment

An increment is the integrated working product improvement resulting from one
or more accepted Stories. Its boundaries follow the selected user needs, which
can span Epics. An increment does not have to reproduce the whole Epic on a
smaller scale. A Sprint, when used, is only the timebox for pursuing a goal.

Legacy workspaces retain their historical `DI-*` plans and acceptance semantics.
Those identifiers are never silently reinterpreted as Stories.

### Behavioral scope and file boundaries

AIM chooses coherent usable increments that satisfy the agreed value and are
clear to review and maintain. A small easy-to-finish selection is insufficient
when it misses that value. Bounded behavior does not mean minimal file count.

More files can be better when each file has one clear responsibility.
Agents should split by stable responsibility and ownership, not by arbitrary line counts.

Within an approved Done Increment, it is acceptable to create focused components, hooks,
helpers, domain modules, service modules, or short supporting docs when they:
- preserve the approved behavior
- make the increment easier to understand and verify
- reduce future context cost for humans and AI agents

Do not create context hogs: oversized route files, components, services, docs, or helpers
that mix responsibilities just to keep the diff in fewer files.
No scope creep means no extra behavior, not “no new files”.
This guidance does not allow broad rewrites or arbitrary splitting; file changes still
must be explicit at Gate B and justified by a clearer boundary.

## Example: Auto-post epic and a real Done Increment

### Epic: Trygg Auto-post

**Epic goal:**<br>
Make Auto-post a trustworthy communication surface that shows the portfolio’s real development based on total value, and avoids misleading or speculative content when data is incomplete.

**Key principles:**
- Total value is always the main KPI
- Auto-post should rather be silent than wrong
- Uncertain data must be clearly communicated to the user

### A real Done Increment from this Epic

**Done Increment:** “Uncertain data” mode for the Auto-post daily snapshot

This increment delivers an end-to-end user experience for days with incomplete or unreliable data:

- The daily snapshot clearly marks the post as **Uncertain data**
- Total value is still shown, but daily change and top-mover content is neutralised
- Visual emphasis is reduced to avoid winner/loser interpretation
- Sharing is disabled or clearly discouraged to prevent publishing misleading content
- On normal days, behaviour is unchanged

This can be demoed and evaluated by a user:

> “On a normal day Auto-post behaves as usual.<br>
> On an uncertain day the post clearly signals caution and does not encourage sharing.”

### Core rule

> If the change cannot reasonably be demoed and evaluated by a user,
> it is probably too small to be its own Done Increment.

The example can be expressed as a Story for a reader who needs trustworthy
information on uncertain days. Another Story can serve a publisher who needs
to suppress sharing. PO can prioritize these needs independently; a delivery
may select either or both when dependencies and user value permit.

---

## Skateboard rule (anti-micro-increment)

When defining a Done Increment, ask:

> Does this feel like a skateboard, or just a better pedal?

- A skateboard: usable, testable, end to end
- A pedal: a local improvement without standalone value

Apply this test to the increment’s agreed usable result; the whole Epic need not
finish. A small accessibility fix, clearer error label or internal reliability
change can be valuable when its need and verification are explicit. Select enough
Stories to preserve the agreed journey and design; independent deployability is
not a Story requirement. Verified learning is a primary result only for explicitly
exploratory work, never a substitute for a requested functioning product.

---

## Gates

Gates are reporting checkpoints (A–E). They are mandatory to report, but the loop does not pause at every gate.

- **Gate A**: relevant Epic direction and Story requirements ready
- **Gate B**: selected Stories and delivery plan ready
- **Gate C**: Implementation ready (soft gate)
- **Gate D**: Review findings ready (soft gate)
- **Gate E**: acceptance of explicitly identified Stories with verified criteria;
  any Epic closure remains a separate, explicitly scoped decision.

### Default gate behaviour

- Complete the integrated delivery workflow, preserving its commitment across
  interruptions and sessions: PO → TDO → Dev → Reviewer → TDO → PO.
- The agent must not stop at Gate C or Gate D unless an escalation condition is met.

### When the loop must stop and escalate to the PO

Stop the dependent action and ask for input when no existing authority resolves:
- scope that must expand beyond what was agreed at Gate B
- Epic intent, runtime context, or feature-doc rules are unclear or contradictory
- acceptance checks cannot be met without new assumptions
- a material unresolved risk to trust, data correctness or user-facing meaning
  that cannot be handled within the mandate

Approval is only semantically meaningful at Gate A, Gate B and Gate E.

At Gate E, the workflow must still distinguish two decisions:
- increment acceptance after TDO demo, test, and feedback framing
- Epic disposition assessed before the response and enacted after acceptance

For preserved legacy DI workspaces, the remainder of this Gates section is the
compatibility acceptance/closure protocol. New Story acceptance and Epic closure
use `user-stories.md`. At `done_increment_accepted`, PO must evaluate the Epic goal, acceptance
criteria, accepted evidence, non-goals, and remaining gaps, then recommend
exactly one of `close`, `continue`, or `split`. The recommendation must state
its rationale and remaining-scope consequence; it must not merely ask the user
to choose among options. A recommendation is not authority. Ordinary Strict and
Auto require an explicit disposition decision, which can share a clearly
presented delivery-acceptance response. Prepare the recommendation before that
response; on resume reassess only missing or changed evidence or authority.

Before recommending `close`, PO must perform a closure truth audit that:

- maps every Epic acceptance criterion to concrete evidence and marks every one
  `proven`
- actively searches for counterevidence, including fresh repeat/resume and
  failure-path behavior rather than relying only on the successful build run
- distinguishes synthetic fixtures, mocks, internal contract checks, and POC
  runs from representative product evidence
- requires representative user-journey verification through the normal entry
  point for `Pilot` and `Product`; the implementing agent may perform it,
  including automated end-to-end tests, recording the performer and assistance
- uses a separate reviewer for material product changes under
  `adaptive-execution.md`; trivial/unavailable exceptions remain explicit
- requires unassisted operation when explicitly required by the user or project
  acceptance criteria
- binds non-empty referenced evidence by path, kind, byte digest, and aggregate
  evidence-set digest, including a structured black-box result, a negative
  test, and a separate closure-authority decision
- records no unresolved findings, contradictions, or remaining Epic gaps

User acceptance cannot convert missing or contradictory evidence into proof.
When any Epic criterion is partial, unproven, synthetic-only outside a declared
POC, or contradicted, PO must
recommend `continue` and TDO must propose the next coherent Done Increment.
`split` is reserved for genuinely new scope outside the approved Epic; it must
not be used to discard unfinished acceptance criteria.

The canonical `epic_complete` transition uses trusted `scripts/aim_decisions.py apply`
for combined decisions, or `scripts/aim_runtime_contract.py close` for legacy
closure. Both bind one contained
truth-audit JSON artifact through `epicClosureEvidence`. Directly writing
`epic_complete`, a Gate E decision, a user `accept`, or a Portfolio mandate does
not satisfy this closure contract.
The preview/apply transaction binds source state, the audit JSON, and all
referenced evidence bytes. UI and Portfolio treat legacy unbound completion as
preserved but unverified history, never as verified current closure.
The artifact contract and operator-facing template are defined in
`epic-closure-truth-audit.md`.

When the Epic continues, TDO must create the next canonical Done Increment and
return the workspace to Gate B. An incomplete Epic must not remain stranded in
an accepted-Increment checkpoint, and a planning candidate must not be shown as
if it were that runtime Increment. Epic closure remains a separate explicit PO
decision. In Portfolio Auto only, the active revalidated Portfolio mandate is
that explicit bounded PO authority: after the same evidence-based PO
recommendation, the main thread records a separate mandate-provenanced Epic
closure, completes the candidate, and
activates the next snapshot candidate without a per-Epic user stop.

For ordinary continuation, the main thread uses the trusted packaged
`scripts/aim_runtime_contract.py continue` transition. It previews the exact
authority path, source digest, next `DI-*`, and canonical candidate before a
digest-matched apply. The published checkpoint is `gate_b_pending` with the new
active Increment, `currentRole: TDO`, and Gate A as the latest passed Gate.

AIM UI remains strict about runtime authority but tolerant in presentation. If
a safely contained, syntactically valid workspace has an unknown `epicStatus`
and every other required field is canonical, the UI may keep the affected card
visible as a neutral in-progress projection labelled “Status updating”. It must
preserve the raw value in technical diagnostics, hide all Gate actions, and
avoid board-wide alarm UI.
Any additional contract drift retains the existing fail-closed behavior.

---

## Gate B checklist: Is this a real Done Increment?

For intent-led AIM work, evaluate the proposed **Story selection and delivery plan**:

- Are all selected Story IDs stable, ready and linked to their own Epic?
- Does each Story identify a user, need, value and testable acceptance criteria?
- Has PO ordered the Stories by value, with dependencies made explicit?
- Does the selection deliver the agreed coherent usable result, and does the
  plan explain why these Stories suffice, including selections across Epics?
- Does the plan bind the exact Story requirements and list implementation
  boundaries, integration checks, evidence and remaining scope?
- Are decisive quality goals observable, with relevant prior goals reused?
- Can the selected behavior and integrated outcome be demonstrated, including
  relevant failure paths, within the mandate and cumulative resource limits?
- Are prior acceptance and user authority preserved without inventing consent?

A failed check requires refinement or a corrected selection. Do not force the
selection to represent every part of an Epic. Do not reject a useful small Story
solely because it affects a label, one file or one user perspective.

## Platform adapters

AIM prefers one shared conceptual flow across platforms:

1. detect repo root
2. detect or create `.aim`
3. read `.aim/state.json` first when it exists
4. resume the active checkpoint or start a new Epic
5. load only the repo-aware context needed for the current state, command, and risk
6. resolve execution mode, cost profile, and platform capability limits
7. enter the AIM role sequence

Parity classes used by AIM:
- `shared`
  - same conceptual behavior and same runtime contract across supported adapters
- `shared_with_adapter_differences`
  - same runtime contract, but different commands, tools, or UX surfaces
- `codex_only`
  - currently documented only in Codex
- `copilot_only`
  - currently documented only in Copilot
- `claude_code_only`
  - currently documented only in Claude Code
- `planned`
  - intentionally not yet treated as supported shared behavior

### Codex adapter

In Codex, AIM runs through the installed AIM skill or explicit AIM intent plus the available Codex tool/runtime surface.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as other adapters
- recommended launcher:
  - install or enable the shipped `agile-iteration-method` skill from `../SKILL.md` when `/aim` command routing is wanted
  - keep the skill as a launcher/runtime guide that points back to this canonical core
  - treat `/aim <intent>` and `$agile-iteration-method <intent>` as equivalent
    selections of the same command contract
- supported capability areas:
  - start and resume AIM through the shared runtime flow
  - create and read `.aim`
  - update shared runtime state through the main AIM thread
  - run validation and repo-aware checks
  - use bounded parallel subagents when runtime support actually exists
- adapter differences:
  - the exact interaction surface is Codex chat and its toolset
  - controlled parallelism depends on whether the runtime actually exposes bounded subagent capability
  - some capabilities can be exposed through Codex-specific MCP integrations
- `.aim` behavior:
  - if `.aim` does not exist when AIM starts or resumes, AIM-in-Codex must create it automatically before entering the role loop
  - this is AIM runtime behavior exposed through the Codex adapter, not a built-in Codex app guarantee outside AIM
  - if `.aim/state.json` contains an incomplete Epic, AIM-in-Codex must resume that Epic rather than silently starting a new one
- fallback:
  - if bounded subagents are unavailable, AIM runs sequentially in one main thread
  - if an adapter-specific tool is unavailable, the runtime falls back to the shared contract instead of inventing different gate semantics

### Claude Code adapter

In Claude, AIM runs through the project skill at `.claude/skills/aim/SKILL.md`
or explicit AIM intent. Legacy `.claude/commands/` remain compatibility entrypoints.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as other adapters
- supported capability areas:
  - start and resume AIM through the shared runtime flow
  - create and read `.aim`
  - update shared runtime state through the main AIM thread
  - use the project AIM skill and repository-defined Claude subagents without
    taking ownership of gates or acceptance
- adapter differences:
  - the interaction surface is the AIM skill plus `.claude/agents/`; optional
    `.claude/commands/` preserve migration compatibility
  - `.claude/agents/` may provide bounded helper agents for assigned implementation, analysis, discovery, verification, or option generation
  - helper agents must remain subordinate to the shared runtime contract and repo-aware policy
- `.aim` behavior:
  - if `.aim` does not exist when AIM starts or resumes, AIM-in-Claude-Code must create it automatically before entering the role loop
  - this is AIM runtime behavior exposed through the Claude Code adapter, not a built-in Claude Code guarantee outside AIM
  - if `.aim/state.json` contains an incomplete Epic, AIM-in-Claude-Code must resume that Epic rather than silently starting a new one
- fallback:
  - if a Claude helper command or helper agent is missing, the repo must fall back to the documented explicit AIM start without changing method semantics
  - if bounded helper capability is unavailable, AIM runs sequentially in one main thread

Setup and usage are documented in:
- `.claude/agents/`
- `.claude/skills/aim/`
- `.claude/commands/`

### Copilot adapter

In GitHub Copilot, AIM runs through the project skill at
`.github/skills/aim/SKILL.md`. The shipped custom-agent layer provides native
orchestration, role specialists, and handoff UX.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as Codex
- supported capability areas:
  - start and resume AIM through the shared runtime flow
  - create and read `.aim`
  - update shared runtime state through the main AIM thread
  - use the project skill for command routing and prompt files, custom agents,
    and handoffs as interface helpers
- adapter differences:
  - commands, handoff UI, and agent wiring can differ
  - runtime state must still map to the same conceptual `.aim` workspace
  - `/aim start` and `/aim continue` are interface commands that must preserve the shared startup and resume flow
  - packaged prompt-file coverage can differ from Codex capabilities and may lag behind the runtime contract
- fallback:
  - if a capability does not map cleanly, the difference must be documented explicitly instead of hidden
  - if bounded parallel capability is unavailable, Copilot must fall back to sequential execution without changing ownership or gate rules

Setup and usage are documented in:
- `adapter-entry-model.md`
- `.github/skills/aim/`
- `.github/agents/`
- `.github/prompts/`

### Feature parity matrix

Use the adapter guidance as the detailed source of truth:
- `source-only/aim-adapter-guidance.md`

At minimum, the matrix must classify:
- start AIM session
- resume active Epic
- create and read `.aim`
- update increment state
- reviewer tool selection
- Playwright CLI execution
- Playwright MCP execution
- deployment orchestration
- database migration orchestration
- validation
- template rendering
- bounded helper agents
- parallel verification subagents

## Controlled parallelism

AIM allocates bounded work under `adaptive-execution.md` when the runtime and
applicable policy and the existing mandate permit it. TDO chooses order from
dependencies and integration risk; concurrency alone authorizes no extra agents,
profile change or scope. Independent implementation may run in parallel with
explicit write ownership; final material review uses a separate agent by default.
Only actual tool/session evidence supports a claim of independent review.

Controlled parallelism remains one of the practical runtime capabilities in AIM.
It allows AIM to speed up analysis, discovery and verification in the right situations without weakening central ownership of shared state, gates or acceptance decisions.

The safety rule is simple:
- only the main AIM thread may advance gates or change shared runtime state

Parallel work is suitable for:
- analysis
- discovery
- verification
- option generation

Parallel work is not the default for:
- deployment
- database migration
- acceptance decisions
- shared state ownership

If parallel capability is unavailable in one adapter, AIM must behave correctly through sequential fallback without changing the runtime contract.

---

## Why the method is not fully autonomous

The method is intentionally not autonomous.

Reasons:
- product decisions require judgment
- scope control must be enforced
- acceptance is a business decision

The AI accelerates thinking and execution.
Responsibility always stays with the human.

---

## When an EPIC is done

The loop ends when:
- all EPIC acceptance criteria are fulfilled
- the declared outcome class matches the evidence actually produced
- representative user-journey verification has passed for Product and Pilot
  outcomes, with the actual performer and any assistance recorded
- a counterevidence search has no unresolved findings, contradictions, or
  remaining Epic gaps
- each in-scope Story has accepted evidence and the whole Epic criteria are proven
- the applicable product-backlog or preserved legacy closure checks pass
- closure authority is separately recorded and every referenced evidence byte
  remains bound to the reviewed preview
- the PO explicitly accepts the EPIC as delivered

At that point, the EPIC is complete.

---

## Load supporting documents when needed

Start with this core document, active `.aim` state, and `aim.profile.yaml`.

Load deeper documents only when their area becomes relevant:

- repo-awareness or adapter loading: `repo-awareness.md`
- calibration, persistent memory, remember, or forget: `repo-awareness-calibration.md`
- current-project or cross-project knowledge reflection: `reflection.md`
- rich repo-specific policy or an operational-doc pointer: `repo-awareness-two-layer-model.md`, then only the pointed doc
- operating modes: `operating-modes.md`
- installation or file ownership: `source-only/install-aim-2.0.md` and `source-only/repository-surface-classification.md`
- cost behavior: `source-only/cost-control-mode.md`
- documentation authority: `source-only/documentation-model.md`
- active adapter mechanics: the matching adapter guide or helper only

Other workflow docs remain canonical for their named area, but they are not startup prerequisites.
`docs/features/` is support/reference.
`.aim/` is runtime state.
Generic root files are outside the AIM architecture.

## License

Documentation for Agile iteration method (AIM) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Preferred attribution:
Jonas Eriksson (Agile iteration method, AIM)

See LICENSE-DOCS for details.

Code in this repository is not automatically covered by CC BY 4.0 unless explicitly stated. If you want code to be open source as well, add a separate code license in LICENSE.
