# AIM UI

> **Beta:** AIM UI is ready for real local evaluation, but its multi-Epic and
> card-decision experience is still evolving. The safety boundary is not Beta:
> the browser cannot pass Gates or write repository runtime state. Its one
> bounded write endpoint can only dispatch an exact reviewed action to the
> already-bound authoritative Codex task.

AIM UI is a local browser control room for requirements and delivery evidence.
It opens on **Increment**, showing the coherent delivery selected from
`.aim/product-backlog.json`: goal, selected Stories, checkpoint, criterion
evidence and user acceptance. The **User Stories** tab retains the requirements
board, with Epic context and product priority on each card.

All current-product views share the validated product ledger: **Increment**, **Graph**,
**User Stories**, **Discuss**, **Plan increment**, **Delivery data**, **Roles**
and **Accepted increments**. An explicit workspace selector opens retained **legacy workspaces** and
their original controls. Existing records are never automatically migrated,
relabelled or counted as Story acceptance. A broken product ledger stays visibly
unavailable instead of silently switching to old work.

## User Stories board

For a runnable browser check of planning and stale-selection behavior, use the
[project verification recipe](aim-ui-verification.md). It creates an isolated
synthetic workspace and preserves raw proof after cleanup.

The board columns are **Backlog**, **Ready**, **In progress**, **Review**,
**Validation**, **Acceptance** and **Done**. Draft Stories appear in Backlog;
all other movement reflects persisted Story lifecycle transitions. Polling,
filtering and opening a card cannot approve work or mutate the backlog.

Cards show Story ID, priority, title, Epic, persona, need and benefit. Expand a
card to inspect acceptance criterion IDs and text; delivery references and
contained evidence links preserve traceability. Filter by Epic or keep All Epics
to compare needs across outcomes. Stories are ordered by priority within each
column. A delivery selection can contain Stories from different Epics.

**Copy start intent** prepares an intent-led `/aim start` prompt. Contextual
Story actions prepare a discussion about refinement or planning; accepted Stories
lead to a follow-up user need rather than rewriting their accepted requirements.
Delivery references open the corresponding selection and evidence. Copying a
prompt never changes runtime state. Actual changes go through the main AIM thread
and the [Story lifecycle](../workflow/user-stories.md).

An empty board explains intent discovery and PO/TDO refinement. Historical Epic/Increment work
remains available through the legacy workspace selector. An invalid product
ledger shows a diagnostic instead of guessed or stale Story cards. Refresh
preserves card identity, expanded criteria and keyboard focus. Actual phase
changes can animate; reduced-motion preferences are respected.

## Follow the current increment

Increment shows the selected Stories, their Epic context, delivery goal,
checkpoint, blocker and supporting evidence. Plan approval and final acceptance
are shown separately. Criteria with recorded evidence are not a completion or
pass rate. Stories keep their recorded scope order; TDO chooses execution order
from dependencies rather than simply following PO-owned product priority.
A delivery can cross Epic boundaries;
its Story selection and approval scope remain explicit. The contextual handoff
names the product ledger, observed digest and delivery identity. The receiving
AIM task reloads and checks the current scope before making changes. Plan approval
and final acceptance remain decisions of the actual designated owner under
explicit human authority; accepted history identifies the actor who decided.
Current Story controls use reviewed
chat handoffs; direct legacy Start/Approve dispatch does not apply to them.

Accepted delivery history preserves the selection and its acceptance evidence.
Done Stories and accepted deliveries do not imply that their Epics are closed.

## Follow dependencies in Graph

Open **Graph** to see the current increment's outcome and the path through its
activities. Select an activity to inspect its user need, prerequisites, file
responsibility, skills to resolve and existing raw proof. Text labels identify
ready, waiting, recorded running, failed and stale work; lines show dependencies.
Keyboard selection, the open inspector and focus survive normal polling. On a
phone the same work appears as a vertical sequence with explicit prerequisites.

**Copy next assignment** includes the observed ledger and scope, bounded work
and inputs. A stale or failed activity can offer **Copy corrective assignment**
when prerequisites and capacity permit a new attempt. Review and send it through
the existing AIM session. Copying, selecting or refreshing never starts agents
or changes the ledger. Recorded session IDs describe receipts, not live presence.

Editing a bound source or proof changes the affected activity to **Needs new
evidence** and prevents dependants from being offered as ready. The graph is
derived from the existing ledger and files; it creates no separate status file.
Deliveries without an execution plan show their recorded native checkpoints.
An invalid ledger remains unavailable. See [AIM Graph's execution contract](../workflow/adaptive-execution.md#aim-graph).

Verify this route with `python3 scripts/verify_aim_graph.py`. It launches an
identified native instance on a disposable synthetic delivery, drives the real
Graph controls, records progress, changes an input and observes stale proof.
Raw observations, desktop/mobile screenshots and a browser trace are preserved.

## Plan across Epics

Plan increment groups the current Stories by their Epic outcomes. Select ready Stories
across those groups to prepare a delivery-planning proposal. The proposal carries
the exact selected identities and observed ledger digest. It is not approval of a
plan. An active delivery prevents another selection; a changed ledger clears
obsolete selection so it cannot be reused silently. Legacy Portfolio Auto and its
capacity policy appear only in the legacy workspace scope.

## Understand outcomes and responsibility

Delivery data counts the current ledger's Stories, accepted deliveries and open/closed
Epics. Its acceptance timeline links to recorded evidence. Throughput includes
only valid explicit acceptance timestamps; unavailable or future timestamps are
excluded and explained. Current delivery records do not store approval timestamps,
so AIM UI does not invent approval-to-acceptance duration. Development effort,
agent usage and elapsed delivery time are different measurements.

Roles describes each AIM role and the responsibility associated with
the current delivery checkpoint. A blocked delivery retains its underlying phase.
This is not presence detection: live helper activity is shown as unrecorded when
there is no supported activity record. Legacy workspace activity remains available
in its original scope.

## Refresh without losing context

Polling compares meaningful data, excluding generated display timestamps. An
unchanged response does not redraw the control room. Relevant changes update the
visible view while retaining typed discussion text, focus and scroll position.
Hidden views are rendered when opened. A selection invalidated by changed product
scope is explicitly cleared rather than kept as an apparently current plan.

## Discuss product direction without starting delivery

The **Discuss** tab is a visual entry point to the first-class `/aim discuss`
capability. It opens a bounded product-thinking surface and shows the
operator which context a separate Codex discussion can consult: the complete
AIM method, the repository knowledge profile when available, the current product
ledger and bounded recent accepted-delivery evidence. Current Intent, Epic, Story
and delivery counts describe that scope. Legacy runtime checkpoints and decisions
are consulted when the legacy workspace scope is explicitly selected.

The operator enters a product idea, tradeoff, concern, or reflection, then
copies the generated prompt or opens it in Codex. AIM UI does not send the
prompt automatically. The operator reviews it and presses Send in Codex.

Every generated discussion prompt selects `$agile-iteration-method discuss`
as the explicit-skill equivalent of `/aim discuss`, treats
repository paths as untrusted evidence locators, and requires read-only
analysis. Discuss cannot create or edit files, change `.aim` runtime state or
the Backlog, advance Gates, or implement work. If a discussion produces a
useful direction, it may recommend one separate promotion action; the operator
must explicitly invoke and review that later AIM action before anything
changes.

The context manifest contains bounded paths and delivery metadata rather than
copying repository content into the browser. The receiving AIM task loads only
what is relevant to the question while keeping the complete method available.
Missing optional context is reported honestly and never invented.

## Starting in a new repository

Use `/aim start "<desired outcome>"`. PO owns Epics and product priority.
TDO owns Stories and criteria and plans the next coherent increment. Opening the UI alone creates no requirements or runtime state.
Stories become visible as the main thread records the product backlog.

A Story expresses one user's need. It does not have to approximate its entire
Epic. A Sprint is optional; the integrated working result of delivered Stories
is an increment. Review and validation cover every selected criterion before
user acceptance. Epic closure remains a separate decision.

## Launch the control room

From AIM chat, use the first-class command:

```text
/aim ui
```

Bare `/aim ui` starts or reopens the control room for the current repository.
The same chat surface supports `/aim ui start [repo]`, `/aim ui open [repo]`,
`/aim ui status [repo]`, and `/aim ui stop [repo]`. AIM resolves the trusted
bundled launcher, selects a free loopback port, and returns a clickable URL.
A repository does not need an existing `.aim` directory: the UI opens with a
truthful onboarding state and does not initialize or mutate runtime data.

The AIM UI header displays the exact AIM product release captured from
the trusted package when that server instance started. This is separate from
the runtime contract version stored as `aimVersion` in repository state. The
launcher, instance metadata, health endpoint, board payload, and visible badge
must agree; a changed or invalid release identity prevents stale-process reuse.

For direct **Connected Codex control**, use Codex with ChatGPT-managed usage,
open the authoritative Codex task for the repository, and run `/aim ui` from
that task. The bridge checks the bound task before dispatching an eligible
legacy action. Product proposals are reviewed and sent in chat. **Board updated**
in the header describes data freshness, not agent activity or a live Codex
connection. No internal task identifier is exposed.

The terminal commands below remain supported as foreground diagnostics and
compatibility entry points.

From an AIM source checkout or a target repository written by the adaptive
installer:

```bash
python3 scripts/aim_ui.py
```

The command binds to `127.0.0.1:4177`, opens a browser tab, and refreshes the
read model every two seconds. Use `--no-browser`, `--port`, or `--repo` when a
different local launch shape is needed.

Zero-repo-write adaptive footprints install the UI under the user's AIM home
distribution:

```bash
python3 ~/.aim/installs/agile-iteration-method/scripts/aim_ui.py \
  --repo /path/to/repository
```

The portable public Agent Skill now bundles the same dependency-free launcher,
server, and UI assets used by `/aim ui`. It does not write those files into the
target repository. Adaptive installations continue to place the payload in the
selected repo or external AIM home according to their reviewed footprint.

The launcher fingerprints its launcher, Python server, and served HTML,
JavaScript, and CSS as one protocol-compatible payload. Instance metadata and
`/api/health` must report that same fingerprint before `/aim ui` may reuse a
running process. After an in-place upgrade, `status` reports a verified but
incompatible instance as stale; the next start signals only that exact
repository/instance/PID relation, waits for it to leave, and starts the aligned
payload. Missing identity evidence removes metadata without signalling the
named PID. Repository runtime files and accepted evidence remain read-only
throughout replacement.

When launched from a Codex AIM task, the instance also binds to that task's
opaque `CODEX_THREAD_ID`. Only a SHA-256 binding fingerprint is retained in
instance metadata or returned by health checks; the browser never receives the
thread id. Launching the same repository from a different Codex task replaces
the verified instance so actions cannot silently continue an older owner.

## Legacy delivery control and Portfolio reference

The remainder of this guide documents the preserved **Epic/Increment runtime**
and its Delivery control, Portfolio, history and connected-action behavior.
These sections apply to existing workspaces and explicit legacy `EPIC:` or
`PORTFOLIO` starts. Their Gates and mandates cannot accept new User Stories.
The User Stories board above uses its own product ledger and evidence lifecycle.

## Declare several Epic workspaces

Without configuration, AIM UI reads the existing root `.aim` workspace exactly
as v1 did. No migration is required.

To combine workspaces, add `.aim/ui-portfolio.json`:

```json
{
  "portfolioVersion": "1.0",
  "workspaces": [
    { "path": "." },
    { "path": "workspaces/checkout-recovery" }
  ]
}
```

Paths are relative to `.aim`. Each directory is a complete AIM workspace with
its own `state.json`, `epic.md`, `increments/`, `decisions/`, `reviews/`, and
optional `agent-activity.json`. The structure is defined by
`schemas/aim-ui-portfolio.schema.json`.

The catalog only controls discovery. It does not contain status, roles, gates,
acceptance, scheduling, or agent instructions. A workspace's `state.json`
remains authoritative for its Epic, and the main AIM thread for that workspace
remains the only state writer.

Closed workspaces may remain in this catalog without consuming delivery
capacity. The catalog has no item-count ceiling: bounded file size, bounded
paths, containment and symlink checks, unique identities, and validated
workspace state protect discovery. AIM UI reports retained workspace history
separately from active use of `maxActiveEpics`.

When this catalog exists, a normal `/aim start "EPIC: ..."` creates new work in
a dedicated `.aim/portfolio/<EPIC-ID>/` workspace through AIM's trusted start
transaction. The transaction reserves a canonical `DI-*`, registers the
workspace, and verifies the same read model served by `/api/board` before Gate A
is shown as ready. Invalid, stale, active-capacity-full, colliding, escaped, or
symlinked input leaves no root checkpoint or retained partial workspace.

If the workspace index is missing, AIM UI displays intact work discovered in
the root workspace and the supported `portfolio/` and `workspaces/` locations.
The browser stays read-only. On an authorized start or resume, AIM reconstructs
that index automatically without changing checkpoints, plans, approvals, or
history. Existing running work still counts toward capacity.

When a catalog is missing, malformed, oversized, or unreadable, the board
discovers each contained workspace separately in the supported locations.
Unreadable neighbors are isolated. A readable workspace omitted from an
otherwise valid catalog remains visible too. These observed workspaces expose
no Start or Approve actions; visibility does not establish runtime authority.
Catalogued, unambiguous work retains its existing action rules.

When saved task evidence is unreadable or contradictory, available work remains
visible and technical details stay in the diagnostic view. The status identifies
a partial view rather than a healthy empty project. Normal polling restores the
full view when the underlying files become readable again. A decision should
describe the uncertain task or scope; users do not choose JSON formats or
perform routine index maintenance. Existing indexes are not silently replaced.

## Control focus and concurrent capacity from chat

The main AIM chat may add `.aim/portfolio-control.json` when the operator wants
an explicit limit:

```json
{
  "controlVersion": "1.0",
  "maxActiveEpics": 2,
  "focusedEpicId": "EPIC-AIM-UI",
  "updatedAt": "2026-08-21T18:20:00Z"
}
```

Natural requests such as `Set portfolio capacity to 2`, `Focus EPIC-AIM-UI`,
and `Activate INC-UI-001` are handled by the authoritative AIM chat. The chat
checks capacity before opening a new runtime workspace. A full portfolio
rejects new activation with a useful next action; an existing Epic can still
resume.

Focus is presentation and chat targeting only. It does not pause other Epics or
approve their gates. If capacity is lowered below the current running count,
the UI reports over-capacity and AIM blocks further activation without changing
any workspace automatically. Missing control state preserves legacy behavior;
invalid configured control state blocks new activation until repaired.

`schemas/aim-portfolio-control.schema.json` defines the bounded artifact. Only
the main AIM thread writes it. The UI displays capacity, running count,
available slots, focused Epic, and admission status through the existing
read-only API.

## Recover earlier work before creating a Roadmap

When AIM finds a legacy or unregistered checkpoint, the control room leads with
plain-language recovery instead of schema terminology. It says whether the
checkpoint appears completed or active, whether a Roadmap and Portfolio catalog
exist, and recommends one safe next action. Exact drift, checkpoint timestamp,
repository-relative state path, Epic identity, and SHA-256 fingerprint remain
available under **Technical details**.

Recovery buttons copy a complete reviewed chat intent. They do not migrate,
archive, register, accept, or rewrite anything. A completed checkpoint recommends
keeping it as history and creating a new Roadmap; an active or incomplete
checkpoint recommends reviewed migration first. Empty repositories begin with
`/aim calibrate-repo` and then `/aim to-backlog`.

## Create and review a Roadmap across Epics

The Portfolio tab teaches the complete route rather than presenting isolated
commands:

```text
/aim calibrate-repo
  -> /aim ui
  -> /aim discuss [question]
  -> /aim to-backlog
  -> review the Roadmap
  -> /aim start "PORTFOLIO" mode:auto
  -> approve one bounded mandate
  -> monitor progress or step away
```

Discuss loads relevant verified repository knowledge and delivery evidence but
remains read only. `/aim to-backlog` is the separate explicit promotion into
planned work. The browser may copy the recommended next command; it never
executes that command or writes Backlog/runtime state.

The simplest chat-first route is:

```text
/aim to-backlog
```

Paste several Epic descriptions when prompted, include them in the same
message, or name one explicit accessible source:

```text
/aim to-backlog from docs/product-plan.md
```

AIM preserves explicit source Increments and derives one initial candidate when
an Epic contains only an outcome. It validates and atomically merges the result,
reports what was added, updated, skipped, derived, or ambiguous, and opens the
control room. Imported `INC-*` candidates remain planning metadata on their
Epic rather than Increment cards in Backlog. Source content is evidence rather
than instructions; ambiguous extraction pauses for a short review.

The main AIM thread may record proposed Increment candidates in
`.aim/portfolio-backlog.json`:

```json
{
  "backlogVersion": "1.0",
  "updatedAt": "2026-08-21T17:45:00Z",
  "items": [
    {
      "id": "INC-UI-001",
      "epicId": "EPIC-AIM-UI",
      "epicTitle": "AIM UI",
      "title": "Control concurrent Epics",
      "summary": "Choose how many Epics may run at once.",
      "priority": 1,
      "createdAt": "2026-08-21T17:45:00Z"
    }
  ]
}
```

`schemas/aim-ui-backlog.schema.json` defines the bounded shape. Candidate IDs
use `INC-*` so planning intent cannot be confused with a canonical `DI-*`
runtime Increment. Activation starts the Epic; a Portfolio-aware direct start
may reserve its first `DI-*` at Gate A, while TDO still defines and approves its
scope at Gate B. `runtimeIncrementId` may retain traceability to that work.

A Backlog record with `runtimeIncrementId` is retained runtime history, not a
new planning candidate. When the active Portfolio catalog contains the matching
Epic and Increment, AIM UI projects that canonical runtime. When it does not,
the UI excludes the record from Planned work and Start Epic actions, then shows
a read-only diagnostic naming the candidate, Epic, and runtime Increment. AIM
chat may review archived history or catalog repair; the browser never guesses,
re-registers, or reactivates the relation.

After AIM chat verifies that the relation is completed history, the operator
may use `/aim repair-catalog <candidate-id>`. AIM presents an immutable preview
binding the workspace, state, acceptance evidence, and source hashes before
requesting explicit approval. The approved transaction archives the contained
workspace unchanged, removes its catalog entry, retires the exact Backlog
record, and writes reversible audit evidence together. AIM UI only reflects the
result on its next poll; it never performs or approves the repair itself.

This file is planning input only. It may contain identity, description,
priority, and timestamps. It must not contain gate status, role transitions,
acceptance, scheduling locks, or agent instructions. Only the main AIM thread
writes it. AIM UI continues to accept only GET and HEAD. The read model rejects
a file larger than 1 MB, limits the array to 256 candidates, and enforces
field-level string ceilings so malformed planning input cannot grow without a
bound.

The Portfolio tab presents these stationary planning candidates as a Roadmap.
It previews the exact eligible order and a deterministic content hash before
execution. Eligibility is not inferred from a missing `runtimeIncrementId`
alone. The read model applies the same repository-bound activation preflight as
Start Epic, including canonical Epic allocation, contained catalog/workspace
relations, path collisions, configured capacity, Backlog freshness, and
contradictory runtime authority. A rejected candidate stays visible with one
actionable reason, but it does not contribute to `eligibleCount`, the immutable
snapshot, or the proposed mandate. Projection remains byte-for-byte read-only.

## Execute the Roadmap as one Portfolio

After populating the Backlog, start the whole ordered board from AIM chat:

```text
/aim start "PORTFOLIO" mode:auto
```

AIM previews the exact candidate order and asks for one bounded Portfolio
mandate. Once approved, the main AIM chat runs one Epic at a time through the
complete AIM lifecycle. The Portfolio view shows the run id, mandate, current
card, remaining count, pause reason, durable Gate checkpoint, and whether the
current decision derives from the Portfolio mandate. Individual cards show
queued, active, completed, or skipped Portfolio state.

The UI remains read-only. `.aim/portfolio-run.json` is a chat-owned checkpoint,
not a browser scheduler and not a replacement for each Epic workspace. Later
Backlog additions stay outside the immutable running snapshot. `/aim continue`
resumes only after AIM revalidates the snapshot and active workspace. Scope,
trust, validation, safety, concurrency, or user stop/change conditions pause the
run without losing completed work.

The **Execute this Roadmap** panel copies both the exact command and the current
snapshot identity into AIM chat. The copied intent still requires the normal
preview and one explicit bounded mandate; the browser never starts execution.
The panel explains that later Roadmap additions are excluded and that scope,
trust, safety, validation, concurrency, or contradictory-state escalation pauses
the run.

Portfolio Strict is not a defined multi-Epic start contract and AIM UI does not
display a non-working Strict command. Strict remains supported for ordinary
single-Epic execution.

## What the control-room tabs show

- Delivery flow, selected by default, with stationary rows for running and
  planned Epics plus an independent Recent Deliveries ledger for accepted
  history; completed Epics never remain in the priority rows merely to host it
- Portfolio, with active Epic, workspace, increment, and attention totals; chat-owned capacity; and one summary panel per Epic
- AIM DATA, with auditable delivery counts, throughput, elapsed delivery time,
  and evidence-linked accepted history
- People and agents, with each Epic's current canonical role and bounded helper-agent activity
- Closed Increments, with complete accepted history grouped by Epic
- proposed candidates summarized on stationary Epic cards without invented
  runtime work, with `Start Epic` available when portfolio admission allows it
- consistent Epic color and identity on summaries, people panels, filters, and cards
- aggregate view plus presentation-only focus controls for one Epic
- each Epic's current role, gate, mode, cost profile, status, and evidence
- bounded helper agents grouped beneath the Epic that recorded them
- explicit read-only integrity warnings when a declared, orphaned, invisible,
  or legacy-contract workspace cannot be projected truthfully
- the latest ten accepted Increments in the independent Recent Deliveries ledger

Filtering never changes runtime state. It only changes which already-read Epics
the browser presents. Delivery flow filters contain planned and open Epics;
Recent Deliveries remains a completion-ordered ledger rather than another
priority row. Switching from another view resets a selection that is not valid
on the bounded active board. All completed outcomes remain available through
Recent Deliveries, Closed Increments, AIM DATA, and the broader Portfolio view.

During a Portfolio handoff, `activation_pending` means the next candidate has
been selected but remains Planned until its contained workspace, canonical
state, and Backlog `runtimeIncrementId` have all been created and validated.
The previously accepted delivery remains visible throughout. A later
checkpoint without those runtime relations, or disagreement among candidate,
workspace, increment, and checkpoint identities, is projected as contradictory
and fails closed. The UI never repairs or fabricates runtime work.

## How AIM DATA measures delivery

AIM DATA is a read-only projection of the same contained workspaces already
validated by the control room. It does not add telemetry or a second analytics
store.

- Epic totals include valid canonical workspaces and distinguish running from
  completed Epics. Planned Backlog-only Epics are not counted as runtime work.
- Accepted Increment totals require validated Gate E acceptance evidence.
- Seven- and thirty-day throughput count only accepted Increments whose Gate E
  evidence contains an explicit timezone-aware `Accepted at` timestamp. The
  windows use the read model's UTC generation time.
- Elapsed delivery time is the median duration from the earliest explicit Gate
  B `Approved at` or `Timestamp` evidence to explicit Gate E acceptance.
- Accepted history remains visible when legacy evidence needs a file-time
  fallback, but that fallback is labeled and excluded from throughput and
  elapsed calculations.
- Every history row links to its contained Gate E evidence. Missing, malformed,
  contradictory, duplicate, or escaped evidence is isolated through the
  existing partial-health boundary rather than converted into a number.

The dashboard reports sample and exclusion counts next to time measures. When
no trustworthy sample exists, it says the measure is unavailable instead of
showing zero.

## Why cards move in Auto mode

The UI polls every declared workspace. The main AIM thread advances that
workspace under the normal gate contract; the next poll moves only the related
card. Other Epics retain their own positions.

Polling itself is visually quiet. AIM UI ignores volatile refresh metadata when
deciding whether the board changed, reuses stable Epic/Increment card nodes, and
leaves the Kanban untouched when authority is unchanged. A genuine column
change uses one brief transform-only handoff for the affected work ticket;
unrelated cards do not replay entrance effects. Reduced-motion preference
disables the handoff without changing the resulting state. Stable refresh also
preserves horizontal Kanban position and keyboard focus.

| AIM runtime state | UI column |
| --- | --- |
| initialized or awaiting Gate A/B | Backlog |
| implementation, paused, or blocked | Work in progress |
| review or TDO validation | In review |
| awaiting PO acceptance | Ready for release |
| accepted increment or completed Epic | Recent Deliveries, outside the row flow |

Epics do not move between these columns. The left Epic spine stays aligned with
its delivery row while canonical active `DI-*` cards move across the four flow
columns.
Gate A may therefore show an Epic with an empty row. Plan, WIP, review, and
decision artifacts for one `DI-*` are aggregated into one card and evidence set.

Recent Deliveries is intentionally a short recency ledger, not the history
store and not a fifth priority stage. The read model sorts accepted runtime
evidence by an explicit `Accepted at` timestamp when available, falls back to
the decision artifact modification time, and uses the numeric Increment identity
as a deterministic tie-breaker. Only the newest ten entries remain in this
compact ledger. Closed Increments shows every accepted card and never deletes
its runtime evidence.

Membership in Recent Deliveries, Closed Increments, and `acceptedCount`
requires validated Gate E acceptance evidence. A terminal state or a card in a
Done presentation column is insufficient by itself. Portfolio reconciliation
reports each failed terminal predicate separately—Backlog candidate, runtime
link, catalogued workspace, candidate identity, closed lifecycle, matching
Increment, Done state, and acceptance evidence—so one defect is not hidden
inside a compound warning.

`history.recentDeliveries` is a required launcher/backend/frontend compatibility
contract for this ledger. Binding lifecycle reuse to the payload fingerprint
prevents a newer frontend from silently interpreting an older backend response
as zero recent delivery activity.

Each Recent Deliveries entry keeps its Increment title, identity, parent Epic,
and acceptance time visible without hover. Activating it opens a keyboard-
accessible read-only detail view with canonical lifecycle and runtime labels,
available Increment/review/Gate E evidence, and workspace context. `View all`
opens Closed Increments. `Create follow-up Epic` prepares a reviewable AIM chat
proposal that references the source Epic and accepted Increment while requiring
a new Epic identity. It is not an action envelope, does not reopen the source,
and cannot mutate runtime state.

For a completed workspace with no active Increment, AIM UI projects the most
recent accepted Increment from the structured state contract:
`previousIncrementId`, `previousIncrementStatus: "accepted"`, Gate E, a
terminal-compatible Epic status, and the contained `gateEAcceptance` evidence
reference. Descriptive decision filenames are supported because the reference
and validated decision content carry the meaning. An invalid structured
reference fails closed with a board warning and is not rescued by a historical
filename. Compatibility discovery recognizes only
`<increment-number>-gate-e.md` and
`YYYY-MM-DD-gate-e-di-<increment-number>.md` for workspaces without applicable
structured history. The DI identity—not the calendar date or card title—keeps
same-day Increments distinct. Multiple supported files for one DI are
ambiguous and remain unaccepted with a compact diagnostic, except for one
verified legacy index chain. An explicit `Gate E acceptance index — DI-*` may
name one supported date-prefixed target in the same decisions directory; AIM UI
treats the pair as one acceptance only when both files accept only that DI,
their valid `Accepted at` instants match, and no additional supported decision
exists. A missing or malformed target, ordinary duplicate, mismatch, symlink,
or extra decision remains hidden with a diagnostic. New history should use
structured state-linked evidence rather than creating compatibility indexes.
Legacy Gate E metadata written as unordered Markdown list items is normalized
the same way as bare metadata fields; negative decisions and wrong Increment
identities continue to fail closed.

## Helper-agent visibility

Supplier runtimes do not expose one portable live-agent API. Each workspace may
therefore provide optional local observation evidence in
`agent-activity.json`:

```json
{
  "activityVersion": "1.0",
  "updatedAt": "2026-08-21T12:01:00Z",
  "agents": [
    {
      "id": "accessibility-review",
      "task": "Check keyboard flow",
      "status": "working",
      "canonicalRole": "Reviewer",
      "epicId": "EPIC-20260821-038",
      "incrementId": "DI-086"
    }
  ]
}
```

Supported statuses are `working`, `waiting`, `completed`, and `failed`. Missing
or malformed helper evidence is reported honestly. It never owns card position,
roles, gates, acceptance, or completion.

## Read-only and failure boundary

### Card action handoff

Eligible planned Epic cards expose `Start Epic`, which initiates the canonical
Activate intent for their next `INC-*`; hard-gate cards expose Approve and
Change. On Codex desktop the confirmation opens `codex://new` in
the repository with a bounded action envelope prefilled. Codex does not send it
automatically: the operator reviews the composer and presses Send. Other hosts
can copy the same intent.

When AIM UI was launched from the authoritative Codex task, eligible Start and
Approve buttons instead dispatch the already-projected envelope directly to
that bound task. Request change still uses the reviewed composer because it
requires new operator text. The background path recomputes the current board,
accepts only a byte-equivalent enabled envelope, and derives the prompt on the
server. It has no free-form prompt field.

The bridge starts the installed local `codex app-server` using its stable JSONL
surface. It requires `account/read` to report ChatGPT-managed auth, verifies the
bound id with `thread/read`, rejects active or persisted in-progress turns,
resumes only that thread, and calls `turn/start` without model, effort,
personality, working-directory, sandbox, permission, or approval overrides.
It never calls `thread/start`, `thread/fork`, `turn/steer`, or
`turn/interrupt`. A deterministic client message id plus a private, atomic
operational ledger makes retries and server restarts idempotent.

Queued, starting, running, checking, attention, unverified, unknown, completed,
and rejected states appear in a live region. `running` requires a returned turn
id or a read-only observation of that saved turn in progress. A completed Codex
reply triggers verification; it is not a completed AIM action.

Verification binds the original enabled envelope to its workspace and Increment.
Start requires a new candidate-to-runtime link and the corresponding visible,
authoritative workspace. Gate A and B require the requested Increment's coherent
runtime progression; Gate E requires matching structured acceptance evidence.
Observation-only workspaces, wrong identities, unchanged checkpoints, and
missing decisions cannot yield success. “Verified” means the requested AIM
transition is observed, not that product implementation is correct or the Epic
is complete. The private result records the checked time and observed state digest.

The private atomic ledger retains the envelope, target and returned turn id.
`/api/actions/latest` restores the current task's last action after a page or
server restart, including when the local port changes. Recovery observes the
saved result and, when available, reads the exact saved Codex turn. It never
resumes or submits a turn. Missing results remain unverified and are checked
again, at most once every five seconds while the UI is following the operation.
A quiet active turn is kept alive even when no event arrives for more than a
minute. A single buffered reader drains all events; an idle read interval never
terminates Codex. Startup request deadlines still apply.
A known failure keeps its explanation after refresh and restart; an outdated
Codex CLI is described plainly without exposing the raw service error. Reserved
Increments never display Gate E before acceptance.
Once a turn is known to be finished, checks read local results without reopening
Codex. A response lost after submission stays uncertain and cannot be retried as a
new send. Old completion records without evidence are shown as unverified.

Approval, permission, user-input, and MCP elicitation requests ask the operator
to continue in Codex; the bridge never answers them. Interrupted status requests
keep the board readable and resume polling, without declaring the action failed.
Operational metadata lives outside the repository with owner-only permissions;
verification and recovery never write AIM runtime artifacts. No status label
substitutes for a Gate or Epic acceptance decision.

Card position and decision publication are separate signals. A workspace may
opt into exact timing with the runtime-state extension below:

```json
"uiDecision": {
  "visibility": "preparing",
  "gate": "Gate E",
  "targetId": "DI-092"
}
```

`epicStatus` moves the card to the correct column immediately. While the marker
is `preparing`, the card explains that AIM is finishing the handoff and exposes
no decision controls. After review, evidence, and final handoff preparation are
complete, the main AIM thread makes its last state mutation: change visibility
to `ready` and advance `updatedAt`. Only an exact Gate and target match reveals
Approve and Request change; malformed or mismatched markers fail closed. The
resulting action envelope uses the final timestamp.

This marker controls presentation only. It cannot pass a Gate, authorize a
decision, or weaken receiver freshness checks. States without `uiDecision`
retain the legacy action timing for backward compatibility.

New v1.2 gate actions name the exact authoritative state file in
`authorityStatePath`, relative to the repository root. The receiving main AIM
thread resolves that contained path and reads it before any other runtime
state, then compares Epic, candidate or Increment, requested decision point, raw last-passed
checkpoint, runtime status, timestamps, and portfolio admission before mutation
and again immediately before writing. Mismatches are stale and change nothing.
Card prose is presentation; canonical ids and expected state fields form the
target.

Gate E is intentionally two decisions: Approve accepts the Increment, while
closing the Epic requires a separate explicit decision. Already-prefilled v1.1
actions resolve their older `workspace` field relative to `.aim`. Version 1.0
remains a safe compatibility input only when one unique contained workspace
matches; unknown versions fail closed. The prefilled prompt includes
this receiving order so safety does not depend solely on an installed skill's
freshness. Updating an installed AIM skill remains an explicit `/aim upgrade`
operation rather than a browser side effect.

- The local server accepts GET and HEAD plus one same-origin, size-bounded
  `POST /api/actions/dispatch` endpoint for exact projected envelopes.
- PUT, PATCH, DELETE, unknown POST paths, cross-origin requests, stale
  envelopes, and free-form background input are rejected.
- Portfolio workspaces must resolve beneath the selected repository's `.aim`.
- Absolute paths, traversal, duplicate paths, missing directories, duplicate
  Epic IDs, and symlink escapes are rejected or isolated with safe warnings.
- Evidence links remain restricted to files inside the repository `.aim` root.
- Static paths reject traversal and the server sends a restrictive CSP.
- One malformed workspace cannot fabricate progress for another healthy Epic.
- Stopping or removing AIM UI requires no AIM runtime migration.

## Portfolio boundary

Every workspace has one canonical active Epic, while the UI can observe several
workspaces and planning candidates at once. The planning backlog is not a
scheduler and does not approve an Increment. Shared multi-writer AIM state,
autonomous agent spawning, remote aggregation, account management, production
telemetry, and cross-repository analytics remain outside this version.
Background control is a transport to the one main AIM thread, never a second
runtime writer.

### Measure the interrupted user journey

The source-repository [journey measurement guide](aim-ui-journey-measurement.md)
measures real-agent startup, product-file creation, interruptions, explicit
continuations and transcript-reviewed questions or repairs. It keeps missing
observations unknown and separates verified action results from agent activity.
A verified Start after reconnecting does not establish that Codex is still
working; the action status now says when current agent activity is unconfirmed.

### Optional Legacy workspace cleanup

When older workspace data is found, AIM UI offers **Review cleanup
in Codex** and **Copy for your AI agent**. The agent previews the removable
files, preserves current User Stories and their evidence, and deletes only
with the user's consent. No archive copy is created. Opening the UI or copying
the request does not delete data. The offer and Legacy workspace selector
vanish once no removable legacy data remains. Evidence still used by the
current product can remain at its original path without retaining a Legacy
workspace on the board.
