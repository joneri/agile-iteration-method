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

This document describes the **AIM 2.0** product surface.
It retains the stable AIM core method and runtime model while making AIM's cost-aware operator story explicit.

## Overview

Agile iteration method uses AI agents as clear roles inside one delivery loop.

Instead of treating AI as one assistant that jumps between ideas,
the method uses:

- clear roles
- real Done Increments (not micro steps)
- clear handoffs
- hard approval gates

The goal is to move toward working software that users can evaluate while keeping human control over scope, quality and direction.

The method is inspired by the “Ralph Wiggum loop”, adapted to real product development and renamed to reflect its Agile nature.

### Stable runtime basics

- Core AIM roles and gate semantics are unchanged.
- AIM is defined as `core + runtime + repo-aware policy + platform adapters`.
- Cost profiles are explicit: `Standard`, `Cost Control`, and `Deep`.
- Cost profile controls runtime depth, not approval semantics.
- The public front door is thin: start, continue, or validate first; read deeper only when needed.
- `.aim` is treated as official repo-local runtime state.
- Small Done Increments are defined by behavioral scope, not by minimal file count.
- Focused file boundaries are valid when they preserve the approved behavior and reduce future context cost.
- Canonical AIM behavior docs live in `docs/workflow/`.
- `docs/features/` is support/reference by default, not AIM core truth.
- Active Epic runtime state lives in `.aim/epic.md`.
- Repository profile is a first-class concept with a defined layer order.
- Execution modes are `Strict` and `Auto`.
- Canonical role names are locked: `PO`, `TDO`, `Dev`, `Reviewer`.
- Optional Copilot and Claude Code layers provide faster commands without changing method semantics.
- Controlled parallelism is allowed only when runtime support exists and ownership remains centralized.
- Commit-after-increment can be used as a team policy, but is not mandatory
  for the method itself.

---

## Core idea

The whole development process is one continuous Agile loop, driven by roles and guarded by approvals.

Kickoff contract:
- PO creates the Epic from desired user outcome.
- TDO creates the next Done Increment from that Epic.

1. The **Product owner (PO)** defines the problem and desired outcome.
2. The **PO** defines an **Epic** that represents a complete piece of user value, with input from the TDO when needed.
3. The Epic is refined until **PO and TDO** agree on scope, constraints and acceptance criteria.
4. The **Technical delivery owner (TDO)** defines the next **Done Increment** as a shippable slice of the Epic end to end.
5. A **Developer (Dev)** implements exactly that Done Increment.
6. A **Reviewer** checks correctness, edge cases and technical risk.
7. The **TDO** validates the increment against the Epic and the increment acceptance criteria.
8. The **TDO** presents the increment as a demo, test and feedback checkpoint and asks whether the increment should be accepted or adjusted.
9. The **PO** evaluates the accepted outcome and recommends whether the Epic
   should close, continue or split new scope into a separate Epic; the user or
   separately authorized Portfolio mandate owns the resulting decision.
10. Feedback is carried into the next Done Increment when the Epic continues.
11. The loop repeats until the Epic is complete.

In short, the PO owns the Epic and the TDO owns the Done Increment.

The AI never changes direction on its own.
Execution may proceed autonomously within an explicitly approved Done Increment but must stop and ask for guidance if scope, intent or assumptions change.

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
  - Epic-first execution
  - Done Increment discipline
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
- subagents may write only scoped outputs in allowed analysis locations

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
  changes it or Gate B records a justified escalation or de-escalation

If no active checkpoint exists:
- the runtime starts a new Epic at Gate A
- cost profile is selected afresh from an explicit user choice, repository
  minimum policy, current risk, or the `Standard` default; a completed Epic's
  persisted profile is history and must not be inherited

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
- Gate B may escalate or de-escalate cost depth when its visible rationale and
  persisted `costProfile` agree
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
- `/aim start "EPIC: ..."`
- explicit Claude Code AIM start with:
  - `EPIC: <desired outcome>`
  - `Mode: Strict` or `Mode: Auto`

### Portfolio-aware normal start

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
  - no subagents by default
  - narrow file reads and short visible checkpoints
  - short trace artifacts by default
  - expand to `Standard` or `Deep` if risk appears
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

Do not stay in Cost Control when work affects:
- trust or user-facing meaning
- data correctness
- deployment or migration
- public API or security behavior
- unclear Epic intent or uncertain acceptance

## Delegated execution

After the PO has approved:
- the Epic, and
- the next Done Increment specification (Gate B),

the roles **TDO → Dev → Reviewer → TDO** may execute the full loop without further PO involvement.

This mode is called **delegated execution**.

### Rules for delegated execution

During delegated execution:

- The AI may proceed through Gate C and Gate D autonomously.
- The TDO may validate and prepare release notes.
- The loop must stop and escalate to the PO if:
  - scope needs to change
  - the Epic intent is unclear or contradicted
  - feature-doc rules or runtime context conflict
  - a blocking issue requires a value judgment
  - a new Done Increment would materially change direction

Delegated execution accelerates delivery,
but **never replaces PO ownership of value or acceptance**.

## Interaction model

AIM replaces the generic visible approval template with a role-specific, step-specific interaction model.

Core method stays the same:
- role order stays the same
- gate order stays the same
- one active Done Increment at a time stays the same

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

### Role-specific response patterns

- `PO` at Gate A:
  - frames the Epic
  - explains why the Epic exists and what is being approved now
- `TDO` before development:
  - proposes the next single Done Increment
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
- increment approval:
  - approve the next single Done Increment
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

### Product owner (PO)

The PO is responsible for value and intent.
The PO owns the Epic.

The PO:
- defines the Epic and its user-visible value
- sets scope and non-goals
- evaluates accepted evidence against the Epic and recommends exactly one of
  `close`, `continue`, or `split` before the disposition decision
- explains the rationale and any remaining gaps instead of asking the user to
  perform an undirected PO assessment
- leaves ordinary Strict/Auto disposition authority with the user
- updates Epic-level completion markers only when outcomes are demonstrably fulfilled
- recommends completion only when the Epic outcome is demonstrably fulfilled

The PO does not design technical solutions or break work into increments.
The PO may explicitly delegate execution of a Done Increment.
When this happens, the PO does not need to approve intermediate steps,
only the final result or any escalated decisions.
---

### Technical delivery owner (TDO)

The TDO owns the delivery of the Epic.

The TDO:
- ensures the Epic represents a complete, user-visible value
- translates the Epic into Done Increments
- proposes and validates technical approaches
- prevents Done Increments that do not embody the Epic
- validates delivered increments against the Epic

---

### Developer (Dev)

The Developer is responsible for implementation.

The Dev:
- works on exactly one Done Increment at a time
- keeps scope tight
- avoids unrelated refactors
- ensures the increment works end to end
- documents how the increment can be verified
- extracts cohesive presentation, hooks, helpers, domain logic, or service modules when the approved scope is clearer and safer with focused boundaries

The Dev never expands scope without approval.
Small scope means small behavioral scope, not necessarily the fewest files.

---

### Reviewer

The Reviewer is responsible for quality and correctness.

The Reviewer:
- checks logic, edge cases and assumptions
- verifies acceptance criteria
- flags risky or misleading behavior
- checks whether the change is easier to understand without needless fragmentation
- produces a short, actionable change list

If the increment is syntactically broken or clearly unsafe,
the Reviewer must stop the loop until it is corrected.

---

## EPIC

An EPIC describes a **complete piece of user value**.

An EPIC must include:
- goal
- non-goals
- acceptance criteria
- rollback notes (if relevant)

An EPIC is a contract between PO and TDO.
It is not a technical design document.

An EPIC is complete only when the PO explicitly accepts it.

---

## Done Increment

A Done Increment is the smallest unit that:

- embodies the EPIC end to end
- delivers real, user-visible value
- can be evaluated meaningfully by a user
- is safe to get feedback on

A Done Increment is **not** a partial fix, polish step or internal improvement
unless it clearly changes the user experience as a whole.

### Behavioral scope and file boundaries

AIM optimizes for increments that are easy to review now and cheaper to change later.
That means small behavioral scope, not necessarily minimal file count.

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

Increment 1 must always aim to deliver the **full value path** of the EPIC,
even if simplified.

Subsequent increments improve robustness, edge cases and polish,
but must still represent a coherent user experience.

---

## Skateboard rule (anti-micro-increment)

When defining a Done Increment, ask:

> Does this feel like a skateboard, or just a better pedal?

- A skateboard: usable, testable, end to end
- A pedal: a local improvement without standalone value

Pedals must be bundled into a larger Done Increment.

---

## Gates

Gates are reporting checkpoints (A–E). They are mandatory to report, but the loop does not pause at every gate.

- **Gate A**: Epic ready (approval is meaningful)
- **Gate B**: Done Increment specification ready (approval is meaningful)
- **Gate C**: Implementation ready (soft gate)
- **Gate D**: Review findings ready (soft gate)
- **Gate E**: Increment accepted, followed by PO disposition assessment and a
  separate continuation/closure decision (approval is meaningful)

### Default gate behaviour

- The agent must run the full workflow in one continuous run:
  PO → TDO → Dev → Reviewer → TDO → PO.
- The agent must not stop at Gate C or Gate D unless an escalation condition is met.

### When the loop must stop and escalate to the PO

Stop and ask for input if:
- scope must expand beyond what was agreed at Gate B
- Epic intent, runtime context, or feature-doc rules are unclear or contradictory
- acceptance checks cannot be met without new assumptions
- there is risk to trust, data correctness or user-facing meaning

Approval is only semantically meaningful at Gate A, Gate B and Gate E.

At Gate E, the workflow must still distinguish two decisions:
- increment acceptance after TDO demo, test, and feedback framing
- Epic disposition after the increment is accepted

At `done_increment_accepted`, PO must evaluate the Epic goal, acceptance
criteria, accepted evidence, non-goals, and remaining gaps, then recommend
exactly one of `close`, `continue`, or `split`. The recommendation must state
its rationale and remaining-scope consequence; it must not merely ask the user
to choose among options. A recommendation is not authority. Ordinary Strict and
Auto require the user's separate disposition decision. Resume from
`done_increment_accepted` repeats this PO assessment before any transition.

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

Before approving Gate B (Done Increment specification), the following checklist must be satisfied.

If any item fails, the increment is too small and must be bundled or reworked.

### Value and scope

- [ ] Does the canonical plan declare `Epic: <EPIC-ID>` for an explicit runtime relation?
- [ ] Does this increment embody a meaningful part of the Epic end to end?
- [ ] Would a user notice and understand the change without explanation?
- [ ] Can this be demoed as a complete behavior, not just a detail?
- [ ] Is the scope behavioral rather than defined by minimizing file count?

### Skateboard test

Ask the question:

> Is this a skateboard, or just a better pedal?

- [ ] The increment delivers a usable experience, even if simplified
- [ ] It does not rely on several future increments to make sense

### Feedback readiness

- [ ] Can a user give meaningful feedback on this increment?
- [ ] Is the feedback about overall behavior, not just wording or colors?

### File boundaries and context efficiency

- [ ] Are proposed files split around stable responsibilities and ownership?
- [ ] Do the boundaries reduce future context load for humans and AI agents?
- [ ] Are any new files focused helpers, components, hooks, domain modules, services, or docs that preserve the approved behavior?
- [ ] Does the plan avoid broad rewrites, arbitrary fragmentation, and giant files created only to keep the diff looking small?

### Anti-patterns (automatic stop)

If any of the following are true, Gate B must not be approved:

- [ ] The increment only changes a single label, color or number without changing behavior
- [ ] The increment exists mainly to “clean up” something that could be bundled
- [ ] The increment cannot be explained in one sentence without saying “this prepares for later”

### Outcome

- If all checks pass: approve Gate B
- If one or more checks fail: bundle with other changes or redefine the increment

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
  - `.claude/agents/` may provide bounded helper agents for analysis, discovery, verification, or option generation
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

AIM allows controlled parallelism only when the runtime supports it and repo-aware policy permits it.

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
