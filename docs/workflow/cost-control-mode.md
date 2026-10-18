# AIM Cost Control Mode

## Purpose

Make AIM budget-aware so users can reduce agent resource use without weakening role ownership, gate semantics, or escalation rules.

This is canonical AIM cost-profile behavior. It gives users explicit controls
for resource use; it does not promise that any workload will be cheaper.

## How it works

AIM separates approval flow from runtime depth:

- execution mode: `Strict` or `Auto`
- cost profile: `Standard`, `Cost Control`, or `Deep`

`Cost Control` keeps the AIM loop intact with a narrower routine footprint:

- compact role outputs
- no implementation subagents by default; material final review uses a separate available reviewer under `adaptive-execution.md`
- narrow context loading
- state-first resume from the targeted Story ledger or legacy `.aim/state.json`
- validator-first runtime checks
- concise review evidence
- short trace artifacts for low-risk work
- compact confirmed checkpoints without routine status rereads or copied logs
- reuse of unchanged relevant evidence, role bindings and prior answers within scope
- a concrete recommendation when risk needs more depth, within existing authority

`Standard` also uses state-first resume and progressive context loading.
Agents read the targeted `.aim/product-backlog.json` or legacy `.aim/state.json`
before rebuilding runtime context, then load the shortest authoritative context
first and load deeper docs only when the task needs them.

All profiles retain agreed quality goals, early measurement of the working core,
separate material review and verification through the delivered entry point.
Reuse current raw results when they still apply; changed dependencies or an
unresolved risk require affected checks. A narrow footprint cannot justify
dropping a criterion or lowering a target.

For a preserved legacy Epic, select cost depth afresh on new work; never copy it from an
`epic_complete` checkpoint. Resume preserves an incomplete Epic's persisted
choice. Gate B may move depth in either direction only within existing authority
or an applicable owner decision; the visible rationale and persisted state must
agree. Concrete risk informs the recommendation, not automatic profile changes.

Cost Control's default trace budget keeps Gate A, Gate B, Gate E, the active
increment, and required review evidence. Gates C and D remain visible but do
not create separate decision artifacts unless risk, policy, or a failed cheaper
check makes that evidence necessary. Validation starts with syntax, direct
focused tests, and the cheapest canonical validator, expanding only after a
named risk or failure.

## Key decisions

- Cost Control is not a weaker method. It changes runtime depth, not acceptance.
- `Strict` and `Auto` remain approval modes.
- Cost profiles are orthogonal to execution modes.
- Concrete risk informs depth within mandate. Complexity alone changes neither
  cost profile nor product priority, and never authorizes lower quality.
- Avoid repeated work in every profile. A cost benefit needs measurement of the
  actual workload and platform; no fixed token, time or money reduction follows
  from selecting a profile.
- Context hogs, repeated major-doc rereads, and long low-risk markdown artifacts are budget bugs.

## Inputs/outputs

Inputs:

- Epic or task intent
- execution mode
- selected cost profile or documented default, subject to existing authority
- repo-aware policy
- risk signals discovered during inspection

Outputs:

- visible `Cost profile` when resource use matters or when not `Standard`
- compact or expanded checkpoints according to risk
- resumed state without rebuilding context when the targeted ledger is coherent
- a concrete recommendation and owner decision when required depth exceeds authority
- verification evidence scaled to the work

## Edge cases

- When trust, data correctness, public API, deployment, migration, security or
  unclear acceptance risk appears, identify the concrete consequence and needed
  evidence. Work within existing resources when sufficient; if deeper effort
  exceeds the mandate, obtain the applicable owner decision before spending it.
- `Auto` plus `Cost Control` is allowed, but final Epic completion still requires the normal AIM final review rule.
- `Deep` does not allow scope creep. It only permits broader inspection and stronger evidence inside approved scope.
- Repository policy may require `Standard` or `Deep` for some work.
- An established, reversible public release path does not by itself require
  `Deep`; deployment mechanics, migration, public API, trust, or unresolved
  release risk may still require a recommendation for more depth within mandate.

## Cumulative resource boundaries

Count time and cost across preparation, implementation, experiments, rechecks and
all delegated agents; keep summed agent work distinct from elapsed wall time.
Small steps and parallel sessions cannot bypass an agreed run count or resource
limit. No numeric budget grants unlimited work; remain proportionate to the
assignment and never invent an expansion threshold. Reversible edits cannot
recover spent time or cost.

Quality ambition does not enlarge the mandate, and limited resources do not
permit silently reducing agreed quality. When they conflict, report the actual
remaining commitment and recommend a concrete path with consequences. Stop only
the dependent expansion while independent authorized work continues. Use existing
plans and decision evidence, not a new approval gate or per-action cost form.

## Debugging

At Gate B, assess the selected cost profile against concrete risk and existing
authority. These are recommendations, not automatic escalation rules:

- low-risk and reversible: `Cost Control`
- normal product work: `Standard`
- trust-sensitive or high-blast-radius: `Deep`

If a run feels expensive, inspect whether AIM loaded documents or ran verification that were not required by the selected profile.
For `/aim continue`, first check whether the agent resumed from its targeted ledger before rereading the full workflow doc, adapter guides, or broad repository material.

## Related files

- `aim.profile.yaml`
- `docs/workflow/agile-iteration-method.md`
- `docs/workflow/documentation-model.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `.github/agents/aim.agent.md`
