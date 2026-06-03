# AIM GitHub Copilot Cost Reduction Playbook

## Purpose

Give AIM users a practical playbook for reducing GitHub Copilot AI Credit waste after the June 1, 2026 move to usage-based billing.

## How it works

Use this playbook when GitHub Copilot is the primary agent surface or when Copilot spend is the main cost concern.

### 1. Stop thinking in premium requests

After June 1, 2026, Copilot usage is billed in GitHub AI Credits, not just premium-request style quotas. Cost now depends on:

- the model used
- input tokens
- output tokens
- cached tokens
- the Copilot surface being used

This means broad prompts, long sessions, and heavy agent surfaces are now directly visible in spend.

### 2. Prefer the cheapest surface that still fits the task

Use cheaper paths first when they are sufficient:

- code completions and next edit suggestions:
  - do not consume AI Credits on paid plans
- lightweight chat:
  - use for narrow questions, small refactors, and local clarification
- expensive agentic surfaces:
  - use only when the task truly needs autonomous execution, long context, or multi-step review

The core AIM move is simple:
- do not use a high-autonomy Copilot surface for a task that is really just a narrow question or a single-file edit

### 3. Treat code review as a double-cost surface

Copilot code review can cost in two ways:

- AI Credits for model usage
- GitHub Actions minutes for the review infrastructure

That makes code review one of the easiest places to waste money if it is triggered too often or too broadly.

Use AIM to reduce review waste:

- avoid automatic review on every low-value PR if the signal is poor
- keep PRs smaller so review context stays smaller
- avoid repeated re-review loops without new meaningful changes
- use self-hosted runners if your organization already prefers that cost model

### 4. Put hard budget controls in place

For organizations and enterprises, GitHub budget controls are one of the strongest real cost levers.

The most important control is the universal user-level budget:

- it caps each user's total AI Credit consumption
- it applies during both pooled usage and metered usage
- a `$0` budget blocks usage immediately

Additional practical guidance:

- do not enable paid overage casually
- if overage is allowed, set explicit hard stops
- review heavy users before simply raising budgets
- use the June-August 2026 promotional period to find real baselines before the pool shrinks later

### 5. Separate pricing research from implementation

If the team is unsure how Copilot billing works for a task, do not let implementation become an expensive research session.

Instead:

- create one small `Deep` increment for billing facts and budget decisions
- then create the implementation increment with a narrower cost profile

This prevents one long agent session from paying both the research and implementation tax at once.

### 6. Use Gate B to block expensive vagueness

At Gate B, ask:

- is this one shippable Done Increment or a broad exploratory request?
- is Copilot cloud agent or another heavy surface truly required?
- do we need code review for this increment, or is the review cost larger than the likely value?
- would a cheaper model or narrower surface still solve the problem?

If those answers are vague, the increment is probably too expensive already.

### 7. Use Gate E to learn from spend

At Gate E, ask:

- did this increment justify the AI Credits it consumed?
- did we choose a more expensive Copilot surface than necessary?
- did code review create useful signal, or just extra AI Credits and Actions minutes?
- what single budget, surface, or workflow change would make the next increment cheaper?

## Key decisions

- GitHub Copilot is the highest-priority cost playbook because the billing model changed on June 1, 2026.
- Budget controls are not optional hygiene; they are part of real cost management.
- Code review should be treated as a premium workflow because it can burn both AI Credits and Actions minutes.
- AIM reduces cost best when it blocks vague work before the expensive surface is chosen.

## Inputs/outputs

Inputs:

- current Copilot plan and billing context
- selected Copilot surface
- current AIM increment scope
- whether code review, cloud agent, or paid overage is enabled

Outputs:

- better choice of Copilot surface
- clearer budget decisions
- fewer wasteful review loops
- smaller and cheaper increments

## Edge cases

- Code completions and next edit suggestions remain unlimited on paid plans and do not consume AI Credits, so they should not be treated like chat or agents.
- When a user is blocked by budget controls, GitHub does not automatically fall back to a cheaper model; AI Credit-consuming features are blocked instead.
- Some enterprises are in a promotional period from June through August 2026 with a larger shared pool than the later standard amount, so current comfort may hide future cost risk.
- If Copilot review is strategically important, the answer may be better runner and workflow configuration, not simply “use less review.”

## Debugging

When Copilot feels too expensive, inspect in this order:

1. Which surface consumed the spend: chat, CLI, cloud agent, review, or another AI Credit feature?
2. Did the team trigger code review too often?
3. Are user-level and enterprise budgets doing anything useful yet?
4. Did the increment stay narrow at Gate B?
5. Did the team accidentally use implementation sessions to discover billing facts?

## Related files

- `docs/features/aim-vendor-cost-baseline-june-2026.md`
- `docs/features/aim-cost-review-checklist.md`
- `docs/workflow/quick-start-aim-1.7.md`
- `docs/workflow/aim-1.6-usage-guides.md`

## Official sources used

- GitHub Docs: [Usage-based billing for individuals](https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals)
- GitHub Docs: [Budgets for usage-based billing](https://docs.github.com/en/copilot/concepts/billing/budgets-for-usage-based-billing)
- GitHub Docs: [Models and pricing for GitHub Copilot](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
- GitHub Docs: [GitHub Copilot billing](https://docs.github.com/en/billing/concepts/product-billing/github-copilot-billing)
- GitHub Docs: [Getting started with budget controls](https://docs.github.com/en/copilot/tutorials/budgets/getting-started-with-budget-controls)
- GitHub Docs: [About GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)
