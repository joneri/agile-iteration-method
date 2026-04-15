# AIM Cost Control Mode

## Purpose

Make AIM budget-aware so users can reduce agent resource use without weakening role ownership, gate semantics, or escalation rules.

## How it works

AIM 1.6 separates approval flow from runtime depth:

- execution mode: `Strict` or `Auto`
- cost profile: `Standard`, `Cost Control`, or `Deep`

`Cost Control` keeps the AIM loop intact while spending less:

- compact role outputs
- no subagents by default
- narrow context loading
- validator-first runtime checks
- concise review evidence
- escalation to `Standard` or `Deep` when risk appears

`Standard` also becomes cheaper in AIM 1.6 by using progressive context loading. Agents read the shortest authoritative context first and load deeper docs only when the task needs them.

## Key decisions

- Cost Control is not a weaker method. It changes runtime depth, not acceptance.
- `Strict` and `Auto` remain approval modes.
- Cost profiles are orthogonal to execution modes.
- Risk controls the profile. Low-risk work can stay narrow; trust-sensitive work must expand.
- Standard AIM should be cheaper by default, not only when Cost Control is selected.

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

## Related files

- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/quick-start-aim-1.6.md`
- `docs/workflow/aim-1.6-usage-guides.md`
- `.github/agents/aim.agent.md`
