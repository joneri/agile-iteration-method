AIM is a role-based workflow for using AI in real Agile delivery: PO → TDO → Dev → Reviewer → TDO → PO, with gates, documentation rules, and end-to-end Done Increments.

## License

© Jonas Eriksson. This work is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).

# Agile iteration method (AIM)

Agile iteration method (AIM) is a structured way of using AI coding agents in explicit roles, with clear handoffs and controlled scope, so you converge to working software without chaotic looping.

## AIM 1.3 at a glance
- Same AIM core loop, now with an explicit runtime model.
- `.aim` is the official repo-local AIM workspace.
- `state.json` is the durable checkpoint for startup, resume, and gate tracking.
- Codex and Copilot share one conceptual runtime contract where parity is possible.
- Adapter differences and fallback behavior are documented explicitly.
- Controlled parallelism is bounded by centralized ownership of shared state and gates.
- Migration from AIM 1.2 to AIM 1.3 is documented.

## Why AIM 1.3 matters
- Less mystery:
  AIM is no longer just a prompt plus conventions. The repo documents core, runtime, repo-aware policy, and adapters separately.
- Better continuity:
  `.aim` and `state.json` make active Epic state visible and resumable across sessions.
- Safer parity:
  Codex and Copilot share one runtime model, while differences are treated as adapter differences instead of hidden method drift.
- Easier troubleshooting:
  validator, fallback, migration, and parity behavior are now inspectable in docs and repo state.
- Better future base:
  AIM 1.3 is a clearer foundation for validator tooling, example repos, CI checks, and packaging later.

## Reference implementation

This repository is the reference documentation implementation for AIM 1.3.

Use it to understand:
- the AIM core loop
- the AIM runtime and `.aim` workspace
- startup and resume behavior
- validator and migration behavior
- Codex and Copilot adapter differences
- how to inspect and troubleshoot runtime state

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
- Interaction clarity: each visible step should make the speaker, decision, and next step obvious
- Evidence over guessing: prove contracts with input/output, not opinions
- Runtime transparency: `.aim` is inspectable and `state.json` is authoritative for resume
- Safe fallback: unsupported capability must degrade safely instead of changing the method silently

## Quick start
### Codex mode (manual)
1. Open this repo in VS Code.
2. Open Codex chat for the workspace.
3. Paste the “Master prompt” from `AGENTS.md` once.
4. Start with `EPIC: <desired outcome>`, then paste your problem using the short prompt in `AGENTS.md`.
5. Choose mode: `Strict` (default) or `Auto`.
6. Reply with `approve` or `change: ...` at gates.

Preferred quick-start reference:
- `docs/workflow/quick-start-aim-1.3.md`

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
- Use `docs/workflow/migrate-aim-1.2-to-1.3.md` to adopt the AIM 1.3 runtime contract.

### Inspect and troubleshoot
- Inspect current runtime state in `.aim/state.json`.
- Inspect active Epic intent in `.aim/epic.md`.
- Use `docs/features/aim-1.3-command-surface-and-onboarding.md` for the AIM 1.3.x command surface and Epic candidate model.
- Use `docs/features/aim-1.3-role-specific-interaction-model.md` for the role-specific interaction contract.
- Use `docs/workflow/aim-1.3-usage-guides.md` for practical frontend, documentation, reviewer-tool, resume, upgrade, and parallel-assistance workflows.
- Use `docs/workflow/aim-1.3-interaction-examples.md` for concrete PO/TDO/Dev/Reviewer checkpoint examples.
- Use `docs/workflow/example-aim-1.3-reference-run.md` for one concrete AIM 1.3 reference flow across Codex and Copilot.
- Use `docs/workflow/troubleshoot-aim-1.3.md` for startup, resume, validator, parity, and fallback issues.
- Use `docs/workflow/release-aim-1.3.md` for publish-ready AIM 1.3 release guidance.

## Command and entrypoint discovery

Use this mental model:
- Codex:
  - invoke the AIM skill and provide `EPIC: ...`
  - natural language start is also valid when it clearly expresses AIM intent
- Copilot:
  - use `/aim start "EPIC: ..."` when slash commands are available
  - use `Install AIM` or `Start working according to AIM` when using the optional Copilot layer

The shortest operator path is documented in:
- `docs/workflow/quick-start-aim-1.3.md`

The practical scenario guides are documented in:
- `docs/workflow/aim-1.3-usage-guides.md`

Concrete step examples are documented in:
- `docs/workflow/aim-1.3-interaction-examples.md`

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
- `docs/workflow/release-aim-1.3.md`  
  Publish-ready release notes draft for AIM 1.3.
- `docs/workflow/example-aim-1.3-reference-run.md`  
  Concrete AIM 1.3 reference example for start, resume, inspect, and adapter-aware operation.
- `docs/workflow/troubleshoot-aim-1.3.md`  
  Operator-facing troubleshooting guide for AIM 1.3 runtime behavior.

## Attribution
Created by Jonas Eriksson.

## Contributors
- [@liamwears](https://github.com/liamwears) - Copilot-layer direction, agent UX ideas, command-driven AIM workflow input.
