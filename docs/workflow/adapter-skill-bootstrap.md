> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM adapter skill bootstrap

## Purpose

Define how Codex, Claude Code, and GitHub Copilot discover and run AIM without
depending on `AGENTS.md`, `CLAUDE.md`, or another generic root instruction file.

The shared architecture is skill-led:

1. a supplier-native AIM skill recognizes an `/aim <intent>` request
2. the main AIM thread reads `.aim/state.json` when it exists
3. it reads `aim.profile.yaml`, then `aim.roles.yaml`
4. it loads only the canonical AIM and repository evidence needed by the active
   state, command, role, and risk
5. it orchestrates PO, TDO, Dev, and Reviewer specialists or reports sequential
   main-thread fallback

`docs/workflow/agile-iteration-method.md` remains AIM core. Skills apply that
contract; they do not redefine it.

## Native skill surfaces

| Adapter | AIM skill | Explicit use | Reload behavior |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/agile-iteration-method/SKILL.md` | `/aim <intent>`; `$agile-iteration-method <intent>` is an equivalent explicit selection | Codex normally detects skill changes; restart if the updated skill is not listed |
| Claude Code | `.claude/skills/aim/SKILL.md` | `/aim <intent>` | use live skill detection when available; restart if the top-level skills directory was newly created |
| GitHub Copilot | `.github/skills/aim/SKILL.md` | request `/aim <intent>` or explicitly use the `/aim` skill | reload skills in supported CLI surfaces or start/reload the active Copilot surface |

Supplier syntax may differ internally. The command intent and state effect may
not differ.

## Complete command family

Every AIM skill must resolve:

- `/aim start`
- `/aim continue`
- `/aim status`
- `/aim validate`
- `/aim help`
- `/aim config`
- `/aim configure-agents`
- `/aim calibrate-repo`
- `/aim remember-repo`
- `/aim forget-repo`
- `/aim upgrade`
- `/aim mode`
- `/aim cost`
- `/aim replan`

Detailed state effects and fallbacks live in
`docs/workflow/adapter-command-contract.md`.

## Role boundary

Canonical role identity, sequence, authority, and gate ownership come from AIM
core. Project-specific expertise comes from `aim.roles.yaml` and native agent
files:

- Codex: `.codex/agents/aim-*.toml`
- Claude: `.claude/agents/aim-*.md`
- Copilot: `.github/agents/aim-*.agent.md`

The skill delegates bounded work at the relevant stage. Only the main AIM thread
may update `.aim/state.json`, advance gates, escalate scope, synthesize the
result, or accept an increment or Epic.

## Discovery and failure behavior

File presence is not enough to claim readiness. Installation, upgrade, and
validation distinguish:

- source truth: the canonical AIM core and command contract exist
- package closure: every direct skill reference resolves after installation
- skill discovery: the skill is installed in a supported native location
- version freshness: the installed package matches the selected AIM source
- command parity: the complete `/aim` family is present
- specialist availability: native role files exist and preserve main-thread
  ownership
- live readiness: the supplier surface can load or explicitly select the skill

When live discovery cannot be automated, the installer emits a manual
fresh-session smoke step. AIM must not report successful bootstrap merely because
ordinary chat happened to resemble the method.

## Readiness receipt

Every reviewed install or upgrade plan includes one receipt per selected
adapter:

- adapter
- skill path and scope
- manifest/package version
- planned classification: create, current, or collision/stale
- reload or fresh-session requirement
- first `/aim` example
- explicit fallback when the supplier supports one

Collisions are not readiness. They remain unresolved until the user keeps or
overwrites them through the normal rollback-protected installer flow.

## Migration

Claude `.claude/commands/*.md` files remain supported compatibility entrypoints
during migration, but `.claude/skills/aim/SKILL.md` becomes the primary AIM
workflow source. Copilot custom agents remain native orchestration and specialist
surfaces beneath the project skill. Codex retains its complete user-level skill
package and project-native role agents.

Migration never rewrites active `.aim` state, repo awareness, role profiles, or
user-edited agent files.
