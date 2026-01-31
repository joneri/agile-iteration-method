AIM is a role-based workflow for using AI in real Agile delivery: PO → TDO → Dev → Reviewer with gates, documentation rules, and end-to-end Done Increments.

## License

© Jonas Eriksson. This work is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).

# Agile iteration method (aim)

Agile iteration method (AIM) is a structured way of using an AI coding agent in explicit roles, with clear handoffs and controlled scope, so you converge to working software without chaotic looping.

## Why this exists
AIM is meant to solve these common problems when using AI for development:
- The agent flip-flops between theories (frontend vs backend, data vs UI) without proving anything
- Scope keeps drifting and you lose control over what is actually being built
- Work gets split into tiny steps that do not deliver usable value
- Debugging becomes guesswork instead of evidence and contracts

## What AIM enforces
- Explicit roles: PO → TDO → Dev → Reviewer → TDO → PO
- Done increments: each increment is shippable and can be evaluated end to end
- Gates: A (Epic), B (increment scope), E (acceptance) are the only approvals that matter
- Evidence over guessing: prove contracts with input/output, not opinions

## How to use in 5 minutes
1. Open this repo in VS Code
2. Open your AI agent chat (Codex) for the workspace
3. Copy the “Master prompt” from `AGENTS.md` and paste it once
4. Paste your problem using the short prompt in `AGENTS.md`
5. Only reply with:
   - `approve`
   - `change: ...`

## Files
- `AGENTS.md`  
  Operational rules for running AIM in one continuous run (roles, gates, stop conditions)
- `agile-iteration-method.md`  
  The explanation: the mindset and why the method works
- `CONTRIBUTING.md`  
  Dev rules, commands, PR discipline
- `docs/features-explanations/`  
  Feature docs: non-obvious behaviors, contracts, fallbacks and debugging notes
- `docs/runbooks/`  
  Runbooks: the “truth” for a feature while implementing changes

## License
This work is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).  
See `LICENSE`.

## Attribution
Created by Jonas Eriksson.