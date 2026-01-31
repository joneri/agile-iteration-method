> License: CC BY 4.0 (documentation).  
> Author: Jonas Eriksson.  
> You may share and adapt this document for any purpose, including commercial use, as long as you provide attribution and indicate changes.

# Agile iteration method

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

---

## Core idea

The entire development process is treated as one continuous Agile loop,
driven by roles and guarded by explicit approvals.

1. The **Product owner (PO)** defines the problem and desired outcome.
2. The **PO** defines an **Epic** that represents a complete piece of user value, with input from the TDO when needed.
3. The Epic is refined until **PO and TDO** agree on scope, constraints and acceptance criteria.
4. The **Technical delivery owner (TDO)** defines the next **Done Increment** as a shippable slice of the Epic end to end.
5. A **Developer (Dev)** implements exactly that Done Increment.
6. A **Reviewer** checks correctness, edge cases and technical risk.
7. The **TDO** validates the increment against the Epic and the increment acceptance criteria.
8. The **PO** accepts the increment or provides feedback.
9. Feedback is carried into the next Done Increment.
10. The loop repeats until the Epic is complete.

In short, the PO owns the Epic and the TDO owns the Done Increment.

The AI never changes direction on its own.
Execution may proceed autonomously within an explicitly approved Done Increment but must stop and ask for guidance if scope, intent or assumptions change.

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
  - runbook rules conflict
  - a blocking issue requires a value judgment
  - a new Done Increment would materially change direction

Delegated execution accelerates delivery,
but **never replaces PO ownership of value or acceptance**.

## Roles and responsibilities

### Product owner (PO)

The PO is responsible for value and intent.
The PO owns the Epic.

The PO:
- defines the Epic and its user-visible value
- sets scope and non-goals
- accepts or rejects Done Increments
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
- Epic intent or runbook rules are unclear or contradictory
- acceptance checks cannot be met without new assumptions
- there is risk to trust, data correctness or user-facing meaning

Approval is only semantically meaningful at Gate A, Gate B and Gate E.

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

## How this works with Codex in VS Code

Codex cannot run multiple agents in parallel.

Instead, the method relies on:
- one continuous Codex chat
- explicit role switching
- strict output structure
- human approval at gates

`AGENTS.md` contains the master prompt that enforces this behavior.

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
- `CONTRIBUTING.md` defines coding standards, PR rules and local commands.
- `docs/features-explanations/` explains non-obvious feature behaviour, contracts and fallbacks.
- Runbooks in `docs/runbooks/` define feature-specific truth and operational steps.

Together, these documents form a complete system for structured AI-assisted development.

## License

Documentation for Agile iteration method (AIM) is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

Preferred attribution:
Jonas Eriksson (Agile iteration method, AIM)

See LICENSE-DOCS for details.

Code in this repository is not automatically covered by CC BY 4.0 unless explicitly stated. If you want code to be open source as well, add a separate code license in LICENSE.