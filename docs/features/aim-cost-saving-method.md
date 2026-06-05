# AIM Cost-Saving Method

## Purpose

Explain, in plain operator terms, how AIM saves money on GitHub Copilot, Codex, Claude Code, and similar coding-agent platforms without weakening quality gates.

## How it works

AIM cuts cost by reducing waste before it turns into billable tokens or AI credits:

- one approved Done Increment at a time
- explicit `Cost Control`, `Standard`, and `Deep` runtime depth
- progressive context loading instead of full-method rereads
- validator-first and evidence-first checks where possible
- escalation before expensive wandering, not after
- smaller behavioral scope so sessions stay shorter and retries stay narrower
- explicit cost review before work starts, at Gate B, and again at Gate E

For GitHub Copilot specifically, this matters because the June 1, 2026 billing model prices usage through AI Credits rather than old premium-request intuition. Long agent sessions, repeated retries, unnecessary large contexts, expensive model choices, and broad ambiguous tasks can now become directly visible spend.

For a concrete behavior-by-behavior comparison, see `docs/features/aim-cost-comparison.md`.

## Key decisions

- AIM 2.0 markets cost savings directly because users now feel the spend directly.
- The method does not promise "cheapest possible" output. It promises lower waste with preserved trust.
- `Cost Control` is the default low-cost operating mode, not a weaker method.
- `Deep` remains mandatory when billing facts, trust, data correctness, or public behavior are at stake.
- The cost-saving story must stay grounded in official vendor behavior, especially for GitHub Copilot AI Credits.

## Inputs/outputs

Inputs:

- Epic or task intent
- current vendor billing behavior
- selected mode and cost profile
- observed waste signals such as long sessions, repeated retries, vague scope, or oversized context

Outputs:

- lower context usage on low-risk work
- fewer accidental agent loops
- better separation between cheap work and expensive work
- explicit guidance on when to switch from `Cost Control` to `Standard` or `Deep`
- a repeatable checklist for reviewing whether the spend was justified

## Edge cases

- Some work should cost more because higher assurance is the correct choice.
- Billing investigations themselves are usually `Deep` work because stale pricing guidance is a trust risk.
- GitHub Copilot code review may also consume GitHub Actions minutes, so AI Credits are not the only cost surface.
- The exact price per model or plan can change, so AIM should explain the current billing unit and operator behavior, then point users back to official vendor docs for the latest numbers.

## Debugging

If a team says "AI is too expensive now", inspect in this order:

1. Did the work belong in `Cost Control`, `Standard`, or `Deep`?
2. Did the team approve a real Done Increment or let the agent wander?
3. Did the run reload too much context?
4. Did the team use a pricing-sensitive surface such as Copilot chat, CLI, cloud agent, or review instead of a cheaper path?
5. Did the work require a current billing-facts increment before implementation?

## Related files

- `docs/features/aim-cost-control-mode.md`
- `docs/features/aim-cost-comparison.md`
- `docs/features/aim-cost-review-checklist.md`
- `docs/features/aim-vendor-cost-baseline-june-2026.md`
- `docs/workflow/quick-start-aim-2.0.md`
- `README.md`
