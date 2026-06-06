# AIM Cost Control Mode

## Purpose

Make AIM budget-aware so users can reduce agent resource use without weakening role ownership, gate semantics, or escalation rules.

This is canonical AIM cost-profile behavior.
In AIM 2.0, cost control is part of the explicit public cost-saving promise rather than a quiet internal optimization.

## How it works

AIM separates approval flow from runtime depth:

- execution mode: `Strict` or `Auto`
- cost profile: `Standard`, `Cost Control`, or `Deep`

`Cost Control` keeps the AIM loop intact while spending less:

- compact role outputs
- no subagents by default
- narrow context loading
- state-first resume from `.aim/state.json`
- validator-first runtime checks
- concise review evidence
- short trace artifacts for low-risk work
- escalation to `Standard` or `Deep` when risk appears

`Standard` also becomes cheaper in AIM 2.0 by using state-first resume and progressive context loading.
Agents read `.aim/state.json` before rebuilding runtime context, then load the shortest authoritative context first and load deeper docs only when the task needs them.

## Key decisions

- Cost Control is not a weaker method. It changes runtime depth, not acceptance.
- `Strict` and `Auto` remain approval modes.
- Cost profiles are orthogonal to execution modes.
- Risk controls the profile. Low-risk work can stay narrow; trust-sensitive work must expand.
- Standard AIM should be cheaper by default, not only when Cost Control is selected.
- Context hogs, repeated major-doc rereads, and long low-risk markdown artifacts are budget bugs.

## Inputs/outputs

Inputs:

- Epic or task intent
- execution mode
- selected or inferred cost profile
- repo-aware policy
- risk signals discovered during inspection

Outputs:

- visible `Cost profile` when resource use matters or when not `Standard`
- compact or expanded checkpoints according to risk
- resumed state without rebuilding context when `.aim/state.json` is coherent
- explicit escalation when deeper runtime depth is required
- verification evidence scaled to the work

## Edge cases

- A user may request `Cost Control`, but AIM must escalate if trust, data correctness, public API, deployment, migration, security, or unclear acceptance risk appears.
- `Auto` plus `Cost Control` is allowed, but final Epic completion still requires the normal AIM final review rule.
- `Deep` does not allow scope creep. It only permits broader inspection and stronger evidence inside approved scope.
- Repository policy may require `Standard` or `Deep` for some work.

## Debugging

At Gate B, check whether the selected cost profile matches the risk:

- low-risk and reversible: `Cost Control`
- normal product work: `Standard`
- trust-sensitive or high-blast-radius: `Deep`

If a run feels expensive, inspect whether AIM loaded documents or ran verification that were not required by the selected profile.
For `/aim continue`, first check whether the agent resumed from `.aim/state.json` before rereading the full workflow doc, adapter guides, or broad repository material.

## Related files

- `aim.profile.yaml`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/documentation-model.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `.github/agents/aim.agent.md`
