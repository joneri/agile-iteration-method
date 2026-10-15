# AIM Cost Review Checklist

## Purpose

Give AIM users a concrete checklist for reducing AI spend before work starts, during Gate B planning, and before Gate E acceptance.

This is canonical AIM cost-review behavior at startup, Gate B, implementation, and Gate E.

## How it works

Use relevant questions when cost is a material concern; do not run a mandatory
interview or complete a form for every increment. Reuse known platform facts and
prior authority. Concrete uncertainty may justify a recommendation, never automatic
profile, model, priority or scope changes. Follow `autonomous-interaction.md`.

### Before starting the Epic

- Resolve the vendor surface from available context; ask only if necessary:
  - GitHub Copilot chat, CLI, cloud agent, review, or another AI-credit surface
  - Claude Code
  - Codex
- Determine whether current vendor billing facts actually affect the decision.
- Preserve the selected profile; `Standard` is the default. Recommend `Cost Control` when useful within authority.
- Recommend proportionate investigation if stale billing assumptions could mislead the work; do not automatically switch to `Deep`.

### At Gate B

- Check whether the Done Increment is genuinely one shippable slice or a vague broad exploration.
- Check whether the increment can be solved with narrow context instead of a full doc-family reread.
- Check whether the task requires an expensive agentic surface or whether a cheaper path would do.
- Check whether the model choice and runtime depth match the actual risk.
- Check whether current billing facts must be verified before implementation begins.

### During implementation

- Avoid broad retries without a new hypothesis.
- Avoid dragging large stale context forward if it is no longer needed.
- Resolve a consequential uncertainty with a bounded check inside the commitment when possible; do not substitute a new investigation for the agreed product.
- Propose a separately scoped pricing investigation only when necessary and authorized.

### At Gate E

- Ask whether the increment produced enough user value to justify the spend.
- Ask whether `Deep` was actually necessary or whether future similar work can stay in `Standard` or `Cost Control`.
- Ask whether the work used an unnecessarily expensive surface, model, or session length.
- Capture one concrete cost-saving lesson for the next increment when spend was higher than expected.

## Key decisions

- Cost review is not a separate AIM mode. It is a decision discipline layered onto existing gates.
- The checklist is especially important for GitHub Copilot after the June 1, 2026 AI Credits billing change.
- Pricing-fact work should often be a separate increment from implementation work.
- Lower cost is not success if trust, correctness, or user-facing meaning were compromised.

## Inputs/outputs

Inputs:

- selected platform and surface
- current task risk
- selected AIM cost profile
- signs of waste such as vague scope, retries, large context, or unnecessary agentic tooling

Outputs:

- a better choice of `Cost Control`, `Standard`, or `Deep`
- a resource-appropriate increment that retains its agreed value and quality
- clearer justification for when expensive work is actually worth it

## Edge cases

- For billing research, choose evidence depth within the agreed resource mandate.
- If GitHub Copilot review is part of the workflow, remember that Actions minutes may also matter.
- If the work is trust-sensitive, saving money is secondary to getting the decision right.
- If a team repeatedly needs `Deep` for the same class of work, the next improvement may need automation or tooling rather than more checklist language.

## Debugging

When a team says AIM still feels expensive, ask:

1. Did we pick the wrong cost profile?
2. Did we let scope stay vague at Gate B?
3. Did we use an expensive agent surface when a cheaper path would have worked?
4. Did we mix pricing research and implementation into one long session?
5. Did we capture any lesson at Gate E for the next increment?

## Related files

- `docs/workflow/cost-saving-method.md`
- `docs/features/aim-vendor-cost-baseline-june-2026.md`
- `docs/workflow/quick-start-aim-2.0.md`
