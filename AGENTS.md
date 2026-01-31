> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.  
> You may share and adapt this document for any purpose, including commercial use, as long as you provide attribution and indicate changes.

# AGENTS.md

## Purpose
This repo uses “Agile iteration method” with Codex acting in explicit roles and doing structured handoffs. The goal is to avoid bouncing between random theories and instead converge fast with small, shippable increments.

Important: Codex cannot truly run multiple agents “automatically” in the background. What we can do is have Codex simulate role switching inside one run so you only have to approve at a few gates.
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
1. Open VS Code.
2. Open Codex chat for this workspace.
3. Paste the “Master prompt” below once.
4. Paste the specific problem statement (what is broken, expected behaviour, links to files if known).
5. Then only respond with: `approve` or `change: ...` at each gate.

## Roles and handoffs

Roles are simulated inside one Codex run and repeat for each **Done Increment** of the same Epic.

- **PO (product owner)**  
  Owns the Epic. Defines value, scope, non-goals and acceptance criteria. Decides when the Epic is complete.

- **TDO (technical delivery owner)**  
  Translates the Epic into a concrete Done Increment. Designs the technical approach for the increment, limits scope and prepares the increment spec.

- **Dev**  
  Implements exactly one Done Increment. Focus is on end-to-end value, not partial work.

- **Reviewer**  
  Reviews the delivered increment for correctness, edge cases and technical risks. Provides concrete, actionable feedback.

- **TDO**  
  Validates the delivered Done Increment against the Epic and the increment acceptance criteria. Prepares release notes and proposes the next Done Increment if the Epic is not yet complete.

- **PO**  
  Accepts the Done Increment or requests changes.  
  Unless explicitly stated otherwise, PO approval at Gate E is implicit when all acceptance checks are met, no escalation conditions were triggered, and the scope still matches the Epic and the runbook.

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
- Logic follows runbooks and uses correct data sources  
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

## Documentation policy (feature explanations)

When a change introduces a new behaviour, a new data contract, a new fallback, or a non-obvious rule, we must document it.

### Read-before-change rule
Before proposing or implementing a fix, the agent must check whether a relevant feature explanation exists in docs/features-explanations/.
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
docs/features-explanations/<feature-name>.md

Examples:
- docs/features-explanations/value-series-trading-days.md
- docs/features-explanations/value-series-provisional-points.md
- docs/features-explanations/autopost-kpis.md

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

At each Gate, the agent must clearly report:
1) what you decided  
2) what will change  
3) exact files you will touch  
4) acceptance checks  

### Default behavior

- The agent must continue through the full loop **in one continuous run**
  (PO → TDO → Dev → Reviewer → TDO → PO)
- The agent must **not pause or ask for approval** at any Gate unless an escalation condition is met.

### When the agent MUST stop and wait

The agent must stop and explicitly ask for input only if one or more of the following occur:

- Scope must expand beyond what was defined at Gate B
- Epic or runbook intent is unclear or contradictory
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
- You discover that the Epic intent or runbook rules are unclear or contradictory.
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
- Always start each phase with: “Role: PO” (or TDO/Dev/Reviewer)
- End each phase with a short “handoff” section stating what the next role must do.
- At gates, output only:
  1) what you decided
  2) what will change
  3) exact files you will touch
  4) acceptance checks
Then:
- At hard gates (A, B, E): wait for `approve` or `change: …`.
- At soft gates (C, D): only wait for my reply if an escalation condition is met.
  Otherwise, continue automatically to the next role.

### PO auto-approve mode for Gate B

For some Epics, the PO may want to minimize manual approvals per Done Increment.
In those cases, the PO can enable auto-approve mode for Gate B.

When the PO states something like:

> For this Epic: treat Gate B as auto-approved as long as the Done Increment spec satisfies the Gate B checklist and stays within the Epic scope defined in the runbook.

the following rules apply:

- Gate B remains a hard gate logically, but:
  - the TDO performs the Gate B checklist themselves
  - if all criteria are satisfied, the TDO explicitly states that Gate B is auto-approved per PO instruction
  - the loop proceeds directly to Dev without waiting for `approve`
- The PO only needs to manually `approve` or `change:` at Gate E for each Done Increment.

Auto-approve at Gate B must NOT be used if:

- the TDO is unsure about the Epic interpretation or runbook intent
- the increment requires expanding scope beyond what the Epic or runbook describes
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
- API: returns expected series points for a known range.
- Frontend: chart renders and includes expected dates.
- No regression: 1y, 2y, 1w behave consistently.
- Debug: any temporary logs removed or gated.

## Example control replies you use at gates
- `approve`
- `change: keep scope smaller, only touch route.ts`
- `change: do not add polling, only fix the data contract`
- `change: remove all console logs except one per request`

## Language rule:
- Phrases like “next Done Increment”, “continue the Epic”, or “proceed” always refer to the SAME Epic.
- Do not create a new Epic unless the PO explicitly asks for it.