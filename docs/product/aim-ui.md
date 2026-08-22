# AIM UI

> **Beta:** AIM UI is ready for real local evaluation, but its multi-Epic and
> card-decision experience is still evolving. The safety boundary is not Beta:
> the browser remains read-only and cannot pass Gates or write runtime state.

AIM UI is a local, browser-based control room for readable AIM runtime evidence.
It turns one or more independently authoritative Epic workspaces into a live
Kanban without becoming a workflow engine.

AIM UI's portfolio view displays several independently authoritative Epics on
one board. Portfolio Backlog v1 also projects bounded planning input written by
the main AIM chat, without turning the browser or the planning file into a
workflow engine.

The control room opens on **Delivery flow**, where the shared Increment Kanban
is the primary operating surface. Portfolio capacity and Epic summaries,
People and agents, and Closed Increments remain available as separate tabs.
Switching tabs is presentation-only and never changes AIM runtime state.

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

## Plan Increments across Epics

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
use `INC-*` so a planning card cannot be confused with a canonical `DI-*`
runtime Increment. When AIM activates a candidate it may retain traceability in
`runtimeIncrementId`; matching runtime evidence then replaces the planning card.

This file is planning input only. It may contain identity, description,
priority, and timestamps. It must not contain gate status, role transitions,
acceptance, scheduling locks, or agent instructions. Only the main AIM thread
writes it. AIM UI continues to accept only GET and HEAD. The read model rejects
a file larger than 1 MB, limits the array to 256 candidates, and enforces
field-level string ceilings so malformed planning input cannot grow without a
bound.

## What the control-room tabs show

- Delivery flow, selected by default, with a shared five-column Kanban containing increments from every selected Epic
- Portfolio, with active Epic, workspace, increment, and attention totals; chat-owned capacity; and one summary panel per Epic
- People and agents, with each Epic's current canonical role and bounded helper-agent activity
- Closed Increments, with complete accepted history grouped by Epic
- proposed Increment candidates from several Epics, sorted by priority in Backlog
- consistent Epic color and identity on summaries, people panels, filters, and cards
- aggregate view plus presentation-only focus controls for one Epic
- each Epic's current role, gate, mode, cost profile, status, and evidence
- bounded helper agents grouped beneath the Epic that recorded them
- safe partial warnings when one declared workspace cannot be read
- the latest three accepted Increments in Done

Filtering never changes runtime state. It only changes which already-read Epics
the browser presents.

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
| accepted increment or completed Epic | Done |

Done is intentionally a short recency window, not the history store. The read
model sorts accepted runtime evidence by an explicit `Accepted at` timestamp
when available, falls back to the decision artifact modification time, and uses
the numeric Increment identity as a deterministic tie-breaker. Only the newest
three cards remain on the delivery board. Closed Increments shows every
accepted card and never deletes its runtime evidence.

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

Eligible cards may initiate Activate for a planned `INC-*`, or Approve and
Change at a hard gate. On Codex desktop the confirmation opens `codex://new` in
the repository with a bounded action envelope prefilled. Codex does not send it
automatically: the operator reviews the composer and presses Send. Other hosts
can copy the same intent.

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

- The local server accepts only GET and HEAD.
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
scheduler and does not approve an Increment. Writable browser controls, shared
multi-writer state, autonomous agent spawning, remote aggregation, accounts,
and AIM DATA analytics remain outside this version.
