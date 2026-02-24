# AIM 1.2 repo-aware execution and modes

## Purpose
Define one stable execution contract so teams can run AIM in Codex and Copilot with the same role behavior, gate semantics, and repository-specific overrides.

## User experience
Users can start with short prompts such as `Starta en AIM-loop med denna EPIC: ...` or `/aim start "EPIC: ..."`.
The run always reports canonical roles (`PO`, `TDO`, `Dev`, `Reviewer`) and visible mode (`Strict` or `Auto`) while keeping the same gate semantics.

## How it works
AIM behavior is loaded in explicit layers:
1. AIM base semantics
2. repository `AGENTS.md`
3. repository `.github/agents/aim*.agent.md`

Each Epic starts with explicit mode selection:
- `Strict` (default): hard gates pause at A, B, E.
- `Auto`: enabled with `Auto-approve until Epic complete`; hard gates are reported but pauses between Done Increments are skipped unless escalation conditions are triggered.

Canonical role naming is fixed:
- `PO`, `TDO`, `Dev`, `Reviewer`
- aliases are allowed only as mapped non-canonical labels (`Planner` -> `TDO`, `Builder` -> `Dev`).

## Inputs and outputs
- Inputs:
  - repository policy files (`AGENTS.md`, `.github/agents/aim*.agent.md`)
  - Epic definition and selected execution mode
  - optional prompt-file commands in `.github/prompts/`
- Outputs:
  - consistent gate output with canonical role labels and mode visibility
  - Done Increment trace artifacts with escalation transparency
  - migration guidance for 1.0 -> 1.1 and 1.1 -> 1.2 repositories

## Key decisions
- Keep AIM core loop unchanged while formalizing repo layering and mode semantics.
- Treat repository profile as required to reduce ambiguity in stack/testing/role constraints.
- Keep `Strict` as default to preserve oversight; keep `Auto` optional with final full review.

## Defaults and fallbacks
- Default mode is `Strict`.
- If repository bootstrap helpers are unavailable, policy files are loaded manually and assumptions are reported.
- If layered instructions conflict and cannot be resolved safely, escalate to PO instead of guessing.

## Edge cases
- Large policy files can increase context size; mitigate by strict load order and selective reads.
- Alias-heavy repos can hide role intent; mitigate by mandatory canonical role reporting in outputs.
- `Auto` mode can be overused; mitigate with explicit mode visibility and required final full review before Epic completion.

## Data correctness and trust
Must remain true:
- load order is explicit and stable across Codex and Copilot
- role semantics do not drift behind alias labels
- escalation is triggered for contradictory instructions or trust-impacting uncertainty

## Debugging
The single best check to verify behavior:
- Primary log: inspect gate outputs for both `Role: <canonical role>` and `Mode: <Strict|Auto>`.
- What “good” looks like:
  - same layer order and role behavior in Codex and Copilot docs/prompts
  - hard-gate behavior matches selected mode
- What “bad” looks like:
  - missing mode in gate output
  - non-canonical top-level roles used in method reporting
  - conflicting load-order statements across docs

## Related files
- AGENTS.md
- docs/workflow/agile-iteration-method.md
- docs/workflow/copilot-layer.md
- .github/agents/aim.agent.md
- .github/prompts/start-aim.prompt.md
- .github/prompts/install-aim.prompt.md
- docs/epics/aim-1.2-repo-aware-execution.md

## Change log
- 2026-02-24: Created AIM 1.2 feature contract for repository-aware execution, canonical roles, and execution modes.
