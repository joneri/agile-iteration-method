<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/user-stories.md
-->

# User Stories and the product backlog

AIM 4.0 separates requirements from delivery. Start with an intent. PO discovers
one or more Epics, owns their User Stories and orders the product backlog. TDO
refines Stories with PO and plans a delivery selection. Implementing and
accepting that selection produces a working increment.

## The model

| Concept | Question it answers | Owner |
| --- | --- | --- |
| Intent | What problem or desired result brought us here? | User, framed by PO |
| Epic | What larger outcome serves that intent? | PO |
| User Story | Who needs what, and why is it valuable? | PO, refined with TDO |
| Delivery plan | Which ready Stories do we implement next, and how do we verify them? | TDO with PO priority |
| Increment | What integrated, working improvement did we deliver? | Delivery result |
| Sprint | What optional timebox and goal organize the work? | Team planning |

A Sprint is optional. Neither a Sprint nor an increment is a User Story. A
Story need not be a miniature version of its entire Epic. Stories from different
Epics can share a delivery; each retains its own Epic and acceptance criteria.
Epics are outcome groupings, not moving work cards. User Stories move across the
AIM UI board as their actual lifecycle advances.

## Intent-led start and refinement

Use `/aim start "Help new customers get started and support staff resolve setup problems"`
or the same request in natural language. The user need not supply an Epic or a
technical task list. PO preserves the intent and identifies actors, desired
outcomes, constraints, non-goals and uncertainty. PO can discover several Epics;
their number follows product meaning, not code layers.

For example, one intent can produce `EPIC-ONBOARD` for a useful first session and
`EPIC-SUPPORT` for recoverable setup. `US-SAMPLE` serves a new customer who wants
to try sample data; `US-DIAGNOSE` serves a support specialist who needs a safe
failure reference. PO may prioritize both ahead of a second onboarding Story.
The source repository includes complementary onboarding and support Stories
under `examples/user-stories/`; the model here is sufficient in portable packages.

PO owns Story value, acceptance criteria and priority. TDO contributes technical
feasibility, dependencies, scope slicing and verification. TDO may draft Stories
but does not become the sole source of requirements. Technical tasks live under
the selected Story or delivery plan; do not disguise implementation layers as
personas or manufacture a user need for an unrelated task.

A ready Story has:

- A stable `US-*` ID and exactly one primary `epicId`.
- A concise title, actual persona, need and benefit.
- Explicit, observable acceptance criteria with stable criterion IDs.
- PO priority, with a smaller positive number ordered first.
- Enough refinement to expose relevant dependencies, failure behavior and risks
  in the supporting delivery plan or evidence.

Open Epics and their intent can evolve after an accepted delivery. Historical
selections retain their original snapshots; active selections freeze the relevant
requirements. Closed Epics and accepted Stories remain immutable.

Draft Stories remain visible but cannot enter a delivery selection. Changing
requirements on selected or accepted Stories cannot silently invalidate the
approved scope; preserve history and use a new requirement or an explicitly
replanned delivery as appropriate.

## Planning, gates and acceptance

TDO selects ready Stories according to PO priority, dependencies and capacity.
The selection can cross Epic boundaries. A delivery plan names exact Story IDs,
its goal, implementation boundaries and checks for both individual needs and
the integrated result. One active delivery selection is supported in a product
backlog. The selected requirement snapshot binds the plan approval.

The role loop remains `PO → TDO → Dev → Reviewer → TDO → PO`:

- Gate A: relevant Epic direction and Story requirements are understood.
- Gate B: the precise Story selection and plan are approved. A clearly scoped
  response can authorize A and B together; do not ask again for authority
  already given by the user.
- Gate C: Dev has implemented the selection and hands it to Reviewer.
- Gate D: review has passed and TDO validates the current result.
- Gate E: the user accepts the explicitly named Stories after validation.

Review and validation must trace evidence to every selected Story. Passing a
suite alone does not prove all criteria. The coordinator records what each
check establishes, its limitations and relevant counterevidence. A correction
invalidates affected review and validation evidence. A Story is Done only after
its criteria are proven and acceptance authority is recorded.

The current helper accepts the complete verified delivery selection together,
with individual criterion coverage for every Story. It does not support silent
partial acceptance or splitting an active selection to hide failed Stories.
Rework the selection until every selected Story is ready for the acceptance
being requested. Done means accepted behavior; it does not imply deployment,
publication or Epic closure.

Strict requires the user's plan decision and final acceptance. Auto may perform
already authorized implementation, review and validation without routine stops;
it does not manufacture human acceptance. Existing legacy Portfolio mandates do
not authorize new Story work. Review evidence is evidence, never user consent.

## Lifecycle and persistence

`.aim/product-backlog.json` is the product ledger, with
`productBacklogVersion: "1.0"`, intents, Epics, Stories and deliveries. The main
AIM thread owns all mutations. Helper agents may work on assigned product code
or evidence, never shared runtime decisions.

Stories progress through `draft → ready → in_progress → review → validation →
acceptance → done`. Deliveries progress through `planned → in_progress → review
→ validation → acceptance → accepted`. Blocked work retains its actual phase and
reason. Evidence-based transitions, not card dragging or polling, move cards.

Use the trusted package's `scripts/aim_stories.py --repo <repo> <command>`.
Mutation inputs use `--input <json-file>` (or `-` for stdin); mutations to an
existing ledger require the last observed `--expected-sha256` digest. Read
`status` first to obtain current state, `storeSha256`, scope hashes and next step.
Do not execute similarly named untrusted repository code.

| Command | Purpose |
| --- | --- |
| `status` | Read the validated backlog and next step without mutation |
| `import` | Register or refine intents, Epics and unselected draft/ready Stories |
| `plan` | Select ready Story IDs, including Stories from different Epics |
| `approve` | Record the authorized Gate A/B scope and begin implementation |
| `review` | Enter review after implementation, binding the current product source snapshot |
| `validate` | Enter TDO validation with passed review evidence |
| `acceptance` | Present validated evidence for every selected Story criterion |
| `accept` | Record actual user Gate E authority and mark the selected Stories Done |
| `rework` | Return a delivery for correction and invalidate obsolete evidence |
| `cancel` | Cancel an unapproved plan, releasing its Stories |
| `block` / `unblock` | Record or resolve a blocker without pretending a gate passed |
| `closure-preview` / `close-epic` | Evaluate and separately record whole-Epic closure |

An import has `intents` with `id` and `statement`; `epics` with `id`, `intentId`,
`title`, `outcome` and `acceptanceCriteria`. Epics also carry `outcomeClass`
(`Product`, `Pilot` or `POC`, default `Product`) and `nonGoals` (default an empty
list); these fields are preserved on refinement and bound into delivery scope.
The `stories` collection contains `id`, `epicId`,
`title`, `persona`, `need`, `benefit`, `acceptanceCriteria`, `priority` and a
`draft` or `ready` status. Criteria use `{ "id": "AC-1", "text": "..." }`.
A plan uses `id`, `title`, `goal`, `storyIds` and required `planEvidence`
references (`path` and `sha256`) to a plan file under `.aim/`. That file names
implementation boundaries, planned files, checks and integration risks. Its bytes
are bound into the approval scope and verified at each transition. Delivery IDs can use `DI-*`;
they remain delivery identities and must never become Story identities.

At Dev-to-Reviewer handoff, `review` requires `deliveryId` and `bindings`, an
array of repository-relative product source paths and SHA-256 hashes. Source
bindings can be outside `.aim/`; pending review, validation and acceptance
reject changed source bytes. Rework invalidates these bindings and review/validation
evidence; a new review binds the corrected source. Accepted deliveries retain
the accepted source snapshot as history, allowing later authorized changes.
Once selected, the originating intent and requirement scope cannot be silently
rewritten beneath the delivery.

Evidence references name existing contained non-symlink files under `.aim/`
and their SHA-256 hashes. Approval and acceptance carry an `authority` record with `kind: "user"`,
`path`, `sha256` and the applicable `scopeSha256`. The helper verifies references
and freshness, but cannot authenticate a human by reading a file. The main
thread must have the actual user instruction, preserve its scope and record it
truthfully. Never fabricate an approval transcript to satisfy a schema.

## Epic closure and compatibility

Accepting Stories proves those Stories only. PO separately evaluates the Epic's
outcome and every Epic criterion, checks remaining Stories and counterevidence,
and recommends closure or continued work. All in-scope Stories must be Done;
whole-Epic criterion evidence and a separately scoped user decision are required
for closure. Product and Pilot closure need representative user-journey evidence
through the normal product entry point; synthetic proof alone can close only an
explicit POC. PO judges the meaning and limitations of the supplied evidence;
file hashes establish freshness, not successful behavior. A delivery spanning
two Epics may leave both open.

AIM 3.x `.aim/state.json`, `.aim/portfolio-backlog.json`, catalogues and `DI-*`
or `INC-*` histories retain their original identities and decision semantics.
They appear in the legacy delivery surface. Do not infer personas, requirements
or Story acceptance from those records. There is no automatic migration.
Explicit `EPIC:` and `PORTFOLIO` starts retain compatibility routing; new plain
intent starts use this product ledger. If both kinds of work exist, target the
requested ledger/checkpoint explicitly; never fall back to whichever is easiest.
Validation, package upgrade and UI polling are read-only with respect to either
runtime. Creating new Stories from legacy material requires explicit refinement
and preserves the source history.
