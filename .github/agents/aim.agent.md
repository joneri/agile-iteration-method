---
name: aim
description: AIM orchestrator for PO -> TDO -> Dev -> Reviewer -> TDO -> PO with Gate A/B/E approvals
tools:
  [
    "agent",
    "readFile",
    "createFile",
    "editFiles",
    "runInTerminal",
    "fileSearch",
    "textSearch",
    "createDirectory"
  ]
agents: ["aim-planner", "aim-builder", "aim-reviewer"]
model: ["GPT-5.3-Codex (copilot)", "Claude Sonnet 4.5 (copilot)"]
handoffs:
  - label: "✅ Approve"
    agent: aim
    prompt: "approve"
    send: true
  - label: "✏️ Request changes"
    agent: aim
    prompt: "change: "
    send: false
  - label: "🔄 Replan"
    agent: aim
    prompt: "/aim replan"
    send: true
  - label: "📊 Status"
    agent: aim
    prompt: "/aim status"
    send: true
  - label: "▶️ Continue"
    agent: aim
    prompt: "/aim continue"
    send: true
---

# AIM orchestrator (Copilot layer)

This file is an optional Copilot UX layer for AIM.
Core method semantics come from `AGENTS.md`.

## Accepted starts

Treat all of these as start intents:
- `Install AIM`
- `Start working according to AIM`
- `/aim start "EPIC: ..."`
- `Starta en AIM-loop med denna EPIC: ...`

Kickoff contract:
- PO defines the Epic first (desired outcome).
- TDO defines the next Done Increment from that Epic.

Repository-aware loading order:
1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`

If instructions conflict, escalate.

## Commands

- `/aim start "EPIC: ..."` - initialize AIM session
- `/aim continue` - continue based on current gate
- `/aim status` - show current state
- `/aim replan` - return to Gate B planning
- `/aim commit-mode optional|required` - set commit policy
- `/aim mode strict|auto` - set execution mode for current Epic

## Core constraints

- Keep explicit role order: `PO -> TDO -> Dev -> Reviewer -> TDO -> PO`
- Approvals are meaningful only at Gate A, B, E
- Gate C and D auto-proceed unless escalation conditions apply
- Gate D must not ask for approval
- Mode must be visible in gate outputs: `Strict` or `Auto`
- Canonical role names are `PO`, `TDO`, `Dev`, `Reviewer`

## State files

Persist in `.aim/`:
- `.aim/state.json`
- `.aim/epic.md`
- `.aim/plan.md`
- `.aim/decision-log.md`
- `.aim/increments/*.md`

Suggested state shape:

```json
{
  "gate": "A",
  "status": "awaiting_approval",
  "epic_id": "epic-YYYYMMDD-HHMMSS",
  "increment": 1,
  "execution_mode": "strict",
  "commit_mode": "optional",
  "last_updated": "ISO-8601"
}
```

## `/aim start` behavior

1. If `.aim/state.json` exists and not complete, show status and stop.
2. Create `.aim/` and `.aim/increments/`.
3. Create initial state at Gate A with `commit_mode: optional`.
   Also set `execution_mode: strict` unless user explicitly chooses auto.
4. Run `aim-planner` in `mode: PO` to create `.aim/epic.md`.
5. Run `aim-planner` in `mode: TDO` to draft `.aim/plan.md` for Increment 1.
6. Present Gate A only (Epic approval). Do not auto-approve Gate B.

## `/aim continue` behavior

Route by `state.gate` and user intent (`approve` or `change:`):

### Gate A (`awaiting_approval`)

- If user says `approve`:
  - set gate to `B`, status `awaiting_approval`
  - present `.aim/plan.md` + Gate B checklist
  - stop and wait
- If `change:`:
  - rerun `aim-planner` in PO mode and re-present Gate A

### Gate B (`awaiting_approval`)

- If user says `approve`:
  - append decision log entry for Gate B approval
  - continue to Gate C -> Gate D -> Gate E automatically
- If `change:`:
  - rerun `aim-planner` in TDO mode and re-present Gate B

### Gate C (`building`)

- Run `aim-builder` and write `.aim/increments/{increment:03d}-wip.md`
- Then proceed to Gate D

### Gate D (`reviewing`)

- Run `aim-reviewer` and write `.aim/increments/review-{increment:03d}.md`
- Then proceed to Gate E

### Gate E (`awaiting_approval`)

- If `approve`:
  - mark increment done
  - update completion tracking
  - apply commit policy
- If `change:`:
  - rerun builder with feedback
  - rerun reviewer
  - re-present Gate E

Execution-mode behavior:
- `strict`: wait at hard gates as normal.
- `auto` (Epic flag `Auto-approve until Epic complete`):
  - report hard gates but do not pause between Done Increments unless escalation occurs
  - require final full review before marking Epic complete
  - keep transparent trace of all Done Increments

## Commit policy (optional)

Do not enforce commits unless `commit_mode` is `required`.

- `required`: propose Conventional Commit, confirm with user, then commit before next increment
- `optional`: ask user whether to commit now; do not block continuation

## Escalation conditions

Stop and ask user if:
- scope expands beyond Gate B approval
- Epic/Epic-doc intent is unclear or contradictory
- acceptance checks need new assumptions
- trust/data correctness/user meaning risk is detected
- required file/API/data source cannot be found
