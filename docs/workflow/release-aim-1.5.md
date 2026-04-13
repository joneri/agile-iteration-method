> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.5 release and production checklist

## Release summary

AIM 1.5 keeps the accepted core and runtime model and turns the latest documentation improvements into a real version step.

Main outcomes:
- small Done Increments are now positioned publicly as small behavioral scope rather than minimal file count
- focused file boundaries are treated as part of product quality, review quality, and future context efficiency
- adapter guidance remains explicit without redesigning AIM
- the front-door docs now behave like a complete onboarding route instead of a loose document set
- Codex, Copilot, and Claude Code still share one explicit adapter story where parity is possible
- `.aim` remains the official repo-local runtime workspace and `state.json` remains the durable checkpoint

## Main feature in 1.5

The headline feature is AIM's file-boundary discipline:
- more files can be correct when the behavior stays small and each file owns a clearer responsibility
- fewer files are not automatically better if they create context hogs
- planning, implementation, review, and onboarding now all explain this the same way

Best supporting reference:
- [AIM modularity and context efficiency](../features/aim-modularity-context-efficiency.md)

## Other 1.5-visible improvements

- adapter guidance is easier to inspect without bloating `AGENTS.md`
- Claude Code remains part of the supported adapter story
- the Codex skill is still positioned as a launcher layer rather than hidden authority
- README, install, quick-start, and the doc map now form one explicit path for new users
- the packaged agent and prompt surfaces now describe the same latest version

## Highlighted changes

### 1) Public modularity guidance is now part of the release story
- `docs/features/aim-modularity-context-efficiency.md`
- `README.md`
- `docs/workflow/quick-start-aim-1.5.md`
- `docs/workflow/release-aim-1.5.md`

### 2) Latest-version onboarding path
- `README.md`
- `docs/workflow/install-aim-1.5.md`
- `docs/workflow/quick-start-aim-1.5.md`
- `docs/workflow/aim-1.5-doc-map.md`
- `docs/workflow/troubleshoot-aim-1.5.md`

### 3) Adapter and packaging consistency
- `AGENTS.md`
- `CLAUDE.md`
- `.github/agents/`
- `.github/prompts/`
- `.claude/commands/`
- `.claude/agents/`

## Production readiness checklist

1. Confirm `README.md` presents AIM 1.5 as the current public front door.
2. Confirm install, quick-start, doc map, and troubleshoot docs point to the 1.5 surface.
3. Confirm the 1.5 docs explain that small increments are measured by behavior, not minimal file count.
4. Confirm focused file boundaries are described as legitimate when they reduce context load without expanding scope.
5. Confirm `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, and packaged agent metadata declare AIM 1.5 consistently.
6. Confirm prompt helpers and upgrade guidance expose `/aim upgrade 1.4-to-1.5`.
7. Confirm `CHANGELOG.md` includes the AIM 1.5 release entry.

## Suggested publish text

AIM 1.5 is out.

What is new:
- the main 1.5 feature is clearer file-boundary discipline: small scope means small behavior, not artificially few files
- the latest adapter and onboarding improvements are now part of one explicit public release path
- Codex, Copilot, and Claude Code still share one documented AIM model where parity is possible
- the front-door docs now feel like a finished latest-version onboarding route
