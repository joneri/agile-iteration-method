# What AIM Is

## A Delivery System, Not a Coding Assistant

Coding assistants answer prompts and generate changes.
AIM organizes AI-assisted work into a delivery process.

It combines:

- product intent
- technical planning
- implementation
- review
- validation
- correction
- acceptance

into one repeatable loop.

The point is not to make AI look busy.
The point is to produce work that remains aligned, inspectable, and ready for a meaningful decision.

## Build What You Want

AIM is not tied to a language, framework, platform, or repository type.

Start with an intent. PO owns Epics and product priority. TDO creates and
owns User Stories and criteria for the relevant user perspectives, and plans a
coherent increment whose Stories can come from several Epics. The
integrated working result of accepted Stories is an increment. A Sprint is an
optional timebox, not a requirement.
This keeps the work centered on user value instead of a growing task list or whatever implementation detail was mentioned most recently.

## Never Lose Track

AIM records intent, Epics, Stories, delivery selections and acceptance evidence
in a durable product backlog. Existing Epic/Increment runtimes remain readable
and resumable under their original protocol.

That gives each session a clear answer to:

- what are we trying to achieve?
- what has been approved?
- what is being built now?
- what evidence exists?
- who owns the next decision?

When work resumes, AIM uses that state before rebuilding context from scratch.

## Quality First

AIM assumes generated work may be incomplete or wrong.

Before a Story selection is accepted:

1. implementation is checked against the selected Story criteria
2. a Reviewer looks for correctness issues, edge cases, and risk
3. technical validation checks the delivered result
4. failed evidence sends the work back for correction
5. a human-controlled acceptance point decides what happens next

AIM does not replace tests or guarantee correctness.
It makes review, verification, and correction normal rather than optional cleanup.

## Repository-Aware

Every repository has its own reality.

AIM can retain structured knowledge about:

- stack and frameworks
- build, test, and validation commands
- important localities
- deployment and migration constraints
- review expectations
- risk zones
- documents that should load only for certain work

The shared profile is intentionally small.
Detailed repo-specific procedures can live in deeper operational documents and load only when their trigger becomes relevant.

## Memory Without Context Bloat

Remembering everything in the active prompt is expensive and fragile.

AIM separates persistent repository knowledge from active runtime context:

- shared facts: `aim.profile.yaml`
- personal hints: user-level storage outside the repository
- active requirements and delivery state: `.aim/`
- deep operational guidance: loaded only when relevant

This allows future sessions to reuse what matters without carrying the whole repository manual all the time.

## Reflection Without Automatic Memory Mutation

Completed work contains useful lessons, but delivery history is evidence rather
than permanent truth.

`/aim reflect` verifies the current project's historical lessons against current
repository evidence and concludes with one concrete next action or an explicit
no-action result. `/aim reflect-all` previews and analyzes selected local AIM
projects to find project-specific, cross-project, personal, and AIM-product
insights.

Reflect reports remain temporary. Every candidate shows provenance, confidence,
contradictions, a proposed destination, and an explicit promotion action.
Nothing becomes durable knowledge until a person approves the separate write.

This goes beyond memory cleanup for repository work: AIM asks not only what can
be merged, but whether it is still true, where it belongs, and who owns the
decision to keep it.

## Your Tokens Are Valuable

AIM treats unnecessary context as a delivery cost.

It starts with:

1. active state
2. the compact repository profile
3. directly affected files
4. the nearest useful validation

It expands when evidence is missing, facts are stale, risk is higher, or the user asks for deeper work.

Cost profiles let operators choose normal, narrow, or deeper runtime attention without changing AIM's ownership and gate model.

## Self-Review and Correction

AIM is self-correcting in a procedural sense:

- work is reviewed before acceptance
- blocking findings return to implementation
- validation failures prevent silent completion
- contradictions and trust-sensitive uncertainty escalate

This is not a claim that AIM can always discover its own mistakes.
It is a design that creates repeated opportunities to discover and repair them.

## Human Controlled

People own:

- intent, Epic outcomes and User Story priority
- acceptance boundaries
- scope changes
- trust-sensitive decisions
- release or completion approval

Strict mode pauses at each important gate.
Auto mode reduces interruptions while preserving the same role sequence, review, escalation, traceability, and explicit approval before Epic completion.

## What AIM Does Not Replace

AIM does not replace:

- product judgment
- engineering expertise
- testing and CI
- security review
- deployment controls
- repository ownership

It provides a disciplined way for AI work to operate inside those systems.

## Why AIM 4.0

Requirements and delivery have different jobs. User Stories make distinct needs
visible and independently prioritizable. Epics explain the larger outcomes;
delivery plans select the next useful work; increments capture the result.

This gives users a board of actual needs, planning across Epics and acceptance
that remains traceable to individual criteria. The established engineering,
repository knowledge, review and validation practices support that model.
Existing work keeps its original identity and history. See the
[Story contract](../workflow/user-stories.md).
