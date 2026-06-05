# AIM Cost Comparison

## Purpose

Show why AIM 2.0 is expected to reduce AI spend compared with undisciplined agentic work, without claiming exact dollar or token savings.

## How it works

The comparison uses observable cost drivers instead of invented prices:

- context rereads
- session length
- retry loops
- review loops
- model or agent-surface choice
- artifact verbosity
- escalation behavior

Those drivers matter because modern coding-agent cost is tied to token volume, model choice, and the surfaces used. In GitHub Copilot after the June 1, 2026 AI Credits shift, broad prompts, long sessions, heavy agent surfaces, and repeated reviews can become visible spend.

## Comparison

| Cost driver | Undisciplined agentic work | Ordinary AIM use | AIM 2.0 cost-aware use |
| --- | --- | --- | --- |
| Scope | Broad prompt or drifting task | One Done Increment, but cost story is less prominent | One behavioral Done Increment with cost reviewed before work |
| Context loading | Often reloads or re-explains everything | Progressive context loading exists | State-first resume from `.aim/state.json` before broad rereads |
| Validation | Often late, manual, or repeated after drift | Validator support exists | Cheap validation and direct evidence before artifact sweeps |
| Review | Can trigger repeated broad reviews | Reviewer role is explicit | Short review by default, deeper review only on risk |
| Artifact size | Long chats and scattered notes | Runtime artifacts are defined | Short low-risk traces; long artifacts require audit value |
| Escalation | Expensive wandering often happens before stopping | Gates control scope | Cost profile escalates only when trust, data, API, security, migration, or unclear acceptance risk appears |
| Context hogs | Large mixed files may be treated as progress | File-boundary discipline exists | Context hogs are explicit budget bugs |
| Copilot surface choice | Heavy agent or review surfaces may be used by habit | Cost profiles help choose depth | Copilot AI Credits, code review cost, and surface choice are first-class Gate B/E checks |

## What this proves

This proves a behavioral cost case, not a measured price benchmark.

AIM 2.0 should be cheaper in normal day-to-day work because it removes or narrows common spend drivers:

- fewer full-method rereads
- fewer large ambiguous sessions
- fewer retry loops without a new hypothesis
- fewer unnecessary deep reviews
- fewer long low-risk markdown artifacts
- earlier separation between pricing research and implementation
- better matching between risk and runtime depth

## What this does not prove

This document does not claim:

- a fixed percentage saving
- a fixed token saving
- a fixed GitHub Copilot AI Credit saving
- that every AIM 2.0 run is cheaper than every uncontrolled agentic run

Some work should cost more because the risk justifies deeper review and broader context.

## Key decisions

- AIM 2.0 can claim lower waste more safely than exact lower cost.
- The strongest comparison is against uncontrolled agent behavior, not against a hypothetical perfect process baseline.
- The improvement is mainly enforcement, front-door clarity, and operator behavior tied to real risk.

## Inputs/outputs

Inputs:

- selected AIM cost profile
- task risk
- active runtime state
- adapter surface, especially Copilot chat, CLI, cloud agent, or code review

Outputs:

- a clearer cost-profile choice
- a smaller approved Done Increment
- cheaper resume behavior when state is coherent
- a documented reason to escalate only when risk justifies it

## Edge cases

- Billing facts can change, so use current official vendor docs for price-sensitive decisions.
- If a team needs formal savings proof, run a measured benchmark with the same task, model, repo, and acceptance criteria.
- If a task is trust-sensitive, `Deep` may be the correct profile even when it costs more.

## Debugging

When AIM 2.0 does not feel cheaper, check:

1. Did it resume from `.aim/state.json`?
2. Did Gate B approve one narrow behavioral increment?
3. Did the run stay in the right cost profile?
4. Did review depth match risk?
5. Did the team use a heavier Copilot surface than needed?
6. Did long artifacts add audit value, or just consume context?

## Related files

- `AGENTS.md`
- `docs/features/aim-cost-control-mode.md`
- `docs/features/aim-cost-saving-method.md`
- `docs/features/aim-cost-review-checklist.md`
- `docs/features/aim-github-copilot-cost-reduction-playbook.md`
- `docs/workflow/quick-start-aim-2.0.md`
