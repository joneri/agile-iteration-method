> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Install AIM 2.0

## One adaptive installation

AIM has one guided installation. A user chooses the target repository and the
suppliers already used there. The installer plans the smallest complete native
package for those suppliers, previews every write or collision, and applies only
after confirmation.

Run:

```bash
curl -fsSL https://joneri.github.io/agile-iteration-method/install.sh | bash
```

The bootstrap downloads the maintained release to a temporary directory. It
does not assume the current shell directory is the target.

The guided flow asks for:

1. target repository, with filesystem completion
2. Codex, Claude, and/or GitHub Copilot adapters
3. collision decisions when existing files differ
4. final apply confirmation

It does not ask the user to choose a Personal, Team, or Enterprise edition.

## Standard result

The standard adapter footprint installs:

- `aim.profile.yaml` as uncalibrated shared repository knowledge
- `aim.roles.yaml` as uncalibrated, editable project-role intent
- `.gitignore` additions for local `.aim/` runtime state
- each selected supplier's native AIM skill and PO/TDO/Dev/Reviewer agents
- only the canonical workflow contracts directly required by those surfaces
- the Codex AIM skill in user scope and Claude/Copilot skills in project scope
  when those adapters are selected

`aim.roles.yaml` is conservatively seeded from observable files such as
`package.json`, `pyproject.toml`, `Package.swift`, `Cargo.toml`, and `go.mod`.
Detection never claims verified mastery. Run `/aim calibrate-repo`, then
`/aim configure-agents`, to verify and improve the project specialists.

## Supplier-native files

| Supplier | Native project files |
| --- | --- |
| Codex | user `~/.agents/skills/agile-iteration-method/` plus `.codex/agents/aim-*.toml` |
| Claude | `.claude/skills/aim/`, `.claude/agents/aim-*.md`, and legacy compatibility commands |
| GitHub Copilot | `.github/skills/aim/` plus `.github/agents/aim-*.agent.md` |

The installer inherits supplier model defaults. Users may edit native files to
pin supported models, tools, skills, MCP servers, permissions, or hooks.

## Preview, automation, and advanced footprint

Preview without writing:

```bash
python3 scripts/aim_install.py --target /path/to/repo --adapter codex --dry-run
```

Select multiple suppliers by repeating `--adapter`. Use `--format json` for a
machine-readable plan and `--non-interactive --apply` for reviewed automation.
Unresolved collisions fail; `--force` is the explicit overwrite mechanism and
still uses rollback backups.

Every preview includes an adapter skill-readiness receipt: installed path and
scope, manifest classification, whether apply is required, reload behavior,
first `/aim` command, and explicit fallback. After apply, follow the adapter's
reload instruction before testing discovery.

Advanced footprints remain available for storage and repository policy:

| Footprint | Effect |
| --- | --- |
| `adapters` | standard project role profile, selected native adapters, required contracts, and runtime ignore |
| `full` | standard result plus complete embedded workflow docs, schemas, and license metadata |
| `profile` | repo-awareness profile and runtime ignore only |
| `local` | home-scope packages only; no target-repository writes |
| `external` | external AIM distribution and home-scope packages; no target-repository writes |

These are installation footprints, not product editions. Protected repository
policy can choose `local` or `external` without changing AIM core behavior.

## Upgrades and migration

If AIM is already installed, run:

```text
/aim upgrade
```

Upgrade uses the same deterministic plan, reports stale files and collisions,
and never rewrites active `.aim/` state. Existing `--mode personal`, `--mode
team`, and `--mode enterprise` flags are accepted temporarily as compatibility
inputs and mapped to their former storage/footprint policies. They are not
shown in the guided flow and do not identify different AIM products.

Legacy `aim-planner` and `aim-builder` helpers map to canonical `aim-tdo` and
`aim-dev` specialists. A reviewed upgrade installs the canonical names; remove
legacy files after confirming no local customization remains.

After skill or agent files change, follow the receipt's supplier reload advice.
Run `/aim configure-agents` when project frameworks,
test tools, architecture, commands, or policy change.

## Safety boundaries

- `CONTRIBUTING.md` is a source-repository-only maintainer file. A target
  installer must never copy, create, modify, require, or read it, and the
  installer manifest must explicitly exclude `CONTRIBUTING.md`.
- The installer never creates, reads, merges, or overwrites generic root
  `AGENTS.md` or `CLAUDE.md` files.
- AIM-owned collisions require explicit keep/overwrite decisions.
- Apply is rollback-protected and safe to rerun.
- `.aim/` is runtime state, not installed product documentation.
- Only the main AIM thread may write `.aim/state.json` or advance gates.
- Native specialists fall back to sequential main-thread execution when the
  supplier, repository policy, task, or cost profile does not allow delegation.

See [Project-agent configuration](project-agent-configuration.md),
[Adapter entry model](adapter-entry-model.md), and
[Adapter skill bootstrap](adapter-skill-bootstrap.md), and
[Repository surface classification](repository-surface-classification.md).
