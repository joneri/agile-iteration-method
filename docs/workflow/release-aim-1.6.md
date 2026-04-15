> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.6 release and production checklist

## Release summary

AIM 1.6 keeps the accepted core and runtime model and makes AIM budget-aware.

Main outcomes:
- cost profiles are now explicit: `Standard`, `Cost Control`, and `Deep`
- Cost Control reduces runtime spend without weakening roles, gates, or escalation
- Standard AIM now uses progressive context loading and compact gates by default
- Deep gives high-risk work an explicit stronger-review profile
- the public front door is lighter: start, continue, or validate before reading the full method
- adapter guidance remains explicit without redesigning AIM
- the front-door docs now behave like a short onboarding route instead of a loose document set
- Codex, Copilot, and Claude Code still share one explicit adapter story where parity is possible
- `.aim` remains the official repo-local runtime workspace and `state.json` remains the durable checkpoint

## Main feature in 1.6

The headline feature is AIM cost control:
- `Strict` and `Auto` still control approval flow
- `Standard`, `Cost Control`, and `Deep` control runtime depth
- Cost Control is full AIM with a smaller runtime budget, not a weaker method
- Standard AIM gets cheaper through progressive context loading, cheap validation first, compact gates, and risk-scaled review

Best supporting reference:
- [AIM Cost Control Mode](../features/aim-cost-control-mode.md)
- [AIM Light Front Door](../features/aim-light-front-door.md)
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

## Other 1.6-visible improvements

- AIM 1.5 file-boundary discipline remains active
- adapter guidance is easier to inspect without bloating `AGENTS.md`
- Claude Code remains part of the supported adapter story
- the Codex skill is still positioned as a launcher layer rather than hidden authority
- README, install, quick-start, and the doc map now form one explicit path for new users
- the packaged agent and prompt surfaces now describe the same latest version

## Highlighted changes

### 1) Public cost-control guidance is now part of the release story
- `docs/features/aim-cost-control-mode.md`
- `README.md`
- `docs/workflow/quick-start-aim-1.6.md`
- `docs/workflow/release-aim-1.6.md`

### 2) Public modularity guidance remains part of the release story
- `docs/features/aim-modularity-context-efficiency.md`
- `README.md`
- `docs/workflow/quick-start-aim-1.6.md`
- `docs/workflow/release-aim-1.6.md`

### 3) Latest-version onboarding path
- `README.md`
- `docs/workflow/install-aim-1.6.md`
- `docs/workflow/quick-start-aim-1.6.md`
- `docs/workflow/aim-1.6-doc-map.md`
- `docs/workflow/troubleshoot-aim-1.6.md`

The first visible choice should be start, continue, or validate. Full method and adapter details stay available after that first route decision.

### 4) Adapter and packaging consistency
- `AGENTS.md`
- `CLAUDE.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/commands/`
- `.claude/agents/`

## Production readiness checklist

1. Confirm `README.md` presents AIM 1.6 as the current public front door.
2. Confirm install, quick-start, doc map, and troubleshoot docs point to the 1.6 surface.
3. Confirm the first visible front-door choice is start, continue, or validate.
4. Confirm the 1.6 docs explain cost profiles and their relationship to Strict/Auto.
5. Confirm Cost Control preserves roles, gates, acceptance, and escalation rules.
6. Confirm `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, and packaged agent metadata declare AIM 1.6 consistently.
7. Confirm prompt helpers expose `/aim cost standard|control|deep`.
8. Confirm prompt helpers and upgrade guidance expose `/aim upgrade 1.5-to-1.6`.
9. Confirm `CHANGELOG.md` includes the AIM 1.6 release entry.

## Suggested publish text

AIM 1.6 is out.

What is new:
- the main 1.6 feature is Cost Control: full AIM with explicit runtime-depth profiles
- Standard AIM gets cheaper through progressive context loading and compact gates
- Deep gives high-risk work an explicit stronger-review path
- the front door now starts with three choices: start, continue, or validate
- the latest adapter and onboarding improvements are now part of one explicit public release path
- Codex, Copilot, and Claude Code still share one documented AIM model where parity is possible
- the front-door docs now feel lighter while the full method remains available behind the map
