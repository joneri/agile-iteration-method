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

Parity rule:
- Copilot and Codex must execute the same repository-driven AIM behavior.
- Where parity is impossible, Copilot must document the difference explicitly and fall back safely instead of silently changing the method.

## What this layer must preserve

- Explicit role order: `PO → TDO → Dev → Reviewer → TDO → PO`
- Gate semantics: approvals matter at `A`, `B`, `E`
- Gate D is soft and must not request approval
- Escalation rules for scope, intent, trust, and missing inputs
- Scope expansion only with explicit stop-and-ask
- Execution mode visibility (`Strict` or `Auto`) at all gates
- Canonical role reporting (`PO`, `TDO`, `Dev`, `Reviewer`)

## Repository-aware loading

Load behavior is layered in this order:
1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`

If layers conflict, escalate to PO.

## Normalized runtime context

Copilot must not interpret repository files ad hoc after startup.
It should load them into the same normalized repo-aware runtime context used by Codex.

Minimum context areas:
- `verification`
- `deployment`
- `migration`
- `reviewer`
- `environment`
- `approval`
- `parallel`

Copilot-specific rule:
- command routing and handoff UI may differ, but those differences must consume the same normalized context rather than inventing a second policy model

Failure handling:
- if repository layers contradict each other on a trust-affecting rule, stop and escalate
- if Copilot cannot support a requested capability, preserve the policy in context and fall back safely instead of dropping the rule silently

## Shared bootstrap and resume contract

Copilot must preserve the same conceptual startup flow as Codex:
1. detect repo root
2. load repo-aware AIM context
3. detect or create `.aim`
4. load active Epic from `.aim/state.json` or initialize a new Epic
5. resolve execution mode
6. resolve platform capability and repo-policy limits
7. enter the AIM role sequence

Resume rule:
- if `.aim/state.json` exists and points to an incomplete Epic, Copilot must resume from that checkpoint instead of silently starting a new Epic

Fallback rule:
- if repo-aware context is missing or contradictory, stop and escalate
- if `.aim` is missing, create it before continuing
- if runtime state is recoverably incomplete, recreate the missing artifacts and report the assumption
- if runtime state is contradictory or unsafe, stop and ask before continuing
- if a capability does not exist in Copilot, keep the same runtime contract and fall back to sequential behavior

## Files used by the Copilot layer

- `.github/agents/aim.agent.md`
- `.github/agents/aim-planner.agent.md`
- `.github/agents/aim-builder.agent.md`
- `.github/agents/aim-reviewer.agent.md`
- `.github/prompts/install-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.2-to-1.4.prompt.md`

Canonical rule:
- `.github/agents/aim*.agent.md` are part of the shared AIM instruction layer and also act as native Copilot agent files.
- `.github/prompts/` are source of truth for Copilot-specific entrypoints and UX wiring.
- The shared AIM runtime contract still comes from `AGENTS.md` and `docs/workflow/agile-iteration-method.md`.

## UI handoff buttons

The `aim` agent defines handoff buttons to reduce typing and speed up gate flow:
- `Send "approve"`
- `Draft "change:"`
- `Replan`
- `Status`
- `Continue`

Important:
- these buttons are transport helpers, not the visible AIM checkpoint contract
- the quoted labels are intentional and make it clear that the buttons send control inputs rather than define the step-specific CTA wording
- the meaning of the decision still comes from the current checkpoint text (`approve Epic`, `accept increment`, `continue Epic`, and so on)

These are configured in:
- `.github/agents/aim.agent.md`

## Quick start

### Preferred production path
1. Select `aim` in the Copilot agent dropdown.
2. Run `/aim start "EPIC: ..."`
3. Make mode explicit:
   - `Mode: Strict`
   - `Mode: Auto`

Behavior:
- if there is no active incomplete Epic, initialize AIM and present Gate A
- if an active incomplete Epic already exists in `.aim/state.json`, show status and resume that Epic instead of creating a parallel session

### Secondary starts
Natural-language starts remain valid when the optional layer is installed:
- `Install AIM`
- `Start working according to AIM`
- `Starta en AIM-loop med denna EPIC: ...`

Epic-doc-first start is also supported as an advanced path:
If you want to start from desired outcome and trust rules first, ask:
- `Install AIM and start from Epic-doc-first mode`

Then provide:
- the Epic doc path (`docs/epics/<feature>.md`)
- trust rules
- acceptance criteria

Migration start remains a secondary specialized path:
- Run `/migrate-aim-1.0-to-1.1`.
- Or use `docs/workflow/migrate-aim-1.0-to-1.1.md` in chat.
- Run `/migrate-aim-1.1-to-1.2`.
- Or use `docs/workflow/migrate-aim-1.1-to-1.2.md` in chat.
- AIM 1.2 to AIM 1.4 migration is currently documented in `docs/workflow/migrate-aim-1.2-to-1.4.md`.
- A dedicated Copilot prompt file is packaged as `.github/prompts/upgrade-aim-1.2-to-1.4.prompt.md`.

Help and diagnostics entrypoints:
Use these commands when the user needs orientation instead of immediate execution:
- `/aim help`
- `/aim status`
- `/aim validate`
- `/aim config`
- `/aim upgrade 1.2-to-1.4`

Expected behavior:
- `/aim help` explains the command surface, Epic versus Done Increment, mode choice, and where AIM state lives
- `/aim status` summarizes current Epic, increment, role, mode, gate, adapter, and parallel capability
- `/aim validate` checks `.aim`, `state.json`, runtime coherence, and ownership boundaries
- `/aim config` explains effective configuration from repo policy, runtime state, and adapter limits
- `/aim upgrade 1.2-to-1.4` points to the shared migration workflow and packaged migration prompt

## Adapter support levels

Use these parity labels when comparing Copilot with Codex:
- `shared`
- `shared_with_adapter_differences`
- `codex_only`
- `copilot_only`
- `planned`
- `not_in_release_contract`

Current Copilot-layer interpretation:
- shared:
  - startup and resume through the shared runtime contract
  - `.aim` creation and checkpoint-based resume
  - main-thread ownership of `state.json`, gates, and acceptance
- shared_with_adapter_differences:
  - slash commands and handoff UI
  - validator entry behavior
  - reviewer tooling and verification execution
  - template rendering and prompt packaging
- planned:
  - bounded parallel subagent behavior matching Codex runtime capability

Anything classified as `planned` or `not_in_release_contract` must not be presented as guaranteed production support.

Copilot must not treat `planned` as silently supported.
It must preserve the policy intent and fall back safely.

## Recommended default operating mode

- Start with PO Epic creation (`EPIC: ...`).
- Let TDO define the first Done Increment from that Epic before coding.
- Keep `Strict` mode as default.
- Use `Auto` only with explicit Epic flag: `Auto-approve until Epic complete`.
- Keep commit-after-Gate-E optional.
- Use `/aim status` and `/aim replan` for control.

## Optional commit policy

Commit policy is team-level, not AIM-core.

Suggested state field in `.aim/state.json`:
- `commit_mode: optional | required`

Behavior:
- `required`: enforce commit before moving to next increment
- `optional`: ask whether to commit, do not block progression

## Auto mode guardrails

When Epic is started with:
- `Auto-approve until Epic complete`

then:
- hard gates are still reported
- manual pauses between Done Increments are skipped unless escalation is triggered
- all Done Increments must remain visible in trace artifacts
- a final full review is required before Epic completion

## Debugging and verification

If behavior is wrong, check in this order:
1. `.aim/state.json` gate + status
2. `.aim/epic.md` acceptance criteria
3. the newest live increment, review, and decision artifacts
4. optional helper files such as `.aim/plan.md` only after the official artifacts are checked

Shared startup checks:
- confirm both Codex and Copilot docs describe the same conceptual startup order
- confirm `/aim start` and `/aim continue` map to the same shared resume semantics
- confirm missing `.aim` results in creation, not silent failure
- confirm both adapters describe the same normalized repo-aware context areas
- confirm parity differences are documented as adapter differences, not method differences

Shared diagnostics checks:
- confirm `/aim status` reports role, mode, gate, adapter, and active increment consistently with `.aim/state.json`
- confirm `/aim config` names the source of effective rules instead of implying hidden defaults
- confirm `/aim validate` uses the shared validator result classes: healthy, recoverable, blocked, contradictory
- confirm install and upgrade prompts match the files actually packaged in `.github/prompts/`

State contract checks:
- confirm official runtime artifacts are `.aim/state.json`, `.aim/epic.md`, `.aim/increments/`, `.aim/decisions/`, and `.aim/reviews/`
- confirm helper files such as `.aim/plan.md` are treated as optional Copilot aids, not as authoritative gate state

Most common failure:
- Gate A approval not transitioning to Gate B plan presentation.

Expected fix:
- route `approve` by current gate (`A -> B`, `B -> C`, `E -> completion`).

## Related files

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/features/aim-1.4-bootstrap-and-resume.md`
- `docs/features/aim-1.4-repo-aware-runtime-context.md`
- `docs/features/aim-1.4-platform-adapters-and-parity.md`
- `.github/agents/aim.agent.md`
- `.github/prompts/start-aim.prompt.md`
- `.github/prompts/help-aim.prompt.md`
- `.github/prompts/upgrade-aim-1.2-to-1.4.prompt.md`
- `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`
- `.github/prompts/migrate-aim-1.1-to-1.2.prompt.md`
