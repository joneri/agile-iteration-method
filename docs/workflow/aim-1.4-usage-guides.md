> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.4 usage guides

Use this guide when you already understand the basics and want the fastest correct pattern for common AIM work.

## 1. Start from a user-written Epic

Use when:
- the user already has a strong Epic candidate

Recommended start:
- Codex:
  - invoke `[$agile-iteration-method](...)` with the Epic candidate inline
- Copilot:
  - select `aim` and run `/aim start "EPIC: ..."`

Expected AIM behavior:
- `PO` validates the Epic candidate
- if it is already valid, `PO` may accept it with light normalization only
- if increment ideas are included, AIM preserves them as planning notes
- `TDO` still defines the next single Done Increment

What the user should expect next:
- `TDO` will propose one increment, not a full increment list
- the visible CTA should be about approving or adjusting that increment

## 2. Frontend implementation with reviewer verification

Use when:
- the work is UI-heavy or needs browser verification

Recommended flow:
1. start from a user-value Epic, not a widget task
2. let `TDO` define one end-to-end Done Increment
3. implement within the approved increment scope
4. let `Reviewer` specify browser or manual verification steps when needed
5. use the post-review `TDO` checkpoint to explain what changed, what was already verified, and how the user can test now
6. let `PO` decide whether the Epic continues after the increment is accepted

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
4. let `Dev` and `Reviewer` use informational checkpoints, not generic approval asks
5. use the post-review `TDO` checkpoint to invite practical doc review or testing when useful

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

Visible interaction reminder:
- resumed steps should still sound like the current role and step, not like a generic restart message

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

Visible interaction reminder:
- `Reviewer` should describe the configured verification expectations without sounding like a final approval gate

## 6. Upgrade to a new AIM version

Use when:
- the repository still carries earlier AIM wording or older helper packaging

Recommended path:
- `/aim upgrade 1.2-to-1.4`
- or `docs/workflow/migrate-aim-1.2-to-1.4.md`

Expected result:
- shared AIM 1.4 runtime terminology
- official `.aim` workspace handling
- explicit command-surface expectations
- adapter differences documented as adapter differences

Visible interaction reminder:
- upgrade guidance should explain the next action and fallback clearly, not just dump file lists

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
- use `docs/workflow/quick-start-aim-1.4.md`
- use `/aim help`
- inspect `.github/agents/aim.agent.md`

Adapter reminders:
- Codex discoverability usually starts with the AIM skill and repo docs
- Copilot discoverability usually starts with the `aim` agent and the documented slash-command surface

## 9. Know what to do at each checkpoint

Use this shorthand:
- `PO` first:
  - approve Epic or request Epic changes
- `TDO` before development:
  - approve increment or adjust increment
- `Dev`:
  - read the implementation update; no approval is normally needed
- `Reviewer`:
  - read the verification summary; no approval is normally needed
- `TDO` after review:
  - test now, accept increment, or request adjustment
- `PO` after accepted increment:
  - continue Epic, close Epic, or capture new scope separately
