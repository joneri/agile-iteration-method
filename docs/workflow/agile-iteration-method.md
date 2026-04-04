> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.  
> You may share and adapt this document for any purpose, including commercial use, as long as you provide attribution and indicate changes.

# Agile iteration method

## Version

This document describes **AIM 1.4**.
It retains the AIM 1.2 core method and keeps the accepted AIM 1.3 runtime model stable while making AIM 1.4 the active release framing.

## Overview

Agile iteration method is a structured way of using AI agents as explicit roles
in an Agile way of working.

Instead of treating AI as a single assistant that jumps between ideas,
the method enforces:

- explicit roles
- real Done Increments (not micro steps)
- clear handoffs
- hard approval gates

The goal is to converge towards working software that can be meaningfully
evaluated by users, while keeping full human control over scope, quality and direction.

The method is inspired by the “Ralph Wiggum loop”, but adapted to real product
development and renamed to reflect its Agile nature.

### AIM 1.4 architecture foundation

- Core AIM roles and gate semantics are unchanged.
- AIM is defined as `core + runtime + repo-aware policy + platform adapters`.
- `.aim` is treated as official repo-local runtime state.
- Feature documentation path is `docs/features/`.
- Epic docs path is `docs/epics/`.
- Repository profile is a first-class concept with explicit layer order.
- Execution modes are explicit: `Strict` and `Auto`.
- Canonical role names are locked: `PO`, `TDO`, `Dev`, `Reviewer`.
- Optional Copilot and Claude Code layers provide faster commands without changing method semantics.
- Controlled parallelism is allowed only when runtime support exists and ownership remains centralized.
- Commit-after-increment can be used as a team policy, but is not mandatory
  for the method itself.

---

## Core idea

The entire development process is treated as one continuous Agile loop,
driven by roles and guarded by explicit approvals.

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
8. The **TDO** presents the increment as a demo, test, and feedback checkpoint and asks whether the increment should be accepted or adjusted.
9. The **PO** decides whether the Epic should continue, close, or split new scope into a separate Epic.
10. Feedback is carried into the next Done Increment when the Epic continues.
11. The loop repeats until the Epic is complete.

In short, the PO owns the Epic and the TDO owns the Done Increment.

The AI never changes direction on its own.
Execution may proceed autonomously within an explicitly approved Done Increment but must stop and ask for guidance if scope, intent or assumptions change.

## AIM 1.4 architecture

AIM 1.4 separates the method from the machinery that runs it.

- `AIM core`:
  - the canonical role sequence
  - gates A-E
  - Epic-first execution
  - Done Increment discipline
  - `Strict` and `Auto` mode semantics
- `AIM runtime`:
  - startup and resume flow
  - `.aim` workspace ownership
  - persistent state and gate bookkeeping
  - validation and fallback behavior
- `repo-aware policy`:
  - repository-specific verification, deployment, migration, and tool rules
  - any repository restrictions on automation or parallel execution
- `platform adapters`:
  - Codex, Copilot, Claude Code, or another compatible environment
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
- the current Epic, active increment, gate, and mode can be inspected there
- gate progression and acceptance decisions are owned by the main AIM thread
- auxiliary or parallel work, when allowed, produces scoped outputs only and does not take ownership of shared state

The full `.aim` file contract, schema, and lifecycle rules belong to the runtime specification.

### Official `.aim` contract

Required AIM 1.4 artifacts:
- `.aim/epic.md`
- `.aim/state.json`
- `.aim/increments/`
- `.aim/decisions/`
- `.aim/reviews/`

Optional AIM 1.4 artifacts:
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
- `TDO` owns planning, synthesis, and decision records
- `Dev` owns implementation trace artifacts
- `Reviewer` owns review findings and readiness signals
- subagents may write only scoped outputs in allowed analysis locations

The runtime must also keep `.aim` clean enough to inspect:
- active artifacts stay in place while the increment is in progress
- completed or stale artifacts may move to `.aim/archive/` when they are no longer active working context
- logs and analysis notes are temporary unless they remain useful for audit or resume
- secrets, credentials, and unrelated application data must never be stored in `.aim`

### Active state model

`state.json` is the durable runtime checkpoint for the current Epic and active increment.

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

AIM 1.4 defines one shared conceptual startup sequence across adapters:

1. detect repo root
2. load repo-aware AIM context
3. detect or create `.aim`
4. load active Epic from `.aim/state.json` or initialize a new Epic
5. resolve execution mode
6. resolve platform capability and repo-policy limits
7. enter the AIM role sequence

### Resume behavior

If `.aim/state.json` exists and points to an incomplete Epic:
- the runtime resumes from that checkpoint
- the runtime does not silently create a new Epic
- the active Epic, increment, gate, and mode come from the checkpoint unless repo policy or explicit user direction requires a stop-and-ask decision

If no active checkpoint exists:
- the runtime starts a new Epic at Gate A

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

AIM 1.4 gives `state.json` a formal runtime meaning instead of treating it as a loose status note.

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
- if the Epic continues, prepare the next increment and return to `gate_b_pending`
- if the Epic is complete, transition to `epic_complete`

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
- `PO` owns acceptance decisions that move the increment to `done_increment_accepted` or the Epic to `epic_complete`

### Relationship to gates

The state model does not replace Gate A-E.
It makes the runtime meaning of those gates durable:
- Gate A approval moves the runtime from `gate_a_pending` to `gate_b_pending`
- Gate B approval moves the runtime into `increment_in_progress`
- Gate D review output supports transition into `tdo_validation_in_progress`
- Gate E approval moves the runtime into `done_increment_accepted` or `epic_complete`

### Resume rule

Resume behavior must read the persisted runtime state, not infer status from partial artifacts alone.

What this means:
- if `state.json` says `blocked`, AIM resumes in blocked mode and asks for input
- if `state.json` says `epic_paused`, AIM resumes as paused until the main thread reactivates the Epic
- if `state.json` says `po_approval_pending`, AIM resumes at Gate E rather than replaying earlier steps

## Normalized repo-aware runtime context

AIM 1.4 does not let each adapter invent its own interpretation of repository rules.
After loading repo files, the runtime must normalize them into one shared repo-aware context.

### Precedence order

The context is built in this order:
1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`
4. active adapter helper files
   - Copilot:
     - repository `.github/prompts/*`
   - Claude Code:
     - repository `CLAUDE.md`
     - repository `.claude/agents/*`
     - repository `.claude/commands/*`

Later layers may refine earlier ones, but they must not silently change AIM core semantics.

### Canonical context output

The normalized runtime context should expose, at minimum:
- `verification`
  - preferred verification tools and expectations
- `deployment`
  - whether deployment is allowed, restricted, or escalation-gated
- `migration`
  - whether migrations are allowed, restricted, or escalation-gated
- `reviewer`
  - reviewer preferences, required evidence, and focus areas
- `environment`
  - platform limits, adapter constraints, and capability availability
- `approval`
  - execution mode, gate approval constraints, and optional commit policy
- `parallel`
  - whether parallel work is allowed and what restrictions apply

### Runtime behavior

The runtime and adapters should read from the normalized context, not directly from scattered repo files during each decision.

This means:
- startup uses the same context shape in Codex, Copilot, and Claude Code
- resume uses the same context shape when deciding whether execution can continue
- verification, deployment, migration, reviewer, and parallel rules are interpreted once, then reused consistently

### Missing or contradictory policy

If normalization does not produce a safe context:
- missing context area:
  - fall back to AIM defaults and report the assumption when it materially affects behavior
- contradictory trust-affecting policy:
  - stop and escalate instead of guessing
- unsupported platform capability:
  - keep the intended policy in the normalized context and fall back safely during execution

## Validator support

AIM 1.4 should provide one quick integrity check for the active runtime state before or during startup, resume, or troubleshooting.

### What the validator checks

The validator should check:
- `.aim` structure
- required versus optional runtime artifacts
- `state.json` syntax and semantic coherence
- active increment alignment with increment, review, and decision artifacts
- normalized repo-aware context availability
- ownership-rule violations, especially around shared state and subagent outputs

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

AIM 1.4 must define a practical upgrade path for repositories that already use AIM 1.2.

### Supported migration scenarios

- no `.aim` yet:
  - startup creates the official `.aim` workspace before continuing
  - the runtime initializes `.aim/epic.md` and `.aim/state.json` from the active Epic context
- informal `.aim` already in use:
  - legacy helper artifacts may remain temporarily
  - the official AIM 1.4 workspace contract becomes the authoritative runtime layout
- Codex-only repository:
  - the repo can adopt AIM 1.4 runtime behavior without also adopting the optional Copilot layer
- Claude Code repository:
  - the repo can adopt AIM 1.4 runtime behavior with `AGENTS.md` plus `CLAUDE.md` and optional `.claude/` helpers
- Copilot-layer repository:
  - existing `.github/agents/aim*.agent.md` files may remain, but they must align with the shared AIM 1.4 runtime contract

### Upgrade checklist

A safe AIM 1.2 to AIM 1.4 migration should:
- keep the repository profile in `AGENTS.md` and any active adapter helper files readable through the accepted layer order
- create or normalize the official `.aim` workspace
- make `state.json` the durable runtime checkpoint for startup and resume
- update documentation so AIM core, AIM runtime, repo-aware policy, and platform adapters are separated explicitly
- keep validator behavior, startup behavior, and resume behavior aligned with the shared runtime model

### Legacy artifact handling

Legacy artifacts should be classified explicitly:
- tolerated temporarily:
  - helper files such as `.aim/plan.md`
  - adapter helper files that remain secondary to the official runtime contract
- migrated:
  - active Epic context into `.aim/epic.md`
  - active runtime checkpoint into `.aim/state.json`
  - AIM 1.2-only runtime wording in repo docs into AIM 1.4 terminology
- archived:
  - stale logs, analysis notes, and superseded helper artifacts after their decision value is preserved elsewhere
- removed or replaced:
  - legacy files that try to own gate or acceptance state outside `state.json`
  - stale instructions that contradict bootstrap, resume, ownership, or validator rules

### Relationship to startup, resume, and validation

Migration does not create a second runtime path.

What this means:
- startup follows the same shared bootstrap sequence during and after migration
- resume still trusts the active official checkpoint instead of guessing from scattered legacy artifacts
- validator quick checks should distinguish recoverable legacy gaps from contradictory legacy state
- only the main AIM thread may repair shared state during migration

## Repository profile and layering

Each repository defines its own profile in `AGENTS.md`:
- stack and runtime assumptions
- verification/testing strategy
- role behavior constraints for `PO`, `TDO`, `Dev`, and `Reviewer`

Layer order:
1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`
4. active adapter helper files
   - Copilot:
     - repository `.github/prompts/*`
   - Claude Code:
     - repository `CLAUDE.md`
     - repository `.claude/agents/*`
     - repository `.claude/commands/*`

If layers conflict, escalate instead of guessing.

Required repository files:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`

Optional adapter files:
- Copilot prompt helpers:
  - `.github/prompts/`
- Claude Code:
  - `CLAUDE.md`
  - `.claude/agents/`
  - `.claude/commands/`

Installation note:
- `.github/agents/aim*.agent.md` are part of the repository instruction layer for AIM itself.
- In Copilot, the same files also act as native custom-agent files.
- `.github/prompts/` are optional Copilot-style command helpers rather than the canonical AIM contract.

Startup triggers (no manual bootstrap expected):
- `Install AIM`
- `Start working according to AIM`
- `Starta en AIM-loop med denna EPIC: ...`
- `/aim start "EPIC: ..."`
- explicit Claude Code AIM start with:
  - `EPIC: <desired outcome>`
  - `Mode: Strict` or `Mode: Auto`

## Execution modes

Two execution modes are defined:
- `Strict` (default): manual approvals per Done Increment at hard gates.
- `Auto` (optional): `Auto-approve until Epic complete`.

In Auto mode:
- roles and gates still execute and are reported
- current mode is shown in gate output (`Mode: Strict` or `Mode: Auto`)
- manual pauses between Done Increments are skipped unless escalation is required
- final full review is required before Epic completion
- all generated Done Increments must remain traceable

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
  - Epic-doc rules conflict
  - a blocking issue requires a value judgment
  - a new Done Increment would materially change direction

Delegated execution accelerates delivery,
but **never replaces PO ownership of value or acceptance**.

## Interaction model

AIM 1.4 replaces the generic visible approval template with a role-specific, step-specific interaction model.

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
  - reports findings, risk, and verification status
  - defaults to a verification update, not an approval-shaped checkpoint
- `TDO` after review:
  - turns implementation and review into a practical demo, test, and feedback checkpoint
- `PO` after accepted increment:
  - decides whether the Epic continues, closes, or should split new scope into a new Epic

### Step-specific approval semantics

Different approvals mean different things:
- Epic approval:
  - approve Epic framing and scope
- increment approval:
  - approve the next single Done Increment
- increment acceptance:
  - accept the demonstrated increment or request adjustment
- Epic continuation:
  - continue the Epic, close it, or separate new scope

Dev and Reviewer should not feel like approval gates in normal flows.
They provide evidence and readiness signals unless escalation is required.

### Language clarity

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

Use a visible `handoff` label only when it improves clarity.
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
- decides whether the Epic continues or closes after accepted increments
- updates Epic-level completion markers only when outcomes are demonstrably fulfilled
- decides when the Epic is complete

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

The Dev never expands scope without approval.

---

### Reviewer

The Reviewer is responsible for quality and correctness.

The Reviewer:
- checks logic, edge cases and assumptions
- verifies acceptance criteria
- flags risky or misleading behavior
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

## Example: Auto-post epic and a real Done Increment

### Epic: Trygg Auto-post

**Epic goal:**  
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

> “On a normal day Auto-post behaves as usual.  
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
- **Gate E**: Increment accepted and next increment proposed (approval is meaningful)

### Default gate behaviour

- The agent must run the full workflow in one continuous run:
  PO → TDO → Dev → Reviewer → TDO → PO.
- The agent must not stop at Gate C or Gate D unless an escalation condition is met.

### When the loop must stop and escalate to the PO

Stop and ask for input if:
- scope must expand beyond what was agreed at Gate B
- Epic intent or Epic-doc rules are unclear or contradictory
- acceptance checks cannot be met without new assumptions
- there is risk to trust, data correctness or user-facing meaning

Approval is only semantically meaningful at Gate A, Gate B and Gate E.

At Gate E, the visible interaction should still distinguish two decisions:
- increment acceptance after TDO demo, test, and feedback framing
- Epic continuation or closure after the increment is accepted

---

## Gate B checklist: Is this a real Done Increment?

Before approving Gate B (Done Increment specification), the following checklist must be satisfied.

If any item fails, the increment is too small and must be bundled or reworked.

### Value and scope

- [ ] Does this increment embody a meaningful part of the Epic end to end?
- [ ] Would a user notice and understand the change without explanation?
- [ ] Can this be demoed as a complete behavior, not just a detail?

### Skateboard test

Ask the question:

> Is this a skateboard, or just a better pedal?

- [ ] The increment delivers a usable experience, even if simplified
- [ ] It does not rely on several future increments to make sense

### Feedback readiness

- [ ] Can a user give meaningful feedback on this increment?
- [ ] Is the feedback about overall behavior, not just wording or colors?

### Anti-patterns (automatic stop)

If any of the following are true, Gate B must not be approved:

- [ ] The increment only changes a single label, color or number without changing behavior
- [ ] The increment exists mainly to “clean up” something that could be bundled
- [ ] The increment cannot be explained in one sentence without saying “this prepares for later”

### Outcome

- If all checks pass: approve Gate B
- If one or more checks fail: bundle with other changes or redefine the increment

## Platform adapters

AIM 1.4 prefers one shared conceptual flow across platforms:

1. detect repo root
2. load repo-aware context
3. detect or create `.aim`
4. load active Epic or start a new one
5. resolve execution mode
6. resolve platform capability limits
7. enter the AIM role sequence

Parity classes used by AIM 1.4:
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

In Codex, AIM runs through repository instructions plus the available Codex tool/runtime surface.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as other adapters
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

`AGENTS.md` contains the operational rules for Codex runs.

### Claude Code adapter

In Claude Code, AIM runs through `AGENTS.md`, `CLAUDE.md`, and any repo-defined `.claude/` helper files.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as other adapters
- supported capability areas:
  - start and resume AIM through the shared runtime flow
  - create and read `.aim`
  - update shared runtime state through the main AIM thread
  - use repository-defined Claude commands or helpers without taking ownership of gates or acceptance
- adapter differences:
  - the interaction surface is Claude Code plus `CLAUDE.md` and optional `.claude/commands/`
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
- `CLAUDE.md`
- `.claude/agents/`
- `.claude/commands/`

### Copilot adapter

In Copilot, AIM can run through the optional custom-agent layer.

- shared goal:
  - preserve the same AIM core and repo-aware policy interpretation as Codex
- supported capability areas:
  - start and resume AIM through the shared runtime flow
  - create and read `.aim`
  - update shared runtime state through the main AIM thread
  - use prompt files, agent handoffs, and command routing as interface helpers
- adapter differences:
  - commands, handoff UI, and agent wiring can differ
  - runtime state must still map to the same conceptual `.aim` workspace
  - `/aim start` and `/aim continue` are interface commands that must preserve the shared startup and resume flow
  - packaged prompt-file coverage can differ from Codex capabilities and may lag behind the runtime contract
- fallback:
  - if a capability does not map cleanly, the difference must be documented explicitly instead of hidden
  - if bounded parallel capability is unavailable, Copilot must fall back to sequential execution without changing ownership or gate rules

Setup and usage are documented in:
- `docs/workflow/copilot-layer.md`
- `.github/agents/`
- `.github/prompts/`

### Feature parity matrix

Use the dedicated adapter/parity doc as the detailed source of truth:
- `docs/features/aim-1.4-platform-adapters-and-parity.md`

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

AIM 1.4 allows controlled parallelism only when the runtime supports it and repo-aware policy permits it.

Controlled parallelism is one of the practical upgrades in AIM 1.4.
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

## Relationship to other documents

- `AGENTS.md` defines operational rules, gates and escalation behaviour for Codex runs.
- `docs/features/aim-1.4-runtime-architecture.md` defines the architectural split between core, runtime, repo-aware policy, and adapters.
- `docs/features/aim-1.4-runtime-workspace.md` defines the official `.aim` workspace contract and runtime checkpoint model.
- `docs/features/aim-1.4-bootstrap-and-resume.md` defines the shared startup and resume flow across adapters.
- `docs/features/aim-1.4-repo-aware-runtime-context.md` defines the normalized repo-aware context that runtime and adapters consume.
- `docs/features/aim-1.4-validator-support.md` defines validator scope, quick-check behavior, and result classes.
- `docs/features/aim-1.4-migration-support.md` defines AIM 1.2 to AIM 1.4 migration scenarios, upgrade checklist, and legacy artifact policy.
- `docs/features/aim-1.4-platform-adapters-and-parity.md` defines adapter contracts, support levels, and the feature parity matrix.
- `CONTRIBUTING.md` defines coding standards, PR rules and local commands.
- `docs/workflow/copilot-layer.md` defines the optional Copilot custom-agent interface.
- `docs/features/` explains non-obvious feature behaviour, contracts and fallbacks.
- Epic docs in `docs/epics/` define feature-specific truth and operational steps.

Together, these documents form a complete system for structured AI-assisted development.

## License

Documentation for Agile iteration method (AIM) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Preferred attribution:
Jonas Eriksson (Agile iteration method, AIM)

See LICENSE-DOCS for details.

Code in this repository is not automatically covered by CC BY 4.0 unless explicitly stated. If you want code to be open source as well, add a separate code license in LICENSE.
