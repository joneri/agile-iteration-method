# User Stories and the product backlog

AIM 4.0 separates requirements from delivery. Start with an intent. PO discovers
one or more Epics and owns product priority. TDO creates and refines their User
Stories and acceptance criteria, and owns the coherent increment commitment.
Implementing, integrating and verifying that selection prepares it for user
acceptance.

## The model

| Concept | Question it answers | Owner |
| --- | --- | --- |
| Intent | What problem or desired result brought us here? | User, framed by PO |
| Epic | What larger outcome serves that intent? | PO |
| User Story | Who needs what, and why is it valuable? | TDO, within PO-owned Epic intent and product priority |
| Delivery plan | Which ready Stories do we implement next, and how do we verify them? | TDO with PO priority |
| Increment | What integrated, working improvement did we deliver? | TDO owns delivery; user owns acceptance |
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

PO owns Epic intent, outcomes, audience, scope, overall quality and product
priority, including priority between Stories. TDO owns Story creation, refinement,
acceptance criteria, dependencies and the coherent delivery commitment. Resolve
conflicts together: technical sequencing must not silently reprioritize product
goals, remove necessary scope or lower quality. Technical tasks live under
the selected Story or delivery plan; do not disguise implementation layers as
personas or manufacture a user need for an unrelated task.

A ready Story has:

- A stable `US-*` ID and exactly one primary `epicId`.
- A concise title, relevant user or actor, need and benefit.
- Explicit, observable acceptance criteria with stable criterion IDs.
- PO priority, with a smaller positive number ordered first.
- Enough refinement to expose relevant dependencies, failure behavior and risks
  in the supporting delivery plan or evidence.

Story count and size serve clarity of need, ownership and verification; there is
no count target or requirement to deploy each Story independently. Preserve the
user journey and coherent design. Shared quality requirements may be referenced
from a common contract. Do not introduce Story Points, generic complexity scores
or invented time estimates as required planning or capacity fields.

Open Epics and their intent can evolve after an accepted delivery. Historical
selections retain their original snapshots; active selections freeze the relevant
requirements. Closed Epics and accepted Stories remain immutable.

Draft Stories remain visible but cannot enter a delivery selection. Changing
requirements on selected or accepted Stories cannot silently invalidate the
approved scope. Preserve the selected criteria and agreed increment outcome as
the review baseline; never rewrite them to make delivered behavior pass. Technical
choices may change within mandate. Changed product outcome, scope or lowered
requirements need the applicable owner decision. Use existing history and
decision surfaces to retain the original commitment, decision, reason and
remaining need; never overwrite accepted requirements or results.

## Questions and reusable decisions

Apply [Autonomous interaction](autonomous-interaction.md) before interrupting the
user and when resuming. Link material questions and answers to existing Story
and criterion IDs and their original evidence. The product ledger remains the
only Story/gate state; question receipts cannot accept Stories. A blocked choice
halts its dependent action, not independent work already within the plan. Changed
decisions use only supported refinement/rework paths and retain historical
acceptance; approved scope changes retain the tooling limitation below.

## Planning, gates and acceptance

TDO selects ready Stories according to PO priority, dependencies and capacity.
The selection can cross Epic boundaries. A delivery plan names exact Story IDs,
the coherent usable capability or improvement it will deliver, why the selected
Stories suffice, implementation boundaries and checks for individual needs and
the integrated result. An easy-to-finish subset is insufficient if it misses the
agreed value. Verified learning can be the primary outcome only for an explicitly
exploratory assignment, never as a substitute for an ordered functioning product.
One active delivery selection is supported in a product backlog. The selected requirement snapshot binds the plan approval.

The commitment covers every selected Story through implementation, integration
and verification across sessions and context windows. A session ending or some
closed Stories cannot make an incomplete increment finished. TDO chooses
sequential or parallel execution from dependencies, integration risk, resources
and existing mandate; parallel work grants no additional agents or budget.
Verify parts and review consequential risks early, integrate as soon as relevant
parts can work together, then review and validate the whole increment. Each Story
does not require a separate full role and acceptance cycle.

If a real blocker or mandate/resource conflict prevents completion, preserve
finished work, decisions and remaining commitments, report the gap and propose
a concrete path forward. Do not silently defer scope or exceed the mandate to
force completion. Verified implementation and user acceptance remain distinct;
waiting for acceptance neither repeats implementation nor authorizes consent.

The integrated delivery role loop remains `PO → TDO → Dev → Reviewer → TDO → PO`:

- Gate A: relevant Epic direction and Story requirements are understood.
- Gate B: the precise Story selection and plan are approved. A clearly scoped
  response can authorize A and B together; do not ask again for authority
  already given by the user.
- Gate C: Dev has implemented the selection and hands it to Reviewer.
- Gate D: review has passed and TDO validates the current result.
- Gate E: the user accepts the explicitly named Stories after validation.

Reviewer independently checks whether the decomposition covers the agreed
contribution to Epic intent as well as every selected criterion and the actual
integrated product. The entire Epic need not finish in this increment. Review
and validation must trace evidence to every selected Story. Passing a suite
alone does not prove all criteria or product quality. The coordinator records
what each check establishes, its limitations and relevant counterevidence. A correction
invalidates affected review and validation evidence; re-review and reverify
affected criteria and integrations, reusing unchanged relevant evidence. A Story
is Done only after its criteria are proven and acceptance authority is recorded.

The current helper has no approved-scope replanning transition. `rework` corrects
implementation against the same frozen scope; `cancel` releases only an unapproved
plan. If an approved commitment cannot be met, use `block` with the obstacle and
remaining commitment and present the concrete owner decision needed. Even an
explicit scope-change decision does not make unsupported ledger edits valid:
preserve the original scope/history and report the tooling limitation rather than
rewriting selected requirements or inventing a migration.

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

Users may explicitly remove legacy workspaces through the trusted
`aim_legacy_cleanup.py` preview/apply flow. Offer this when opening a Control
room that detects older data. Cleanup preserves the current product ledger and
its referenced evidence, including evidence stored inside an older workspace.
Unreferenced classified legacy data is deleted without an archive copy; unknown
files remain. This optional cleanup does not migrate or accept Stories.
