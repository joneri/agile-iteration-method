# Epic: AIM 1.2 repo-aware execution and modes
(Read more in docs/features/<feature>.md)

Kickoff contract:
- PO owns this Epic and defines desired outcome.
- TDO derives the next Done Increment from this Epic.

## purpose
Make AIM 1.2 first-class for repository-aware execution in both Codex and Copilot while preserving the core loop and role accountability.

## non-goals
- no GUI layer or Codex-specific UX polish
- no rewrite of AIM core loop logic
- no dynamic memory across repositories
- no cross-repo shared configuration system

## user experience
Describe the expected behaviour end to end.
- normal case:
  - User starts with short commands such as `Starta en AIM-loop med denna EPIC: ...` or `/aim start "EPIC: ..."`.
  - AIM loads repo policy in defined order and runs the same canonical role flow (`PO -> TDO -> Dev -> Reviewer -> TDO -> PO`) in Codex and Copilot.
  - Execution mode is visible in all gate outputs (`Strict` or `Auto`).
- edge case:
  - If repo files are missing or contradictory, AIM escalates instead of guessing.
- failure / stale / uncertain data:
  - If layering is unclear or context size is unsafe, AIM reports assumptions and asks for PO direction.

## trust rules
What the user must be able to trust. Keep it concrete.
- role semantics stay canonical even if tool aliases exist
- override order is explicit and stable
- Auto mode is always visible and traceable
- final full review happens before an Epic is completed in Auto mode

## key kpis
What matters. Keep it short.
- primary kpi:
  - teams can start and run AIM with short commands and consistent behavior
- secondary kpis:
  - fewer bootstrap mistakes
  - fewer role-name misunderstandings
- never-a-kpi:
  - reducing transparency by hiding gates or traces

## data sources and truth
Where the data comes from and which source wins if they disagree.
- source of truth:
  - AIM base semantics + repository `AGENTS.md` + repository `.github/agents/aim*.agent.md`
- fallbacks:
  - if bootstrap script is missing, load files manually and report assumptions
- freshness rules:
  - always use current workspace repo files

## acceptance criteria
Write as observable outcomes.
- [ ] AIM 1.2 defines repository profile as a required concept and defines load/override order.
- [ ] AIM 1.2 defines canonical roles (`PO`, `TDO`, `Dev`, `Reviewer`) and alias mapping rules.
- [ ] AIM 1.2 defines execution modes (`Strict`, `Auto`) with explicit mode visibility and startup selection.
- [ ] Auto mode supports Epic-level auto-approve with transparent Done Increment traces and final full review before Epic completion.
- [ ] Codex and Copilot startup paths are documented to use the same repository-driven behavior.

## debug and verification
Minimum steps to prove it works.
- how to reproduce:
  - run short trigger command in Codex and Copilot and verify same role/gate behavior
- expected logs (only if needed):
  - one clear note of detected repo profile and mode
- manual checks:
  - mode shown in gate output
  - alias names do not replace canonical role reporting
  - Auto mode still shows all Done Increment traces
- automated checks:
  - docs consistency scan for role names, mode terms, and load-order statements

## risks
List real risks and how we reduce them.
- risk:
  - context size explosion
- mitigation:
  - strict load order and selective file loading
- risk:
  - divergence between AIM base and repo overrides
- mitigation:
  - explicit layer order and escalation on contradiction
- risk:
  - teams overusing Auto mode
- mitigation:
  - explicit visibility, trust warning, and final full-review requirement

## files likely involved
Only list if helpful. Keep it short.
- AGENTS.md
- docs/workflow/agile-iteration-method.md
- docs/workflow/copilot-layer.md
- .github/agents/aim.agent.md
- README.md
- CHANGELOG.md

## documentation update rule
Before starting:
- read: docs/features/<feature>.md

After finishing:
- update the same file with:
  - behaviour changes
  - new endpoints / flags / fallbacks
  - edge cases and the best debug step
