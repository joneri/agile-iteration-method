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

An Epic describes the outcome.
The next increment must deliver a useful part of that outcome end to end.
This keeps the work centered on user value instead of a growing task list or whatever implementation detail was mentioned most recently.

## Never Lose Track

AIM records the active Epic, increment, role, and gate in durable runtime state.

That gives each session a clear answer to:

- what are we trying to achieve?
- what has been approved?
- what is being built now?
- what evidence exists?
- who owns the next decision?

When work resumes, AIM uses that state before rebuilding context from scratch.

## Quality First

AIM assumes generated work may be incomplete or wrong.

Before an increment is accepted:

1. implementation is checked against the approved increment
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
- active Epic state: `.aim/`
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

- the Epic and desired outcome
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

## Why AIM 2.0

AIM 2.0 is a structural rebuild, not a pile of patches.

It preserves the proven role and gate loop while separating workflow, repo awareness, runtime state, installation, and adapters.

For users, that means:

- easier onboarding
- guided installation
- safer repository boundaries
- clearer platform support
- persistent repo knowledge
- less repeated context loading
- a product that can grow without mixing every concern together
