# AIM UI v1

AIM UI is a local, browser-based control room for the current AIM run. It turns
the repository's readable `.aim` evidence into a live Kanban without becoming a
second workflow engine.

## Launch the control room

From an AIM source checkout or a target repository written by the adaptive
installer:

```bash
python3 scripts/aim_ui.py
```

The command binds to `127.0.0.1:4177`, opens a browser tab, and refreshes the
read model every two seconds. Use `--no-browser`, `--port`, or `--repo` when a
different local launch shape is needed.

Zero-repo-write adaptive footprints install the UI under the user's AIM home
distribution. Launch that copy and point it at the target repository:

```bash
python3 ~/.aim/installs/agile-iteration-method/scripts/aim_ui.py \
  --repo /path/to/repository
```

The public Agent Skill contains AIM's complete portable workflow but does not
execute or place UI code in target repositories. Use the separately reviewed
adaptive installer when a public-skill user also wants the control room.

## What the board shows

- the active Epic as the visual rail for the board
- related Done Increments in Backlog, Work in progress, In review, Ready for
  release, and Done
- Epic identity on every card
- current canonical owner, gate, mode, cost profile, state, and evidence
- attention when AIM is blocked or waiting for PO acceptance
- PO, TDO, Dev, and Reviewer as the canonical role lane
- bounded helper agents as separate activity when readable evidence is available

The read model uses an `epics` collection and every increment has an `epicId`.
That keeps the UI contract compatible with future multi-Epic work while v1
intentionally exposes at most one active Epic.

## Why cards move in Auto mode

The UI polls AIM's authoritative runtime files. The main AIM thread advances the
state under the normal gate contract; the next poll projects the new state into
the matching column. The browser does not move the card or approve the gate.

| AIM runtime state | UI column |
| --- | --- |
| initialized or awaiting Gate A/B | Backlog |
| implementation, paused, or blocked | Work in progress |
| review or TDO validation | In review |
| awaiting PO acceptance | Ready for release |
| accepted increment or completed Epic | Done |

## Helper-agent visibility

Supplier runtimes do not expose one portable live-agent API. AIM UI therefore
shows helper agents only when the main AIM thread has readable local evidence in
`.aim/agent-activity.json`:

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
      "epicId": "EPIC-20260821-037",
      "incrementId": "DI-084",
      "spawnedAt": "2026-08-21T12:00:00Z",
      "updatedAt": "2026-08-21T12:01:00Z"
    }
  ]
}
```

Supported activity statuses are `working`, `waiting`, `completed`, and `failed`.
The file is optional observation evidence. It cannot own roles, gates, card
position, acceptance, or Epic completion. When it is absent or malformed, the
UI says that helper activity is unavailable instead of inventing telemetry.

## Read-only and failure boundary

- The local server accepts only GET and HEAD.
- Evidence links are restricted to files inside the selected `.aim` workspace.
- Static paths and evidence paths reject traversal outside their roots.
- The server sends a restrictive content-security policy and does not load
  third-party scripts, fonts, or analytics.
- Missing or malformed runtime input becomes an explanatory degraded view.
- Stopping or deleting AIM UI requires no `.aim` migration or rollback.

v1 is a locally installed control room for one repository. Hosted multi-repository
operation, multiple active Epics, writable controls, scheduling, accounts, and
AIM DATA analytics are deliberately outside this version.
