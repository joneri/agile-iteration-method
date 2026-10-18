# AIM Cost and Resource Controls

## Purpose

Explain how AIM bounds resource use on GitHub Copilot, Codex, Claude Code and
similar coding-agent platforms while preserving the agreed product and quality.

Apply the mandate boundaries in `autonomous-interaction.md` and the profile rules
in `cost-control-mode.md`. The controls are designed to avoid repeated work
within those boundaries. Actual cost depends on the task, platform, model and
verification required; no fixed saving is promised.

## How it works

AIM uses these controls to address common sources of unnecessary resource use:

- one approved coherent Story selection at a time
- explicit `Cost Control`, `Standard`, and `Deep` runtime depth
- progressive context loading instead of full-method rereads
- compact confirmed checkpoints instead of repeated status reads and copied logs
- reuse of unchanged relevant results, role bindings and prior answers within their exact scope
- validator-first and evidence-first checks where possible
- escalation before expensive wandering, not after
- bounded implementation and targeted retries that preserve the committed product outcome
- proportionate resource decisions in existing planning and review, without a new gate or routine questionnaire

Long sessions, retries, large contexts, model choices and broad ambiguous work
can affect resource use. Consult current official platform billing information
before translating those observations into money. The June 2026 vendor baseline
linked below is a dated reference, not current pricing guidance.

For a concrete behavior-by-behavior comparison, see `docs/features/aim-cost-comparison.md`.

## Key decisions

- Describe the control and its intended effect before claiming a benefit.
- Support any measured saving with its workload, versions, resources and limits.
  A smaller document or faster application is not by itself proof of lower agent cost.
- `Standard` is the default cost profile. Select `Cost Control` within applicable authority for bounded low-risk work; it is not a weaker method.
- Concrete risks can justify recommending `Deep`; they do not automatically change the profile, model, scope or resource mandate.
- Keep pricing-sensitive guidance grounded in current official vendor information.

## Inputs/outputs

Inputs:

- Epic or task intent
- current vendor billing behavior
- selected mode and cost profile
- observed waste signals such as long sessions, repeated retries, vague scope, or oversized context

Outputs:

- a focused context selection with reasons for expansion
- bounded work and targeted correction paths
- reuse of still-applicable evidence and compact confirmed checkpoints
- explicit guidance on when to switch from `Cost Control` to `Standard` or `Deep`
- a repeatable checklist for reviewing whether the spend was justified

## Edge cases

- Some work should cost more because higher assurance is the correct choice.
- Pricing-sensitive investigations need current official sources; stale guidance
  can justify recommending deeper inspection within the resource mandate.
- Include all relevant platform resource surfaces when assessing spend.
- The exact price per model or plan can change, so AIM should explain the current billing unit and operator behavior, then point users back to official vendor docs for the latest numbers.

## Debugging

If a team says "AI is too expensive now", inspect in this order:

1. Did the work belong in `Cost Control`, `Standard`, or `Deep`?
2. Did the work stay within the approved Story selection and product quality goals?
3. Did the run reload too much context?
4. Were unchanged checkpoints, relevant prior answers and raw results reused when valid?
5. Does the cost assessment use current official billing facts and the whole run,
   including delegated work?

## Related files

- `docs/workflow/cost-control-mode.md`
- `docs/features/aim-cost-comparison.md`
- `docs/workflow/cost-review-checklist.md`
- `docs/features/aim-vendor-cost-baseline-june-2026.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `README.md`
