AIM is a role-based workflow for using AI in real Agile delivery: PO → TDO → Dev → Reviewer → TDO → PO, with gates, documentation rules, and end-to-end Done Increments.

## License

© Jonas Eriksson. This work is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).

# Agile iteration method (AIM)

Agile iteration method (AIM) is a structured way of using AI coding agents in explicit roles, with clear handoffs and controlled scope, so you converge to working software without chaotic looping.

## AIM 1.2 highlights
- Same AIM core loop, but with much stronger operational control.
- Repository profile is first-class, so each repo can define stack/testing/role constraints safely.
- Layered execution is explicit and predictable:
  AIM base -> `AGENTS.md` -> `.github/agents/aim*.agent.md`.
- `Strict` and `Auto` modes are explicit and always visible in output.
- Codex and Copilot now share the same startup behavior and role semantics.
- Copilot layer includes UI handoff buttons and command-driven shortcuts.
- Commit-after-increment remains optional policy (team choice, not forced method behavior).

## Why AIM 1.2 is a big upgrade
- Faster kickoff:
  users can start from natural language or `/aim start "EPIC: ..."` with the same role flow.
- Less confusion:
  canonical roles are locked to `PO`, `TDO`, `Dev`, `Reviewer` across docs, prompts, and agents.
- Better trust:
  mode visibility and explicit layering reduce hidden behavior and role drift.
- More throughput:
  `Auto` mode enables rapid Epic progress without removing gates or final review.
- Easier adoption:
  migration exists for both legacy paths (`1.0 -> 1.1` and `1.1 -> 1.2`).

## What's new in 1.2 (promoted)
- Copilot custom-agent support with canonical specs in `.github/agents/`.
- Codex/Copilot parity via repository-aware load order:
  AIM base -> `AGENTS.md` -> `.github/agents/aim*.agent.md`.
- Handoff UI buttons for faster flow control in Copilot chat:
  `Approve`, `Request changes`, `Replan`, `Status`, `Continue`.
- Prompt-file commands for setup/start/migration in `.github/prompts/`.
- Epic-first kickoff contract:
  PO defines Epic from desired outcome, TDO defines Done Increment from Epic.
- Canonical role names locked to:
  `PO`, `TDO`, `Dev`, `Reviewer` (aliases are non-canonical).
- Short trigger support includes:
  `Starta en AIM-loop med denna EPIC: ...`.
- Migration paths:
  - AIM 1.0 -> 1.1: `/migrate-aim-1.0-to-1.1` or `docs/workflow/migrate-aim-1.0-to-1.1.md`.
  - AIM 1.1 -> 1.2: `/migrate-aim-1.1-to-1.2` or `docs/workflow/migrate-aim-1.1-to-1.2.md`.

## Why this exists
AIM is meant to solve common problems when using AI for development:
- The agent flip-flops between theories without proving anything.
- Scope drifts and you lose control over what is built.
- Work gets split into tiny steps that do not deliver usable value.
- Debugging becomes guesswork instead of evidence and contracts.

## What AIM enforces
- Explicit roles: PO → TDO → Dev → Reviewer → TDO → PO
- Epic kickoff: PO writes the Epic from desired outcome/user value
- Increment planning: TDO writes the next Done Increment from that Epic
- Done Increments: each increment is shippable and can be evaluated end to end
- Gates: A (Epic), B (increment scope), E (acceptance) are the only approvals that matter
- Evidence over guessing: prove contracts with input/output, not opinions

## Quick start
### Codex mode (manual)
1. Open this repo in VS Code.
2. Open Codex chat for the workspace.
3. Paste the “Master prompt” from `AGENTS.md` once.
4. Start with `EPIC: <desired outcome>`, then paste your problem using the short prompt in `AGENTS.md`.
5. Choose mode: `Strict` (default) or `Auto`.
6. Reply with `approve` or `change: ...` at gates.

### Copilot layer (optional)
1. Open `docs/workflow/copilot-layer.md`.
2. Install the agent templates from `.github/agents/` and prompt templates from `.github/prompts/`.
3. In Copilot Chat, use one of:
   - `Install AIM`
   - `Start working according to AIM`
   - `Starta en AIM-loop med denna EPIC: ...`
   - `/aim start "EPIC: ..."`
4. Include mode in kickoff:
   - `Mode: Strict` or `Mode: Auto`
5. Use handoff buttons in chat for fast control:
   - `Approve`
   - `Request changes`
   - `Replan`
   - `Status`
   - `Continue`

### Migration paths
- Run `/migrate-aim-1.0-to-1.1` (from `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`).
- Or use `docs/workflow/migrate-aim-1.0-to-1.1.md` in any AI chat.
- Run `/migrate-aim-1.1-to-1.2` (from `.github/prompts/migrate-aim-1.1-to-1.2.prompt.md`).
- Or use `docs/workflow/migrate-aim-1.1-to-1.2.md` in any AI chat.

## Files
- `AGENTS.md`  
  Operational AIM rules for Codex runs.
- `docs/workflow/agile-iteration-method.md`  
  Method explanation and principles.
- `docs/workflow/copilot-layer.md`  
  Copilot-specific interface layer and setup.
- `.github/agents/`  
  AIM Copilot custom-agent templates (canonical source).
- `.github/prompts/`  
  AIM prompt-file templates for quick commands (canonical source).
- `docs/features/`  
  Feature docs: non-obvious behavior, contracts, fallbacks, debugging notes.
- `docs/epics/`  
  Epic docs: desired outcome, trust rules, and acceptance context used by PO and TDO.
- `CONTRIBUTING.md`  
  Contribution and consistency rules.
- `CONTRIBUTORS.md`  
  Creator and contributor acknowledgments.
- `docs/workflow/release-aim-1.2.md`  
  Publish-ready release notes draft for AIM 1.2.

## Attribution
Created by Jonas Eriksson.

## Contributors
- [@liamwears](https://github.com/liamwears) - Copilot-layer direction, agent UX ideas, command-driven AIM workflow input.
