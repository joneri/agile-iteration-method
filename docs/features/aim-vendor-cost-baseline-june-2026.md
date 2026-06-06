# AIM Vendor Cost Baseline (June 2026)

## Purpose

Give AIM users one current baseline for how Codex, Claude Code, and GitHub Copilot charge for usage so pricing-sensitive work starts from official billing units instead of guesswork.

This is a date-stamped external-vendor reference, not canonical AIM behavior.
Current vendor facts must be reverified before price-sensitive decisions.

## How it works

As of June 2026, the three main coding-agent surfaces differ in how they present cost:

- GitHub Copilot:
  - usage is measured in GitHub AI Credits
  - GitHub documents that each interaction consumes input, output, and cached tokens, converts that token usage into AI credits, and values 1 AI credit at $0.01 USD
  - the June 1, 2026 billing transition replaced premium-request thinking with token-priced AI credit usage
- Claude Code:
  - the official costs guide states that Claude Code charges by API token consumption
  - the product exposes `/usage`, spend limits, and context-management controls so users can see and reduce token use
- Codex:
  - OpenAI documents a token-based rate card where credits are priced per million input, cached input, and output tokens
  - for most customers, this replaced approximate credits-per-message estimates with token-type pricing

## Key decisions

- Treat vendor billing guidance as date-sensitive and source-sensitive.
- Prefer official vendor docs and changelogs over community summaries.
- Treat GitHub Copilot as the highest immediate confusion risk in June 2026 because the pricing unit changed on June 1, 2026 and now spans chat, CLI, cloud agent, and other agentic surfaces.
- Separate vendor-cost baseline docs from AIM mode docs so current external facts can change without rewriting AIM core semantics.

## Inputs/outputs

Inputs:

- active vendor documentation
- current public pricing or billing references
- the AIM task or Epic that depends on cost understanding

Outputs:

- a current statement of each platform's billing unit
- specific clues about what makes usage expensive
- a recommendation to use `Deep` when billing behavior is a core part of the work

## Edge cases

- GitHub Copilot code completions remain outside AI-credit billing on paid plans, but chat, CLI, cloud agent, Spaces, Spark, and third-party coding agents consume AI credits.
- GitHub Copilot code review has a second cost surface: GitHub also documents that code review can consume GitHub Actions minutes in addition to AI credits.
- Claude Code `/usage` shows helpful local estimates, but the docs say authoritative billing still lives in the Claude Console.
- OpenAI Codex credit consumption depends heavily on the mix of input, cached input, and output tokens; output-heavy or fast-mode work can cost more than lightweight local tasks.
- Vendor plan allowances and model prices can change after this June 2026 snapshot, so future AIM work should verify the latest official pages before publishing a pricing claim.

## Debugging

When AI costs feel unexpectedly high, check these first:

- GitHub Copilot:
  - whether the work used chat versus an agentic surface
  - which model was used
  - whether additional AI-credit budget was enabled
  - whether code review also consumed Actions minutes
- Claude Code:
  - `/usage`
  - model choice
  - stale context and long-running sessions
  - agent-team count, MCP overhead, and extended thinking settings
- Codex:
  - model choice
  - output-heavy tasks
  - fast mode
  - cached versus uncached context

## Related files

- `docs/workflow/cost-control-mode.md`
- `docs/workflow/quick-start-aim-2.0.md`

## Official sources used for this June 2026 baseline

- GitHub Docs: [Usage-based billing for individuals](https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals)
- GitHub Docs: [Models and pricing for GitHub Copilot](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
- GitHub Changelog: [Updates to GitHub Copilot billing and plans](https://github.blog/changelog/2026-06-01-updates-to-github-copilot-billing-and-plans)
- Claude Code Docs: [Manage costs effectively](https://code.claude.com/docs/en/costs)
- OpenAI Help Center: [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card)
