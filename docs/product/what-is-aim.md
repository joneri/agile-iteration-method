# What AIM Is

## From an idea to software you can assess

Describe the product or improvement you want. AIM organizes AI-assisted work
into a delivery process you can follow and assess.

It combines:

- product intent
- technical planning
- implementation
- review
- validation
- correction
- acceptance

into one repeatable loop.

Each increment connects the goal, implementation and evidence so you can make
a meaningful acceptance decision.

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

Quality goals are agreed before implementation. AIM measures the first working
core and asks a separate reviewer to challenge a material core before costly
expansion. That early check helps expose a wrong approach while it is still
small enough to correct.

Before a Story selection is accepted:

1. implementation is checked against the selected Story criteria
2. a Reviewer looks for correctness issues, edge cases, and risk
3. technical validation checks real user journeys through the delivered entry point
4. failed evidence sends the work back for correction
5. a human-controlled acceptance point decides what happens next

AIM does not replace tests or guarantee correctness.
It makes review, verification, and correction normal rather than optional cleanup.

Raw observations support the quality assessment, including complete-result time
when it matters. A maintained map of important user journeys and a runnable
verification entry help future changes repeat the right checks. Missing or
failed evidence stays visible until corrected or resolved by the responsible
owner.

The [retained Enigma M3 results](../features/aim-enigma-evaluation.md) show
**96.5/100** for GPT-6 Luna with AIM in the latest assessment, compared with
**49.8/100** for the [historical Luna-only delivery](../features/aim-3.2-enigma-m3-case.md).
The earlier AIM result was **93.5/100**. Both used the same model, high reasoning
effort, brief and scoring weights. Different dates and delivery conditions mean
this is a historical comparison, not a fresh paired experiment or a general
quality or cost guarantee. The latest version of AIM includes later changes
outside this score; the assessed native delivery remained unfinished.

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

## Shared Learning During Delivery

Relevant shared lessons are recalled during delivery; new verified reusable
corrections and independently confirmed failures contribute generalized advice
with existing proof. An unverified remedy stays proposed. No manual
reflection command or routine report is required. These agent responsibilities
do not guarantee that every repo or event has contributed.

The old `reflect` and `reflect-all` names are retired compatibility aliases for
bounded read-only registry views. Maintained project facts stay in their own sources. A concrete stale fact,
contradiction or missed-learning question can justify a targeted authorized audit.
Advice is evidence to assess, not authority to change requirements or other repos.

Advice keeps its applicability and proof so an agent can assess whether it fits
the current problem. Sensitive project details remain at their source.

## Your Tokens Are Valuable

AIM treats unnecessary context as a delivery cost.

It starts with:

1. active state
2. the compact repository profile
3. directly affected files
4. the nearest useful validation

It expands when evidence is missing, facts are stale, risk is higher, or the user asks for deeper work.

Cost profiles let operators choose normal, narrow, or deeper runtime attention without changing AIM's ownership and gate model.

Confirmed checkpoints and still-applicable results can be reused without
repeating the same reads and checks. Existing approvals and answers stay bound
to their original scope. These controls are designed to reduce repeated work;
they do not promise a fixed token, time or cost reduction.

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

## Keep the whole product in view

Requirements and delivery have different jobs. User Stories make distinct needs
visible and independently prioritizable. Epics explain the larger outcomes;
delivery plans select the next useful work; increments capture the result.

This gives users a board of actual needs, planning across Epics and acceptance
that remains traceable to individual criteria. The established engineering,
repository knowledge, review and validation practices support that model.
Existing work keeps its original identity and history. See the
[Story contract](../workflow/user-stories.md).
