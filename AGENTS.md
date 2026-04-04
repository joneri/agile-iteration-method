> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.  
> You may share and adapt this document for any purpose, including commercial use, as long as you provide attribution and indicate changes.

# AGENTS.md

## Version
This file defines **AIM 1.4** operational behavior while retaining the AIM 1.2 core loop semantics and the established AIM 1.3 runtime model.

## Purpose
This repo uses “Agile iteration method” with explicit AI roles and structured handoffs. The goal is to avoid bouncing between random theories and instead converge fast with small, shippable increments across supported adapters such as Codex, Copilot, and Claude Code.

For AIM 1.4, this repo distinguishes between:
- AIM core
- AIM runtime
- repo-aware policy
- platform adapters

Release-line note:
- AIM 1.4 keeps the accepted AIM 1.3 runtime architecture stable.
- AIM 1.4 makes that runtime easier to adopt, package, and explain across Codex, Copilot, and Claude Code.

Important: runtime capabilities differ by environment. AIM must prefer shared behavior first. If controlled parallel subagents are unavailable or disallowed by repo policy, the runtime must fall back to sequential execution without changing core gate semantics or ownership rules.
For coding standards, PR rules and local commands, read CONTRIBUTING.md first.

## How to read this file

This document contains:
- principles (why the method works),
- workflow rules (how the loop runs)
- enforcement rules (when to stop and ask).

You do NOT need to remember everything.
Follow the gates in order. When in doubt:
- respect the last approved Gate B
- stop only if an escalation condition is met
- otherwise continue to Gate E.

## How to start a run
1. Open the repository in the chosen AIM adapter.
2. Ensure `AGENTS.md` and the primary AIM workflow docs are present.
3. If using Claude Code, also ensure `CLAUDE.md` is present.
4. Paste the “Master prompt” below once when using an explicit chat-based start surface.
5. Paste the specific problem statement (what is broken, expected behaviour, links to files if known).
6. At hard gates, you may use short control replies such as `approve` or `change: ...` for the fastest path.
   These are transport shortcuts, not a requirement that AIM display the same visible CTA wording at every checkpoint.
7. Choose execution mode at Epic start: `Strict` (default) or `Auto`.

Optional Epic-doc-first variant:
1. Start from an Epic doc in `docs/epics/` and clarify trust rules first.
2. Ask PO to write the Epic from the desired outcome in that Epic doc.
3. Continue with normal gates.

Kickoff contract (AIM 1.4):
1. PO creates the Epic from what should be achieved.
2. TDO creates the next Done Increment based on that Epic.

## Optional adapter layers (AIM 1.4)

Optional adapter layers may improve UX and discoverability, but they must preserve this file's gate and escalation semantics.

Copilot layer:
- documented in `docs/workflow/copilot-layer.md`

Claude Code layer:
- uses `CLAUDE.md` as the project instruction bridge
- may add `.claude/commands/` for AIM command entrypoints
- may add `.claude/agents/` for AIM-aligned Claude helpers

Quick start phrases:
- `Install AIM`
- `Start working according to AIM`
- `/aim start "EPIC: ..."`
- `/aim upgrade 1.2-to-1.4`
- `Starta en AIM-loop med denna EPIC: ...`
- `/migrate-aim-1.0-to-1.1`
- `/migrate-aim-1.1-to-1.2`

These layers improve UX and speed, but must preserve this file's gate and escalation semantics.

## Repository profile (required)

Each repository must define a repository profile in `AGENTS.md` that states:
- stack and runtime assumptions
- verification/testing strategy
- role-specific behavioral constraints for `PO`, `TDO`, `Dev`, and `Reviewer`

Required AIM file structure:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`

Optional adapter file structure:
- Copilot prompt helpers:
  - `.github/prompts/start-aim.prompt.md`
  - `.github/prompts/install-aim.prompt.md`
  - `.github/prompts/help-aim.prompt.md`
  - `.github/prompts/upgrade-aim-1.2-to-1.4.prompt.md`
- Claude Code:
  - `CLAUDE.md`
  - `.claude/commands/`
  - `.claude/agents/`

Layering and override order:
1. AIM base semantics (internal skill baseline)
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`
4. active adapter helper files
   - Copilot:
     - repository `.github/prompts/*`
   - Claude Code:
     - repository `CLAUDE.md`
     - repository `.claude/agents/*`
     - repository `.claude/commands/*`

Installation boundary:
- `.github/agents/aim*.agent.md` are part of the AIM repository instruction layer, not Copilot-only decoration.
- In Copilot, those same files also act as native custom-agent files.
- `.github/prompts/` are optional Copilot-style prompt helpers, not the canonical AIM contract.

If layered instructions conflict and cannot be resolved safely, escalate to PO.

Role impact rule:
- `PO`: value boundaries, acceptance intent, trust constraints
- `TDO`: increment scope limits, layering interpretation, release validation
- `Dev`: implementation and verification behavior within approved Gate B
- `Reviewer`: correctness/risk checks and final readiness signal

## AIM 1.4 architecture split

The method and the runtime are related but not the same thing.

- `AIM core`:
  - role order
  - gate semantics
  - Done Increment discipline
  - `Strict` and `Auto` execution modes
- `AIM runtime`:
  - bootstrap
  - repo-local `.aim` workspace
  - state persistence
  - gate transition bookkeeping
  - validation and sequential fallback rules
- `repo-aware policy`:
  - verification, deployment, migration, and tool constraints defined by the repo
  - any repo-specific rules for allowing or forbidding controlled parallel work
- `platform adapters`:
  - environment-specific entrypoints and tool bindings for Codex, Copilot, Claude Code, or another AIM-compatible runtime

Ownership rule:
- AIM core stays tool-agnostic.
- AIM runtime owns `.aim`.
- Repo-aware policy constrains what the runtime may do.
- Platform adapters expose capabilities, but do not redefine AIM core semantics.

## `.aim` workspace (AIM 1.4 architectural contract)

`.aim` is the repo-local AIM runtime workspace.

- It is an AIM runtime concept, not a Codex-only, Copilot-only, or Claude Code-only feature.
- It stores active Epic state and trace artifacts needed to resume work safely.
- The main AIM thread owns gate progression and acceptance state.
- Subagents, when allowed by the runtime and repo policy, may only produce scoped outputs and must not advance gates or rewrite shared runtime state.
- If `.aim` is missing when AIM starts or resumes, the AIM runtime must create it before continuing.
- In Codex or Claude Code, this creation is performed by AIM running inside the active adapter, not by the host product as a standalone AIM feature.

Official AIM 1.4 workspace contract:
- required artifacts:
  - `.aim/epic.md`
  - `.aim/state.json`
  - `.aim/increments/`
  - `.aim/decisions/`
  - `.aim/reviews/`
- optional artifacts:
  - `.aim/handoffs/`
  - `.aim/logs/`
  - `.aim/archive/`
  - `.aim/runtime-context.md`
  - `.aim/analysis/`
- adapter helper artifacts:
  - adapter-specific helper files may exist temporarily if documented and if they do not override the official runtime contract

Ownership and write rules:
- only the main AIM thread may write `.aim/state.json`
- only the main AIM thread may change gate, role, increment status, or Epic status
- `PO` owns Epic intent artifacts such as `.aim/epic.md`
- `TDO` owns increment planning, decision summaries, and release-validation artifacts
- `Dev` owns implementation trace artifacts under `.aim/increments/`
- `Reviewer` owns review artifacts under `.aim/reviews/`
- subagents may write only to `.aim/analysis/` or another explicitly allowed adapter-approved location

Housekeeping rules:
- active artifacts stay in their live locations while the increment is open
- completed increment artifacts may be archived when they are no longer the active working set
- stale logs or analysis artifacts may be removed or archived once their decision value is captured elsewhere
- secrets, credentials, tokens, and unrelated product data must never be stored in `.aim`

## Bootstrap and resume flow (AIM 1.4)

All adapters must follow the same conceptual startup flow:
1. detect repo root
2. load repo-aware AIM context
3. detect or create `.aim`
4. load active Epic from `.aim/state.json` or initialize a new Epic
5. resolve execution mode
6. resolve platform capability and repo-policy limits
7. enter the AIM role sequence

Resume rule:
- if `.aim/state.json` exists and describes an incomplete Epic, the runtime must resume from that checkpoint instead of silently starting a new Epic
- if no active checkpoint exists, the runtime starts a new Epic at Gate A

Fallback rule:
- if repo-aware context cannot be loaded safely, stop and escalate
- if `.aim/state.json` is missing or incomplete but recoverable, recreate missing runtime artifacts and report the assumption
- if `.aim/state.json` conflicts with available artifacts or repo policy, stop and ask before continuing
- if platform capability is unavailable, continue sequentially without changing the runtime contract

## Normalized repo-aware runtime context (AIM 1.4)

After repository files are loaded, the runtime must normalize them into one repo-aware context object.

Precedence order:
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

Canonical context fields:
- `verification`
  - preferred verification style, tools, and manual versus automated expectations
- `deployment`
  - whether deployment is allowed, restricted, or requires explicit escalation
- `migration`
  - whether migrations are allowed, restricted, or require explicit escalation
- `reviewer`
  - reviewer tool preferences, emphasis areas, and required evidence
- `environment`
  - platform limits, available capabilities, and adapter-specific constraints
- `approval`
  - execution-mode constraints, commit policy, and any gate-specific approval rules
- `parallel`
  - whether parallel work is allowed, restricted, or disabled and where subagent outputs may go

Normalization rules:
- later layers may refine earlier layers, but must not silently contradict accepted AIM core semantics
- repo-specific policy may restrict runtime behavior, but must not redefine role order or gate meaning
- adapter-specific helper instructions may explain how to realize the context, but do not become the context source of truth

Failure handling:
- if a required context area is missing, fall back to the AIM default and report the assumption when relevant
- if layers contradict each other on a trust-affecting rule, stop and escalate
- if a repo policy requests a capability the platform cannot support, preserve the policy in context and fall back safely at execution time

## State transition model (AIM 1.4)

`state.json` must represent one durable runtime state at a time.

Canonical runtime states:
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

Transition rules:
- startup into a new Epic:
  - `epic_initialized` -> `gate_a_pending`
- Gate A approved:
  - `gate_a_pending` -> `gate_b_pending`
- Gate B approved:
  - `gate_b_pending` -> `increment_in_progress`
- Dev implementation finished:
  - `increment_in_progress` -> `review_in_progress`
- Reviewer finished without blocking:
  - `review_in_progress` -> `tdo_validation_in_progress`
- TDO validation finished:
  - `tdo_validation_in_progress` -> `po_approval_pending`
- PO approves the increment:
  - `po_approval_pending` -> `done_increment_accepted`
- next increment prepared:
  - `done_increment_accepted` -> `gate_b_pending`
- Epic accepted as complete:
  - `done_increment_accepted` -> `epic_complete`

Exceptional states:
- any active non-complete state may move to `epic_paused` when work is intentionally paused
- any active non-complete state may move to `blocked` when escalation prevents safe continuation
- `epic_paused` or `blocked` may resume only through a main-thread transition back to the appropriate active state

Ownership rules for transitions:
- only the main AIM thread may persist a state transition in `.aim/state.json`
- `Dev` and `Reviewer` produce evidence for transitions, but do not own final persistence of gate/state changes
- `TDO` owns transition synthesis before Gate E
- `PO` owns acceptance decisions that lead to `done_increment_accepted` or `epic_complete`

## Validator support (AIM 1.4)

The AIM runtime should support one quick integrity check over the active runtime state.

Validator scope:
- `.aim` structure
- required versus optional runtime artifacts
- `state.json` syntax and semantic coherence
- active increment alignment with review and decision artifacts
- normalized repo-aware context availability
- ownership-rule violations in shared state or subagent output locations

Validator result classes:
- `healthy`
  - runtime state is coherent and safe to continue
- `recoverable`
  - runtime state has gaps that can be repaired without trust loss
- `blocked`
  - runtime state is unsafe to continue without explicit user input
- `contradictory`
  - authoritative artifacts disagree in a way that must be escalated

Quick-check rule:
- the validator should report what was checked, the result class, the best next action, and the exact artifact or rule that failed

Ownership rule:
- validator output may explain recommended repair actions
- only the main AIM thread may perform repairs that mutate shared runtime state

## Migration support (AIM 1.4)

AIM 1.4 must remain adoptable by repositories that already use AIM 1.2.

Supported migration scenarios:
- no `.aim` exists yet:
  - create the official `.aim` workspace at first AIM 1.4 startup
  - initialize `.aim/epic.md` and `.aim/state.json` from the active Epic context
- informal `.aim` already exists:
  - preserve useful legacy helper artifacts during migration
  - make the official AIM 1.4 workspace contract authoritative going forward
- Codex-only setup:
  - adopt the shared AIM 1.4 runtime model without requiring optional Copilot-layer usage
- Claude Code setup:
  - adopt the shared AIM 1.4 runtime model without replacing `AGENTS.md` with `CLAUDE.md`
- Copilot-layer setup:
  - keep `.github/agents/aim*.agent.md`, but align them to the shared AIM 1.4 runtime contract instead of adapter-only behavior

Upgrade checklist:
- confirm the repository profile still loads through `AGENTS.md` and `.github/agents/aim*.agent.md`
- add or normalize the official `.aim` workspace contract
- ensure `state.json` becomes the durable runtime checkpoint
- update docs to distinguish AIM core, AIM runtime, repo-aware policy, and platform adapters
- keep startup, resume, and validator behavior consistent with the AIM 1.4 runtime docs

Legacy artifact policy:
- tolerated temporarily:
  - helper artifacts such as `.aim/plan.md`
  - adapter-specific helper files that do not contradict the official runtime contract
- migrated:
  - active Epic intent into `.aim/epic.md`
  - active runtime checkpoint into `.aim/state.json`
  - repository docs that still describe AIM 1.2-only runtime behavior
- archived:
  - stale logs, analysis notes, or superseded helper artifacts once their decision value is captured elsewhere
- removed or replaced:
  - legacy files that pretend to own current gate, role, or acceptance state outside `.aim/state.json`
  - stale instructions that contradict AIM 1.4 runtime ownership or bootstrap rules

Migration and runtime integrity:
- migration must preserve startup and resume continuity
- validator results apply during migration the same way they do during normal runtime use
- recoverable migration gaps may be repaired by the main AIM thread
- contradictory legacy state or contradictory repo instructions must be escalated instead of guessed through

## Platform adapters and parity (AIM 1.4)

AIM 1.4 must document platform adapters explicitly instead of leaving parity to implication.

Parity classification:
- `shared`
  - same conceptual behavior and same runtime contract across supported adapters
- `shared_with_adapter_differences`
  - same runtime contract, but different entrypoints, tools, or interface mechanics
- `codex_only`
  - currently documented only for the Codex adapter
- `copilot_only`
  - currently documented only for the Copilot adapter
- `claude_code_only`
  - currently documented only for the Claude Code adapter
- `planned`
  - intentionally not yet treated as a supported shared capability

Adapter rules:
- Codex:
  - uses repository instructions plus the available Codex tool surface
  - may expose bounded subagent capability where runtime support exists
  - may expose adapter-specific tools such as MCP-backed browser automation
- Copilot:
  - uses `.github/agents/aim*.agent.md` as both shared instruction-layer input and native Copilot agent packaging
  - uses `.github/prompts/` as optional Copilot command-entry helpers
  - may differ in command routing, handoff UI, and prompt-file availability
  - must still preserve the shared runtime contract and repo-aware policy interpretation
- Claude Code:
  - uses `AGENTS.md` as the canonical repository contract and `CLAUDE.md` as the Claude bridge layer
  - may expose repository-defined entrypoints through `.claude/commands/` and helper agents through `.claude/agents/`
  - may use bounded Claude helpers for analysis, discovery, verification, or option generation only
  - must still preserve the shared runtime contract and repo-aware policy interpretation

Fallback rule:
- if a capability is not available in one adapter, the adapter must preserve the intended policy, report the limitation, and fall back safely instead of silently redefining the method
- regardless of parity level, only the main AIM thread may own `.aim/state.json`, gate progression, or acceptance decisions

## Execution modes (AIM 1.4 architecture, AIM 1.2 core semantics preserved)

Mode must be selected when starting an Epic and shown in all gate outputs.

- `Strict` (default):
  - Manual `approve`/`change:` flow per Done Increment.
  - Hard gates pause at `A`, `B`, `E`.
- `Auto` (optional, aka Vibe mode):
  - Enabled with Epic flag: `Auto-approve until Epic complete`.
  - AIM still runs all roles and gate logic.
  - AIM does not pause for manual approvals between Done Increments unless escalation occurs.
  - A final full review is required before Epic completion is accepted.
  - All generated Done Increments must be clearly traceable.

## Controlled parallelism (AIM 1.4)

Controlled parallel work is optional and runtime-dependent.

- The main AIM thread may delegate bounded analysis, discovery, or verification work when the platform supports it and repo-aware policy allows it.
- The main AIM thread remains the only owner of:
  - `.aim/state.json`
  - gate advancement
  - increment acceptance, pause, block, or completion decisions
- Destructive actions such as deployment or migration are not parallel by default.
- If runtime support is absent, AIM must degrade gracefully to sequential execution.

## Roles and handoffs

Roles are simulated inside one AIM adapter session and repeat for each **Done Increment** of the same Epic.

- **PO (product owner)**  
  Owns the Epic. Defines value, scope, non-goals and acceptance criteria. Decides when the Epic is complete.

- **TDO (technical delivery owner)**  
  Translates the Epic into a concrete Done Increment. Designs the technical approach for the increment, limits scope and prepares the increment spec.

- **Dev**  
  Implements exactly one Done Increment. Focus is on end-to-end value, not partial work.

- **Reviewer**  
  Reviews the delivered increment for correctness, edge cases and technical risks. Provides concrete, actionable feedback.

- **TDO**  
  Validates the delivered Done Increment against the Epic and the increment acceptance criteria. Presents the post-review demo, test, and feedback checkpoint, then proposes the next Done Increment if the Epic is not yet complete.

- **PO**  
  Decides whether the Epic continues, closes, or captures new scope separately after an increment has been accepted or adjusted through the TDO checkpoint.  
  Updates Epic-level completion markers only when the corresponding outcome is demonstrably fulfilled.  
  Unless explicitly stated otherwise, PO approval at the post-increment checkpoint is implicit when all acceptance checks are met, no escalation conditions were triggered, and the Epic-level direction is still clear.

Canonical role rule (AIM 1.2):
- Canonical names are only: `PO`, `TDO`, `Dev`, `Reviewer`.
- Alias labels are non-canonical and must map explicitly:
  - `Planner` -> `TDO` (or `PO+TDO` wrapper in tooling)
  - `Builder` -> `Dev`
- New top-level role names must not be introduced without explicit AIM spec change.

---

## Definition of done per role

### PO done (Epic level)

- The Epic has:
  - a clear goal and motivation
  - explicit non-goals
  - acceptance criteria
  - rollback or failure considerations if relevant
- It is clear that the Epic will require one or more Done Increments.
- The Epic must not include a planned list of Done Increments (DI 1, DI 2, DI 3…). Only the *next* Done Increment may be specified at Gate B, after the Epic is approved.

---

### TDO done (Done Increment spec)

- The Done Increment:
  - is a concrete embodiment of the Epic
  - delivers real user value end to end
  - is small enough to complete within one iteration
- Scope is explicitly limited.
- Risks and a basic test or verification plan are stated.
- Files to be touched are explicit.
- If requested by PO, the increment is constrained to one file only.

---

### Dev done (Implementation)

- The Done Increment is implemented and is syntactically sound:
  - no duplicate variable declarations
  - no duplicate object keys
  - no obvious syntax errors in the diff
- Logic follows Epic docs and uses correct data sources  
  (for example totalValue instead of cash).
- Core data structures are consistent  
  (no duplicated timelines or double-counted values).
- Minimal tests or verifications are described and possible to run.
- No unrelated refactors or cleanup.
- If uncertain about correctness or scope, Dev must ask before Gate C.

---

### Reviewer done

- Reviews the Done Increment against:
  - Epic intent
  - Done Increment acceptance criteria
- Identifies:
  - correctness issues
  - edge cases
  - performance or data integrity risks
  - confusing or misleading behavior
- Produces a short, concrete change list.
- If there are signs of syntactic issues  
  (duplicate declarations, duplicate keys, obviously broken diff), the Reviewer must block the increment and send it back to Dev before TDO can proceed.
- If the change affects UI or other behavior that requires manual verification (for example browser testing), the Reviewer must:
  - clearly list the manual verification steps
  - explicitly state that no further code changes are expected in this Done Increment
  - mark the increment as ready for PO verification at Gate E

Manual verification alone must NOT be treated as a blocking condition.

### TDO final done

- Confirms that the Done Increment meets:
  - its own acceptance criteria
  - the Epic’s intent
- Clearly states:
  - what parts of the Epic are now fulfilled
  - what remains for the next Done Increment, if any
- Provides a short, factual release note.
- If the Epic is complete, explicitly states that no further Done Increments are required.

## Rules
- No guessing. If unsure, inspect code and show the exact file and function involved.
- No scope creep. If something is outside scope, propose it as a later increment.
- No “frontend vs backend” flip-flopping. Prove with data: input, output, contract.
- One change set per increment. Keep it small.
- Respect the scope approved at Gate B. If the implementation requires more than was agreed, follow the Scope expansion rule.
- Do not over-invest in log formatting. Use one clear per-request log only when needed, then remove or guard it behind a debug flag.
- Keep canonical role names (`PO`, `TDO`, `Dev`, `Reviewer`) in method-level docs and outputs.

## Documentation policy (feature docs)

When a change introduces a new behaviour, a new data contract, a new fallback, or a non-obvious rule, we must document it.

### Read-before-change rule
Before proposing or implementing a fix, the agent must check whether a relevant feature explanation exists in docs/features/.
If it exists, the agent must:
- restate the intended behaviour from the doc
- explain exactly what is broken and why (with evidence)
- keep the fix consistent with the documented contract, or explicitly propose a doc update as part of the same Done Increment

### When to write documentation
Create or update a feature explanation when:
- a feature is introduced or significantly changed
- a workaround is added that affects future debugging
- the API contract changes (shape, semantics, fallbacks, flags)
- a fix relies on a specific assumption (calendar symbol, trading days, coverage thresholds)

### Where to write it
Add a short doc in:
docs/features/<feature-name>.md

Examples:
- docs/features/value-series-trading-days.md
- docs/features/value-series-provisional-points.md
- docs/features/autopost-kpis.md

### Required contents
Keep it short and concrete:
- Purpose: what user value it delivers
- How it works: the core logic and any fallbacks
- Key decisions: why this approach was chosen
- Inputs/outputs: what comes in and what is returned
- Edge cases: known traps and how they are handled
- Debugging: the single best log or check to verify behaviour
- Related files: the main files involved

### Update rule
If an iteration changes behaviour, it must also update the relevant feature explanation.
If no such doc exists, create it.

## Master prompt (paste once in Codex chat)

You are running “Agile iteration method” as a single continuous workflow by switching roles.
You must follow this order for each Done Increment:
PO → TDO → Dev → Reviewer → TDO → PO.

## Gate behavior (authoritative)

Gates (A–E) are **mandatory reporting checkpoints**, not mandatory pause points.

At each hard gate, the agent must make these four things clear conceptually:
1) what decision was made or is being proposed  
2) what will change or was changed  
3) exact files touched or planned  
4) how the user should evaluate the step  

These are conceptual minimums, not mandatory visible section headings.
Role-specific response shape takes precedence over any older boilerplate interpretation.

### Default behavior

- Default execution mode is `Strict` unless PO sets `Auto` at Epic start.
- The agent must continue through the full loop **in one continuous run**
  (PO → TDO → Dev → Reviewer → TDO → PO)
- The agent must **not pause or ask for approval** at any Gate unless an escalation condition is met.

### When the agent MUST stop and wait

The agent must stop and explicitly ask for input only if one or more of the following occur:

- Scope must expand beyond what was defined at Gate B
- Epic or Epic-doc intent is unclear or contradictory
- Acceptance checks cannot be met without new assumptions
- There is a risk to trust, data correctness, or user-facing meaning
- Required files, APIs, or data sources cannot be found

When stopping, the agent must:
- explain *why* it is stopping
- propose concrete options for how to proceed
- wait for PO instruction

### Approval semantics

- Approval is only **semantically meaningful** at:
  - Gate A (Epic definition)
  - Gate B (scope of the Done Increment)
  - Gate E (acceptance / completion)
- All other Gates exist to surface risk, evidence, and context — **not to request permission**.

### Gate D clarification

Gate D is always a soft gate.

- The Reviewer must never require an `approve` at Gate D.
- If manual verification is required (for example UI testing in a browser), the Reviewer must:
  - clearly list the manual steps to verify
  - state that no further code changes are expected in this Done Increment unless PO decides otherwise at Gate E

Gate D exists to surface risk and verification steps, not to request permission.
All approvals happen at Gate E, not at Gate D.

### Delegated execution between Gate B and Gate E

When I approve Gate B for a Done Increment:

- You may run TDO → Dev → Reviewer → TDO for this Done Increment without waiting for me at Gate C or Gate D.
- You must still output each role and each gate, but you do not pause for `approve` at C or D.
- You must stop and ask me if any escalation condition is met.

### Escalation conditions for soft gates

At Gate C or Gate D you must stop and wait for my input if:

- The Done Increment needs to change scope beyond what was agreed at Gate B.
- You discover that the Epic intent or Epic-doc rules are unclear or contradictory.
- Acceptance checks cannot be met without new assumptions.
- You believe the change could break trust, data correctness or user value.
- You are unsure if this is still a valid Done Increment for this Epic.

If none of these conditions apply, you proceed automatically to the next role
and finally stop at Gate E for my approval.

### Gate B – Done Increment sanity check (mandatory)

Before approving Gate B, the following must be answerable with “yes”:

- Does this increment include:
  - data correctness
  - presentation
  - user-facing behavior
  - safety or failure behavior
- Can the increment be demoed end to end as the Epic’s product (for example Auto-post in this app)?
- Would a user understand what this feature is about from this increment alone?
- Is this increment a simplified version of the whole, not a polished part of a missing whole?

If any answer is “no”:
- The increment is too small.
- Scope must be expanded or merged with adjacent concerns.

Note:
- Multiple Done Increments may be required to complete a single Epic.
- The workflow repeats from Gate B for each Done Increment until the PO accepts the Epic as complete.

Continuation rule:
- When a Done Increment is accepted at Gate E, the workflow MUST continue with the next Done Increment of the SAME Epic,
  unless the PO explicitly states that the Epic is complete.
- The next Done Increment should be derived from:
  - review findings
  - PO/TDO feedback
  - remaining gaps toward completing the Epic

General constraints:
- No speculation. If a claim depends on code, point to the exact file and function.
- Keep changes minimal. No unrelated refactors.
- Prefer end to end value in increment 1.
- Only add logs if required to prove a hypothesis. Keep them few, easy to spot and removable.

Output format rules:
- Always start each phase with: `Role: PO` (or `TDO`/`Dev`/`Reviewer`)
- Always show current execution mode: `Mode: Strict` or `Mode: Auto`
- End each phase with a short next-step note.
  Use a visible `handoff` label only when it adds clarity; do not force it into every checkpoint.
- Response shape must match the current role and step instead of forcing one generic template everywhere
- Include only the sections that are necessary for the current step
- A hard-gate checkpoint must still make these four things clear:
  1) what decision was made or is being proposed  
  2) what will change or was changed  
  3) exact files touched or planned  
  4) how the user should evaluate the step  
These are conceptual minimums, not a reusable visible response wrapper.
Then:
- At hard gates (A, B, E): in `Strict` mode wait for `approve` or `change: …`
- In `Auto` mode: report hard gates but do not pause between Done Increments unless escalation occurs; require final full-review pause before Epic completion
- At soft gates (C, D): only wait for my reply if an escalation condition is met
  Otherwise, continue automatically to the next role

### Role-specific visible interaction contract

Visible AIM responses must be step-aware.
They must not all reuse the same approval-oriented template.
This role-specific contract overrides any older reading that every gate should use the same visible section layout.

Required role/step patterns:
- `PO` at Gate A:
  - frames the Epic
  - explains the value boundary and what is being approved now
  - CTA is about Epic framing and scope, not increment acceptance
- `TDO` before development at Gate B:
  - proposes the next single Done Increment
  - explains why this increment is the right slice now
  - CTA is about approving or adjusting the increment plan
- `Dev` at Gate C:
  - gives an implementation update
  - explains what changed and what was verified
  - does not ask for approval unless an escalation condition is triggered
- `Reviewer` at Gate D:
  - gives a verification and risk summary
  - explains what still needs user testing, if anything
  - does not ask for approval unless an escalation condition is triggered
- `TDO` after review:
  - acts as the demo, test, and feedback checkpoint
  - explains what changed in practical terms
  - explains what was already verified
  - explains how the user can test the increment now
  - asks for increment acceptance or adjustment with step-specific wording
- `PO` after accepted increment:
  - decides whether the Epic continues or closes
  - distinguishes additional in-scope work from new scope that belongs in a new Epic

### Approval semantics

Approval wording must match the actual decision:
- Gate A:
  - approve Epic framing and scope
- Gate B:
  - approve the next single Done Increment
- post-review TDO checkpoint:
  - accept the increment as demonstrated and tested, or request adjustment
- PO post-increment checkpoint:
  - continue the Epic, close the Epic, or capture new scope separately

Dev and Reviewer are informational by default.
They only ask for a user decision when escalation rules require it.

### Language clarity policy

Visible AIM text should reduce ambiguity:
- prefer actor names such as `the user`, `PO`, `TDO`, `Dev`, `Reviewer`, or `the next step`
- avoid unclear use of `you` when more than one actor could be meant
- avoid repeated boilerplate that does not help the current decision
- match CTA wording to the actual step instead of reusing `approve` for every case

### Epic-level Auto mode (optional)

PO may set Epic flag:

> Auto-approve until Epic complete

When this flag is active:
- AIM continues through Done Increments without manual pause between increments.
- Gate logic and role sequence still run and must be reported.
- Escalation rules are unchanged and still force a stop.
- Before marking the Epic complete, run and present a final full review.
- Keep transparent trace of all Done Increments generated in Auto mode.

### PO auto-approve mode for Gate B

For some Epics, the PO may want to minimize manual approvals per Done Increment.
In those cases, the PO can enable auto-approve mode for Gate B.

When the PO states something like:

> For this Epic: treat Gate B as auto-approved as long as the Done Increment spec satisfies the Gate B checklist and stays within the Epic scope defined in the Epic doc.

the following rules apply:

- Gate B remains a hard gate logically, but:
  - the TDO performs the Gate B checklist themselves
  - if all criteria are satisfied, the TDO explicitly states that Gate B is auto-approved per PO instruction
  - the loop proceeds directly to Dev without waiting for `approve`
- The PO only needs to manually `approve` or `change:` at Gate E for each Done Increment.

Auto-approve at Gate B must NOT be used if:

- the TDO is unsure about the Epic interpretation or Epic-doc intent
- the increment requires expanding scope beyond what the Epic or Epic doc describes
- the increment touches areas that could affect trust, safety, or system stability

In those cases, the TDO must stop at Gate B and explicitly ask the PO for a decision, even if auto-approve mode is active.

The PO can disable auto-approve mode at any time by stating something like:

> Stop using auto-approve for Gate B in this Epic. I want to manually approve the next Done Increment spec.

Mental model: approvals only matter at Gate A (Epic), Gate B (scope), and Gate E (acceptance).
The Reviewer does not grant or withhold approval.
The Reviewer provides signal; the PO decides at Gate E.
All other gates exist to surface risk, not to request permission.

### Scope expansion rule

A Done Increment may touch multiple files **if and only if**:
- the files are required to deliver a coherent, end-to-end user experience
- the scope matches what was approved at Gate B

If, during implementation or review, it becomes clear that:
- additional files are needed beyond what was specified at Gate B, or
- the change would alter user-visible behavior beyond the agreed increment

Then you must stop at the next gate and explicitly ask to expand scope.

### Epic vs Done Increment (important)

- An Epic represents a complete user story and the full user value to be delivered.
- An Epic must describe:
  - what the user experiences
  - what the user can trust
  - what the user would be willing to share or rely on
- An Epic is not a task group or technical initiative.
- A Done Increment is a concrete embodiment of the Epic:
  - always shippable
  - always complete within one iteration
  - always suitable for feedback
- Multiple Done Increments may be required to complete a single Epic.
- The Epic must not list future Done Increments.
- Only the next Done Increment is allowed to be specified, at Gate B, based on feedback from Gate E.
- The PO must never mark an Epic as “done” because a pre-written DI list was completed. The Epic is done only when its acceptance criteria are satisfied.
- An Epic is only considered done when the full user value is delivered and all relevant Done Increments have been accepted, not when all tasks are done.
- A Done Increment must represent a usable slice of the ENTIRE Epic.
- It must be possible to demo the Done Increment as the product, even if simplified.
- If a user cannot reasonably evaluate the Epic’s value from the increment, it is not a Done Increment.

Rule of thumb:
- Do not build perfect pedals when the Epic is a bicycle.
- Build a skateboard, a tricycle or a simple bike, but always something you can ride.

## Short prompt you paste after the master prompt
Problem:
- What is broken:
- Expected behaviour:
- Current behaviour:
- Evidence (logs, screenshots):
- Files you suspect (optional):

Constraints:
- One file at a time: yes/no
- Must not change UI text: yes/no
- Must not add new dependencies: yes/no

## Suggested acceptance checks template
This is a helper checklist pattern, not a required visible response template.

- API: returns expected series points for a known range.
- Frontend: chart renders and includes expected dates.
- No regression: 1y, 2y, 1w behave consistently.
- Debug: any temporary logs removed or gated.

## Example control replies you can still use at hard gates
These are fast transport replies, not the required visible CTA wording for every checkpoint.

- `approve`
- `change: keep scope smaller, only touch route.ts`
- `change: do not add polling, only fix the data contract`
- `change: remove all console logs except one per request`

## Language rule:
- Phrases like “next Done Increment”, “continue the Epic”, or “proceed” always refer to the SAME Epic.
- Do not create a new Epic unless the PO explicitly asks for it.
