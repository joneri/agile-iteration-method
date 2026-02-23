> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM Copilot layer (optional)

## Purpose

The Copilot layer is an interface adapter for AIM.
It makes AIM faster to start and easier to operate in VS Code with:
- custom agents
- handoff buttons
- slash commands via prompt files

It does **not** change AIM semantics.
Core AIM rules still come from:
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`

## What this layer must preserve

- Explicit role order: `PO → TDO → Dev → Reviewer → TDO → PO`
- Gate semantics: approvals matter at `A`, `B`, `E`
- Gate D is soft and must not request approval
- Escalation rules for scope, intent, trust, and missing inputs
- Scope expansion only with explicit stop-and-ask

## Files used by the Copilot layer

- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/start-aim.prompt.md`

Canonical rule:
- `.github/agents/` and `.github/prompts/` are source of truth.

## UI handoff buttons

The `aim` agent defines handoff buttons to reduce typing and speed up gate flow:
- `Approve`
- `Request changes`
- `Replan`
- `Status`
- `Continue`

These are configured in:
- `.github/agents/aim.agent.md`

## Quick start

### Option A: natural-language start
In Copilot Chat, ask:
- `Install AIM`
- `Start working according to AIM`

Then provide:
- `EPIC: ...` (desired outcome in one line)

### Option B: command start
1. Select `aim` in the Copilot agent dropdown.
2. Run:
   - `/aim start "EPIC: ..."`

### Option D: migration start (AIM 1.0 -> 1.1)
- Run `/migrate-aim-1.0-to-1.1`.
- Or use `docs/workflow/migrate-aim-1.0-to-1.1.md` in chat.

### Option C: Epic-doc-first start
If you want to start from desired outcome and trust rules first, ask:
- `Install AIM and start from Epic-doc-first mode`

Then provide:
- the Epic doc path (`docs/epics/<feature>.md`)
- trust rules
- acceptance criteria

## Recommended default operating mode

- Start with PO Epic creation (`EPIC: ...`).
- Let TDO define the first Done Increment from that Epic before coding.
- Keep Gate B as manual approval (unless PO explicitly enables Gate B auto-approve).
- Keep commit-after-Gate-E optional.
- Use `/aim status` and `/aim replan` for control.

## Optional commit policy

Commit policy is team-level, not AIM-core.

Suggested state field in `.aim/state.json`:
- `commit_mode: optional | required`

Behavior:
- `required`: enforce commit before moving to next increment
- `optional`: ask whether to commit, do not block progression

## Debugging and verification

If behavior is wrong, check in this order:
1. `.aim/state.json` gate + status
2. `.aim/epic.md` acceptance criteria
3. `.aim/plan.md` increment scope
4. `.aim/increments/*.md` implementation and review outputs

Most common failure:
- Gate A approval not transitioning to Gate B plan presentation.

Expected fix:
- route `approve` by current gate (`A -> B`, `B -> C`, `E -> completion`).

## Related files

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`
