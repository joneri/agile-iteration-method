# AIM Cost Review Checklist

## Purpose

Give AIM users a concrete checklist for reducing AI spend before work starts, during Gate B planning, and before Gate E acceptance.

## How it works

Use this checklist whenever AI cost is a meaningful concern.

### Before starting the Epic

- Ask which vendor surface is being used:
  - GitHub Copilot chat, CLI, cloud agent, review, or another AI-credit surface
  - Claude Code
  - Codex
- Ask whether current vendor billing facts matter to the task.
- Default to `Cost Control` only if the work is low-risk and the pricing model itself is not under investigation.
- Start in `Deep` if stale billing assumptions could mislead the work.

### At Gate B

- Check whether the Done Increment is genuinely one shippable slice or a vague broad exploration.
- Check whether the increment can be solved with narrow context instead of a full doc-family reread.
- Check whether the task requires an expensive agentic surface or whether a cheaper path would do.
- Check whether the model choice and runtime depth match the actual risk.
- Check whether current billing facts must be verified before implementation begins.

### During implementation

- Avoid broad retries without a new hypothesis.
- Avoid dragging large stale context forward if it is no longer needed.
- Prefer one focused clarification increment over a long drifting session.
- Treat pricing investigation as its own increment when it is the real blocker.

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
- a narrower and cheaper Done Increment
- clearer justification for when expensive work is actually worth it

## Edge cases

- If billing facts themselves are the work, the run usually starts in `Deep`.
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

- `docs/features/aim-cost-saving-method.md`
- `docs/features/aim-vendor-cost-baseline-june-2026.md`
- `docs/workflow/quick-start-aim-1.7.md`
- `docs/workflow/aim-1.6-usage-guides.md`
