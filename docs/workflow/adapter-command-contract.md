> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 2.0 Adapter Command Contract

## Purpose

Define one command-intent contract for Codex, Claude, and GitHub Copilot.

Adapters route through supplier-native AIM skills, but a command must mean the
same thing everywhere. `/aim <intent>` is the shared documented command family;
supplier-specific explicit skill selection is an equivalent route to the same
intent, not a second command language. This contract is secondary to AIM core in
`docs/workflow/agile-iteration-method.md` and does not redefine roles, gates,
ownership, or acceptance.

## Required command family

| Command | Intent | State effect |
| --- | --- | --- |
| `/aim start "EPIC: ..."` | start a new Epic or resume an incomplete checkpoint instead of creating a parallel run | initializes root Gate A only without Portfolio; with `.aim/ui-portfolio.json`, must use a trusted transaction to publish a dedicated registered workspace |
| `/aim start "PORTFOLIO" mode:auto` | preview the ordered AIM UI Backlog and request one bounded Portfolio mandate | after explicit mandate approval, may create `.aim/portfolio-run.json` and sequentially coordinate included canonical Epic workspaces |
| `/aim continue` | resume from the persisted role, gate, increment, mode, and cost profile | advances state only when the current AIM transition allows it |
| `/aim status` | report the AIM product release from `VERSION` separately from the runtime contract in `.aim/state.json` `aimVersion`, then Epic, increment, role, mode, cost profile, gate, adapter, and next action | read-only |
| `/aim validate` | run or explain Structural, Behavioral, Product coherence, and Release readiness checks | read-only |
| `/aim help` | show the thin front door and the next useful command | read-only |
| `/aim config` | show effective mode, cost, profile, ownership, validation, and adapter fallback configuration | read-only |
| `/aim discuss [question]` | discuss product direction, architecture, tradeoffs, or recent delivery with relevant AIM and repository context | read-only; never creates or changes runtime state, Backlog, source, profiles, durable knowledge, Gates, Epics, or Increments |
| `/aim ui [start\|open\|status\|stop] [repo]` | start or control the local read-only AIM UI for the current or explicitly named repository | may manage a user-scope local UI process and instance metadata; never writes repository or AIM runtime state |
| `/aim to-backlog [inline input \| from <source>]` | turn user-supplied Epic descriptions or one explicit accessible source into planned AIM UI Backlog candidates | atomically merges only `.aim/portfolio-backlog.json`; never activates work or creates canonical runtime state |
| `/aim repair-catalog <candidate-id>` | preview one exact completed runtime-linked Backlog relation and request explicit repair approval | after approval, may atomically archive the contained workspace, remove its catalog entry, retire the matching Backlog record, and publish bounded audit evidence |
| `/aim configure-agents` | inspect or update project role expertise and regenerate selected supplier-native specialists through a reviewed plan | may update `aim.roles.yaml` and AIM-owned adapter files; never `.aim/` runtime state |
| `/aim calibrate-repo` | verify and persist reusable repository knowledge using the canonical calibration flow | writes only approved profile or user-hint facts; never active state |
| `/aim remember-repo <category> "<rule>"` | add one structured shared or personal repository rule | writes the owning profile or user-hint file; never `.aim/` |
| `/aim forget-repo <category> "<rule-id>"` | remove one structured repository rule after showing the proposed change | writes the owning profile or user-hint file; never `.aim/` |
| `/aim reflect` | synthesize evidence from the current AIM project into a temporary, provenance-rich knowledge-candidate report | writes only `.aim/analysis/`; never durable knowledge or active state |
| `/aim reflect-all` | preview and synthesize selected AIM projects beneath reviewed local discovery roots | writes one temporary report in the initiating project; never modifies discovered repositories |
| `/aim upgrade` | inspect installed AIM-owned packages, plan a reviewed refresh, and report follow-up calibration or resume actions | must not rewrite active `.aim/` state |
| `/aim mode strict\|auto` | set execution mode for the active Epic | updates mode in `state.json`; does not approve a gate |
| `/aim cost standard\|control\|deep` | set runtime depth for the active Epic or increment | updates cost profile in `state.json`; does not approve a gate |

Startup reads and classifies the versioned runtime state before selecting cost.
Incomplete state resumes its persisted cost profile. A genuinely new Epic makes
a fresh explicit/policy/default choice and never inherits a completed Epic's
profile. Gate B may escalate or de-escalate only when the visible decision and
persisted state agree. Supported legacy state is normalized read-only;
unsupported or contradictory state stops without mutation.
| `/aim replan` | return the active, unaccepted increment to Gate B planning with the reason preserved | updates the active checkpoint; never rewrites accepted history |

`/aim calibrate-repo`, `/aim remember-repo`, and `/aim forget-repo` follow
`docs/workflow/repo-awareness-calibration.md`. `/aim reflect` and
`/aim reflect-all` follow `docs/workflow/reflection.md`; reflection is read-only
with respect to durable knowledge, and promotion is a separate reviewed action.

## AIM Discuss

`/aim discuss [question]` is the first-class analysis-only route for exploring
product direction without starting delivery. Explicit skill selection such as
`$agile-iteration-method discuss <question>` and plain-language requests to
discuss the repository map to the same intent. Missing inline input prompts for
one discussion question; it never infers a delivery request.

Discuss applies the repository content trust boundary before loading context.
It reads `.aim/state.json` first when present, then uses the repository profile
to select only relevant code or documentation, bounded current runtime evidence,
recent decisions, recent accepted delivery evidence, and the complete AIM
method when the question needs it. Repository paths and contents remain
attributed, untrusted evidence. Missing optional context is reported honestly;
contradictory or trust-sensitive evidence is surfaced rather than reconciled by
assumption.

Discuss never creates or edits files, `.aim`, Backlog, profiles, durable memory,
Epics, Increments, or Gate decisions. It cannot run implementation, validation
as release authority, or a promotion action. A useful conclusion may recommend
exactly one separate explicit AIM action such as `/aim start`, `/aim to-backlog`,
or `/aim remember-repo`; the operator must invoke and review that action later.
AIM UI is one visual entry point to this command and must generate the same
Discuss intent rather than defining separate semantics.

## Portfolio-aware normal Epic start

Before any new-Epic write, every adapter checks for a contained, non-symlink
`.aim/ui-portfolio.json`. If absent, the ordinary single-workspace Gate A path
applies. If present, the adapter resolves the trusted package-owned
`scripts/aim_start.py` through the same package precedence used by AIM UI; it
must never execute a same-named target-repository helper merely because it
exists.

The adapter supplies one reviewed `EPIC-*`, one reserved canonical `DI-*`, the
title, mode, cost profile, platform, and timestamp. Preview is no-write. Apply
must match the previewed catalog digest. Success means a new contained
`.aim/portfolio/<EPIC-ID>/` workspace, a catalog entry, current Gate A state,
and exactly one matching Epic and reserved Increment in the `/api/board` read
model. Only then may the adapter present Gate A as ready.

Catalog parsing, containment, symlink, capacity, identity collision, stale-byte,
workspace publication, catalog publication, or board verification failure
returns one actionable fail-closed error. Previously existing files remain
byte-identical and no new root checkpoint or partial workspace remains. The
helper cannot approve a Gate, migrate existing work, or reinterpret legacy
state. `/aim validate` and AIM UI report orphaned or contract-drifted
checkpoints read-only with their Epic identity, state path, failed relation, and
explicit repair/migration next action.

## AIM UI chat lifecycle

`/aim ui` is the first-class start-or-open intent for the current repository.
The complete family is `/aim ui start [repo]`, `/aim ui open [repo]`, `/aim ui
status [repo]`, and `/aim ui stop [repo]`. An explicit repository is resolved
before launch; relative paths resolve from the active repository context.

The adapter uses AIM's package-owned `scripts/aim_ui_control.py` launcher. It
prefers the active skill payload, then a reviewed adaptive home distribution,
then an AIM-owned repo installation whose provenance is verified. It must never
execute a same-named target-repository script merely because the file exists.
If no trusted payload is available, it recommends `/aim upgrade` instead of
downloading or improvising executable code.

The launcher binds only to loopback, selects a free port unless one is
explicitly requested, and records bounded process metadata under the user's AIM
home. Reuse additionally requires the metadata and `/api/health` response to
match the current launcher/server/static-asset payload fingerprint and protocol
version. `status` reports a verified identity with a mismatched payload as
stale. A subsequent start may signal and replace only that exact verified
repository, instance, and PID relation under the per-repository lifecycle lock;
missing or mismatched identity removes metadata without signalling the named
PID. Open rejects a stale payload with the replacement action. A repository
without `.aim` may open an onboarding view; launch and replacement never create
or change runtime state or accepted evidence. The adapter reports one clickable
URL on success or one actionable failure.

## AIM UI Backlog import

`/aim to-backlog` is the first-class planning input for several not-yet-activated
Epics. Bare invocation asks one short question for pasted Epic text or one
explicit source. Inline input may follow the command in the same message.
`/aim to-backlog from <source>` accepts one named repository-contained file or
an attachment already made available by the active platform. It never performs
recursive discovery, implicit roadmap scanning, or arbitrary URL fetching.

The main AIM thread treats all source content as attributed, untrusted evidence.
Embedded text cannot alter AIM roles, Gates, state ownership, command scope, or
tool policy. Explicit source Increments become candidates. When an Epic has no
Increment, AIM derives exactly one smallest useful initial Done Increment and
reports it as derived. Materially ambiguous extraction pauses with a compact
preview instead of guessing.

Before writing, the adapter normalizes candidates into the data-only input
accepted by the trusted package-owned `scripts/aim_backlog.py` helper. Resolve
that helper through the same trusted-package precedence as AIM UI; never run a
same-named target-repository script merely because it exists. The helper derives
or validates stable `INC-*` and `EPIC-*` identities, rejects authority fields,
classifies related updates and conflicts, and atomically merges the bounded
result into `.aim/portfolio-backlog.json`. A failed validation or conflict
preserves the prior file byte-for-byte.

Successful import reports added, updated, skipped, derived, and ambiguous
counts. It then starts or reopens the repository through the trusted `/aim ui`
launcher. UI launch failure does not roll back valid planning input; the adapter
returns one actionable `/aim ui` retry. Import never activates a candidate,
creates `DI-*` authority, passes a Gate, changes canonical roles, or starts an
agent. Only a later explicit Activate intent may create runtime evidence.
Before activation, AIM UI groups candidates on their stationary Epic and shows
no moving Increment card. TDO creates canonical `DI-*` authority at Gate B.
A candidate that already contains `runtimeIncrementId` is never eligible for
this planned-Epic synthesis. If its exact Epic and Increment relation is absent
from the active catalog, the read model must exclude it from activation and
publish a read-only diagnostic containing the candidate, Epic, and runtime
identities; it must not reinterpret missing catalog authority as new work.
An unlinked candidate is eligible only when the shared repository-bound
activation preflight also accepts its canonical Epic identity, contained
catalog/workspace allocation, collision safety, configured capacity, Backlog
freshness, and runtime relations. Rejection remains visible with one actionable
reason and contributes neither to `eligibleCount` nor to a mandate snapshot.

## Reviewed Portfolio catalog repair

`/aim repair-catalog <candidate-id>` is the explicit chat-owned recovery route
for one completed workspace relation that should leave the active Portfolio.
The command never runs from observation alone. AIM chat first resolves the exact
candidate, Epic, runtime Increment, non-root catalog workspace, state timestamp,
and contained Gate E acceptance evidence. It then invokes the trusted
package-owned `scripts/aim_catalog_repair.py` for a no-write preview.

The preview binds catalog, Backlog, state, acceptance, and workspace-tree
SHA-256 values plus a deterministic contained archive and audit destination.
Apply requires those exact values and a separate explicit operator approval.
Success moves the workspace tree unchanged into `.aim/archive/`, removes its
active catalog entry, removes only the reviewed runtime-linked Backlog record,
and writes the complete retired candidate plus evidence hashes to a sibling
audit file. Unrelated planning candidates and catalog workspaces retain their
order and content.

The helper rejects root-workspace archival, incomplete or non-Gate-E state,
wrong identities, multiple runtime-linked records for the Epic, missing or
mismatched acceptance content, traversal, symlinks, stale source bytes, and
destination collisions before mutation. Every handled publication-checkpoint
failure restores the prior catalog bytes, Backlog bytes, and workspace path;
rollback failure is reported as operator attention rather than atomic success.
It also rejects a candidate referenced by the current non-archived Portfolio
run, including a completed run that has not passed its explicit archive
transition. This prevents repair from removing evidence still required by the
run's immutable snapshot.
The helper owns data safety only: it cannot decide that repair is appropriate,
approve its own preview, rewrite accepted evidence, or grant runtime authority.
AIM UI remains GET/HEAD-only and retains its diagnostic for unrepaired or
manually contradictory history.

### Roadmap recovery and execution handoff

AIM UI calls valid `portfolio-backlog.json` planning metadata a **Roadmap** in
newcomer-facing copy. This does not introduce a second state contract: planned
`INC-*` candidates remain stationary planning metadata and cannot masquerade as
active or accepted `DI-*` runtime.

For empty or legacy repositories the read model may publish a read-only recovery
projection. It must identify what AIM found, recommend one safe chat action, and
keep exact contract diagnostics behind technical details. A checkpoint handoff
includes the repository-relative `state.json` path, detected Epic, exact failed
checks, expected checkpoint timestamp, SHA-256 fingerprint, and requested
operation. UI controls only copy this intent; they never migrate, archive,
register, accept, or repair runtime.

For a Roadmap, the read model may preview the ordered eligible candidates and a
deterministic snapshot hash. The only supported multi-Epic execution handoff is
the exact `/aim start "PORTFOLIO" mode:auto` command. It must explain that later
additions are excluded, escalation pauses execution, and one explicit bounded
mandate remains required. Do not advertise Portfolio Strict until a canonical
multi-Epic Strict contract exists; ordinary single-Epic Strict is unaffected.

## Portfolio Auto start and resume

`/aim start "PORTFOLIO" mode:auto` is the first-class whole-Backlog route. AIM
selects the current valid `INC-*` candidates without a `runtimeIncrementId`,
sorts them by priority, creation time, and id, previews that immutable snapshot,
and asks for one explicit Portfolio mandate. This is the same planned-candidate
set AIM UI shows; a retained Backlog item with runtime authority is history, not
new work that a later mandate may replay.
The mandate names its snapshot and safety boundary. It is not blanket approval
for later cards, materially changed outcomes, destructive or external effects,
or work outside repository policy.

After approval, the main AIM chat uses the trusted package-owned
`scripts/aim_portfolio_run.py` helper to atomically checkpoint only
`.aim/portfolio-run.json`. The helper validates data and transitions; it cannot
reason, approve a Gate, activate an agent, or mutate an Epic workspace. The
helper rebuilds the activatable snapshot through the same preflight and repeats
that preflight immediately before writing. A changed catalog, capacity,
Backlog timestamp or bytes, candidate identity, or runtime relation fails closed
without creating the run file. The
main chat activates at most one new candidate, runs its complete canonical
PO/TDO/Dev/Reviewer/TDO/PO loop, and records eligible decisions as
`auto-approved by portfolio mandate` with the mandate id. User approval must
never be fabricated.

Each candidate retains an independently authoritative contained Epic
workspace. Once its review, validation, Gate E, and Epic closure evidence pass,
the chat checkpoints completion and advances to the next snapshot candidate.
The transition helper accepts only canonical runtime statuses. Immediately
before adding a candidate to `completedCandidateIds`, it re-reads and validates
the exact catalogued workspace, snapshot and candidate identities, Backlog
`runtimeIncrementId`, `epic_complete` state and closure checkpoint,
`previousIncrementStatus: accepted`, Gate E, and the contained
`gateEAcceptance` decision. The matching Increment plan must also declare its
exact `Epic:` identity; completion refuses an unbound, mismatched, missing, or
ambiguous plan before changing Portfolio state. Any failed predicate preserves
the active run unchanged and names the failed terminal relation.

AIM UI preserves already accepted legacy history when a plan predates that
explicit field: only the exact state-linked `previousIncrementId` may inherit
its containing workspace Epic, and only validated terminal Gate E evidence can
make it Done. This read-only compatibility rule does not weaken new completion.
Gate E accepts the Increment only. Immediately before the distinct Epic-closure
transition, the chat revalidates the run and workspace, then records
`auto-approved by portfolio mandate <mandateId>` with decision authority
`portfolio_mandate`. It then completes the active candidate, preserving its
workspace, Backlog runtime link, Gate E evidence, and UI catalog entry. Only
after that durable completion may it select the next candidate with the
`activation_pending` checkpoint. The candidate stays Planned until the chat
creates and validates its workspace and state, records its canonical
`runtimeIncrementId` in Backlog, and only then advances the run checkpoint to
the matching runtime status. This sequence may proceed without another user
message. This Portfolio Auto
specialization overrides the ordinary requirement for a new per-Epic operator
interaction, not the requirement for a separate closure decision or evidence.
`/aim continue` revalidates the immutable snapshot hash, run checkpoint, active
workspace, Backlog link, catalog containment, and admission state before
resuming. `activation_pending` resumes deterministically; a later checkpoint
without all required runtime relations is contradictory and fails closed. It
never replays completed work or silently incorporates later Backlog changes.

Portfolio Auto pauses with its checkpoint intact for scope expansion,
ambiguous or untrusted evidence, validation that bounded correction cannot
restore, unsafe or unauthorized effects, repository/capacity/concurrency
conflicts, or Pause/Stop/Change/Replan intent. Malformed, symlinked, stale, or
hash-mismatched run state fails closed. AIM UI projects progress and approval
provenance read-only; it never drives the loop.

One canonical `.aim/portfolio-run.json` may exist at a time. Before a new
Portfolio mandate is created, an operator may explicitly run the trusted helper
`archive --expected-updated-at <observed> --archived-at <now>` for a validated
`completed` or `stopped` run. The helper moves the exact run into a
collision-safe contained `.aim/archive/` path. Running, paused, malformed,
symlinked, stale, or colliding state is not archived. Start never archives
implicitly, and archived evidence never grants authority to a later run.

## Post-Gate-E PO disposition contract

Gate E accepts the Increment only. At `done_increment_accepted`, the main AIM
thread acts as PO and evaluates the Epic goal, acceptance criteria, accepted
evidence, non-goals, and remaining gaps. It must recommend exactly one of
`close`, `continue`, or `split`, state the rationale and remaining-scope
consequence, and must not merely ask the user to choose among undirected
options.

The recommendation is not a state transition or authority. Ordinary Strict and
Auto runs require the user's separate disposition decision. `continue` hands a
bounded remaining outcome to TDO for the next Gate B; `split` keeps new scope
outside the current Epic. `/aim continue` at `done_increment_accepted` repeats
the same PO assessment and recommendation before mutation. In Portfolio Auto,
the same recommendation is recorded before a separately revalidated mandate
may authorize eligible Epic closure and candidate completion.

Before `close`, the adapter must classify the Epic as `Product`, `Pilot`, or
`POC` from the approved Epic contract and create one contained closure truth
audit. Every acceptance criterion must be mapped to concrete evidence and have
status `proven`; counterevidence must have been actively searched; unresolved
findings, contradictions, and remaining Epic gaps must be empty. `Product` and
`Pilot` additionally require an unassisted representative black-box pass.
Synthetic, fixture, mocked, or implementation-assisted evidence can close only
an Epic explicitly framed as `POC`; it cannot be relabelled as Product evidence.

If any predicate fails, the adapter must recommend `continue`, create another
coherent Done Increment after authority is given, and preserve the unfinished
Epic. `split` applies only to genuinely new scope and cannot remove an unmet
acceptance criterion. A user's `accept`, a Gate E decision, or a Portfolio
mandate supplies decision authority but never substitutes for evidence.

All adapters must execute Epic closure through the trusted package-owned
`scripts/aim_runtime_contract.py close` no-write preview and digest-matched
apply. The transition binds the reviewed JSON through
`epicClosureEvidence` plus `epicClosureEvidenceSha256` and
`epicClosureEvidenceSetSha256`. Every referenced evidence object binds a
contained non-empty file by path, kind, and SHA-256; black-box, negative-test,
and separate closure-authority records are required as applicable. Direct
`epic_complete` writes are non-canonical. Before
Portfolio completion, `scripts/aim_portfolio_run.py` revalidates that exact
closure evidence in addition to the Gate E relation.
Closure apply requires previewed state, closure-evidence, and evidence-set
SHA-256 values; staleness in any relation fails without a state transition.
The canonical artifact shape is defined in
`docs/workflow/epic-closure-truth-audit.md`.

After an ordinary user decision `continue`, the adapter creates the next
canonical `DI-*` plan, then resolves the trusted package-owned
`scripts/aim_runtime_contract.py continue` command. Preview binds the exact
contained authority path, source-state SHA-256, new Increment, and canonical
candidate. Apply requires the previewed digest, rechecks freshness, validates
the candidate against the shipped runtime-state schema and coherence rules, and
atomically replaces `state.json`. The only published next checkpoint is
`gate_b_pending` with `currentRole: TDO` and `lastGatePassed: Gate A`; internal
planning labels such as `increment_planning` are never runtime states.

Read-only AIM UI may tolerate only status-only drift for presentation. A
syntactically valid, safely contained workspace with a canonical active `DI-*`
and otherwise canonical required fields remains visible as a neutral
in-progress card labelled “Status updating” with its raw status in compact
diagnostics. The adapter must hide all Gate actions for that projection. Any additional drift remains
fail-closed, and the UI never normalizes or writes the observed state.

## Portfolio-control chat intents

Portfolio control is expressed as explicit chat intent rather than a second
workflow engine. Portable examples are `Activate INC-UI-CONTROL-001`, `Set
portfolio capacity to 2`, `Focus EPIC-BACKLOG-AIM-UI`, and `Show portfolio
status`.

The main AIM thread resolves these intents against optional
`.aim/portfolio-control.json` and the independently authoritative workspaces in
`.aim/ui-portfolio.json`.

- activation counts workspaces whose canonical state is still running before
  creating a new runtime
- an already-running Epic can resume even when capacity is full
- a new Epic is rejected when running count equals or exceeds
  `maxActiveEpics`
- lowering capacity below running count reports over-capacity and blocks new
  activation; it never pauses or rewrites a workspace
- focus selects default chat targeting and UI emphasis only; it does not
  approve gates, stop other Epics, or authorize agents
- missing control state preserves legacy unbounded activation
- malformed configured control state fails closed for new activation

Only the main AIM thread may write control state or the canonical `INC-*` to
`DI-*` activation link. The browser remains read-only. Portfolio control must
never contain roles, gates, acceptance, workspace status, or agent-spawn
instructions.

### Targeted AIM UI action envelopes

AIM UI may prefill, but never auto-send or execute, a bounded action envelope
for `activate`, `approve`, or `change`. It identifies the Epic, candidate or
Increment, expected hard gate/runtime status, timestamps, and contract version.
Change additionally carries the operator's bounded correction request.

Version 1.2 gate envelopes carry `authorityStatePath`, the exact bounded POSIX
path to the authoritative `state.json` relative to the repository root, and
`expectedLastGatePassed`, the raw checkpoint observed in that file. The path
must begin with `.aim/`, end with `state.json`, and remain contained under the
repository's `.aim` directory. `gate` is the decision
being requested, not a copy of `lastGatePassed`. A Gate E action therefore
names Gate E while normally expecting raw Gate D and
`po_approval_pending`. Absolute paths, empty/dot/traversal segments,
backslashes, missing files, and symlink escape fail closed. Version 1.2 does
not accept the older, directory-shaped `workspace` field.

The receiving main AIM thread treats the envelope as user intent, not authority.
For a v1.2 gate action it resolves and containment-checks `authorityStatePath`
from the repository root and reads that exact file before any other runtime
state; it must not begin with `.aim/state.json` when another path is named. It
compares Epic, candidate/Increment, requested decision,
raw checkpoint, status, timestamp, replay, and admission as applicable, then
performs the same freshness check immediately before writing. Consumed
candidates or changed admission reject without mutation.

Version 1.1 remains a bounded compatibility input: its `workspace` selector is
resolved relative to `.aim`, with `.` meaning root `.aim`. Version 1.0 has no
direct runtime locator. Its receiver may proceed only when portfolio discovery yields exactly
one contained workspace whose canonical Epic, candidate/Increment, status, and
timestamp match. Zero or multiple matches reject the action; root state is never
an implicit fallback. Unknown action versions reject without mutation.

Host handoff success never implies gate success. Approve at Gate E accepts the
Increment; it does not close the Epic. Epic closure remains a separate explicit
disposition based on the PO recommendation. For ordinary Strict and Auto runs,
that decision requires the user.
For an active Portfolio Auto run, the already approved, revalidated bounded
mandate is the explicit PO authority for a subsequent separate Epic-closure
decision; no Gate E action envelope may itself claim or perform that closure.

## First-run onboarding contract

Before showing help, status, or a first-run response, adapters must detect
onboarding state first:

- installed but not calibrated
- calibrated but no Epic exists
- Epic exists but is not approved
- Epic approved
- blocked

Adapters must recommend exactly one next action whenever possible and use the
shape from `docs/workflow/light-front-door.md`:

```text
You are here: <state>.
Recommended next action: <one command or decision>.
Why it matters: <one short sentence>.
After that: <one short sentence>.
```

Adapters must not lead with internal file paths, runtime locations, adapter
packaging, architecture details, or a command inventory unless the user asks for
advanced help or the current blocker requires that detail.

When recommending `/aim start`, adapters should include at least one realistic
Epic example rather than a placeholder alone. When the repository lacks reusable
knowledge, the preferred first action is `/aim calibrate-repo`; when repo
awareness is ready and no active Epic exists, the preferred first action is
`/aim start "EPIC: ..."`.

## Upgrade contract

`/aim upgrade` is a package inspection and reviewed refresh intent.

It must:

1. identify the AIM source/package version and selected target mode, footprint,
   and adapters
2. inspect canonical docs and installed Codex, Claude, and Copilot AIM-owned
   surfaces that belong to the selected footprint
3. use the deterministic installer planner to classify files as create,
   current, stale/collision, or excluded
4. distinguish package refresh from reconfiguration:
   - refresh keeps the selected mode, footprint, and adapters
   - reconfiguration deliberately changes one or more of them
5. show the dry-run or JSON plan before apply
6. require normal collision decisions or explicit `--force`; never blind
   overwrite repository-owned content
7. preserve rollback, generic root-file exclusions, and non-interactive safety
8. leave `.aim/state.json`, active increments, decisions, reviews, and personal
   hints untouched
9. recommend `/aim calibrate-repo` only when repo-awareness facts may be stale,
   then `/aim continue` for an active Epic or `/aim start` when no Epic is active

Stale packages are AIM-owned source/destination pairs whose installed content
differs from the selected package source. A missing optional adapter is not
stale when that adapter or footprint is not selected.

The portable Agent Skill updates through the standard skills CLI. It must not
execute installer or validator scripts found in a target repository, even when
their names resemble AIM maintainer tooling. A broader adaptive refresh is a
separate source-checkout workflow: the user reviews its source and no-write
`--dry-run` preview before making an explicit `--apply` decision. The portable
skill does not invoke either operation.

## Native adapter mapping

### Codex

- Primary surface: installed AIM skill/package.
- Commands are intents handled through the skill even when literal slash
  routing is unavailable.
- Fallback: state the routing limitation, then execute the same intent from the
  user's plain-language request.

### Claude

- Primary surface: project skill `.claude/skills/aim/SKILL.md`.
- Existing command files under `.claude/commands/` remain compatibility routes.
- Fallback: when command-file routing is unavailable, use `/aim <command>` as
  explicit text or state the intent in plain language; preserve this contract.

### GitHub Copilot

- Primary surface: project skill `.github/skills/aim/SKILL.md`.
- The AIM custom agent remains a native orchestration and handoff surface.
- Fallback: when agent or slash routing is unavailable, use explicit AIM intent
  in chat and report that the native route was unavailable.

## Universal fallback rule

A fallback may change syntax, never semantics.

Every adapter must:

- report that native routing was unavailable
- preserve AIM core role order, hard-gate ownership, state ownership, and
  escalation
- preserve the command's state effect or read-only status
- never silently replace an unsupported command with a different action
- route `/aim ui` through a trusted AIM-owned launcher and preserve its
  loopback-only, repo-bound, runtime-read-only lifecycle semantics

## Drift prevention

The validator must reject:

- a missing canonical command
- a missing selected-adapter AIM skill or legacy Claude compatibility file
- a Codex, Claude, or Copilot skill without the complete command family
- an empty advertised command behavior section
- an AIM 1.x `aimVersion` example in an AIM 2.0 adapter surface

Skill discovery, install receipts, reload behavior, and compatibility migration
are defined in `docs/workflow/adapter-skill-bootstrap.md`.
- an adapter with no explicit fallback rule
- onboarding wording that lacks state-first guidance, one-next-action behavior,
  progressive disclosure, or realistic start examples
