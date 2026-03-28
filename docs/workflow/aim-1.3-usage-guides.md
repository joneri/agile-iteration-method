> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.3.x usage guides

Use this guide when you already understand the basics and want the fastest correct pattern for common AIM work.

## 1. Start from a user-written Epic

Use when:
- the user already has a strong Epic candidate

Recommended start:
- `/aim start "EPIC: ..."`
- or the Codex AIM skill with the Epic candidate inline

Expected AIM behavior:
- `PO` validates the Epic candidate
- if it is already valid, `PO` may accept it with light normalization only
- if increment ideas are included, AIM preserves them as planning notes
- `TDO` still defines the next single Done Increment

## 2. Frontend implementation with reviewer verification

Use when:
- the work is UI-heavy or needs browser verification

Recommended flow:
1. start from a user-value Epic, not a widget task
2. let `TDO` define one end-to-end Done Increment
3. implement within the approved increment scope
4. let `Reviewer` specify browser or manual verification steps when needed
5. keep Gate D soft; final acceptance still belongs at Gate E

Reviewer-tool examples:
- Playwright CLI when the repo prefers terminal-driven browser checks
- Playwright MCP when the adapter exposes that capability and repo policy prefers it

## 3. Documentation written iteratively with AIM

Use when:
- the work is doc-first and behavior contracts matter more than runtime code

Recommended flow:
1. write the Epic in user-facing terms
2. let `TDO` choose one documentation slice that is understandable on its own
3. keep each Done Increment scoped to one coherent contract or operator concern
4. review for contradictions, drift, and overclaiming

Good targets:
- onboarding
- runtime contract docs
- migration guides
- troubleshooting

## 4. Resume from `.aim`

Use when:
- a previous Epic was interrupted

Expected checks:
- inspect `.aim/state.json`
- confirm the current Epic and active Done Increment
- confirm the latest increment, review, and decision artifacts match the checkpoint

Expected AIM behavior:
- resume the incomplete Epic from the checkpoint
- do not silently create a second active Epic
- validate contradictions before continuing

## 5. Configure reviewer tooling

Use when:
- the repository needs explicit verification guidance

Set reviewer expectations through repo-aware policy, not hidden defaults.

Typical configuration concerns:
- browser verification preference:
  - Playwright CLI
  - Playwright MCP
- manual verification required or optional
- deployment checks allowed or disallowed
- migration checks required before acceptance

The effective rule should be inspectable through:
- `AGENTS.md`
- `.github/agents/aim*.agent.md`
- `/aim config`

## 6. Upgrade to a new AIM version

Use when:
- the repository still carries earlier AIM wording or older helper packaging

Recommended path:
- `/aim upgrade 1.2-to-1.3`
- or `docs/workflow/migrate-aim-1.2-to-1.3.md`

Expected result:
- shared AIM 1.3 runtime terminology
- official `.aim` workspace handling
- explicit command-surface expectations
- adapter differences documented as adapter differences

## 7. Use controlled parallel subagents safely

Use when:
- the adapter exposes bounded parallel help
- repo policy allows it
- the work benefits from analysis, verification, or option generation in parallel

Allowed pattern:
- one main AIM thread owns `.aim/state.json`
- one main AIM thread owns gate progression and acceptance
- subagents produce scoped outputs only
- subagent outputs remain secondary to the synthesized main-thread decision

Not allowed by default:
- parallel gate advancement
- parallel acceptance decisions
- parallel deployment or migration
- unrestricted writes to shared AIM runtime state

## 8. Discover commands quickly

If you are unsure where to begin:
- use `docs/workflow/quick-start-aim-1.3.md`
- use `/aim help`
- inspect `.github/agents/aim.agent.md`

Adapter reminders:
- Codex discoverability usually starts with the AIM skill and repo docs
- Copilot discoverability usually starts with slash commands, prompt files, and the `aim` agent
