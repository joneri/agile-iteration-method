# Platforms and Project Agents

AIM is one delivery system with two maintained distribution paths. The public
Agent Skill provides a portable, self-contained installation through the
standard skills CLI. The adaptive installer can also inspect a target repository
and install supplier-native front doors and project-agent formats. Neither path
changes the shared role-and-gate loop or creates a separate AIM edition.

## Choose an Installation Path

Install complete AIM as a public Agent Skill:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method
```

Choose this path for common skill discovery, installation, and updates across
Codex, GitHub Copilot, Claude Code, and other compatible agents. The package is
generated from canonical AIM sources and is full AIM, not AIM Lite.

Use the adaptive installer when the repository also needs a reviewed footprint,
adapter selection, initial `aim.roles.yaml`, and supplier-native project
specialists. Clone and inspect its public source before running a no-write
preview:

```bash
git clone --depth 1 https://github.com/joneri/agile-iteration-method.git aim-source
cd aim-source
python3 scripts/aim_install.py --dry-run
```

Both paths support later `/aim configure-agents` work. See the
[public Agent Skill distribution](../workflow/version-and-installation.md) and
[adaptive installer](../workflow/install-aim-2.0.md) for their complete
contracts.

Every current distribution supports the [AIM UI control room](aim-ui.md)
through `/aim ui`. The public Agent Skill runs its own package-local payload
without placing UI code in the target repository. Adaptive repo-writing
footprints also expose `scripts/aim_ui_control.py`; zero-repo-write footprints
use the home-scope copy. All variants preserve loopback-only, read-only runtime
projection.

## One Product, Project-Specific Specialists

`aim.roles.yaml` describes the project's PO, TDO, Dev, and Reviewer expertise,
validation, and boundaries. It is readable, editable, and supplier-neutral.

| Platform | Front door | Project specialists |
| --- | --- | --- |
| Codex | user `agile-iteration-method` skill | `.codex/agents/aim-*.toml` |
| GitHub Copilot | project `.github/skills/aim/` | `.github/agents/aim-*.agent.md` |
| Claude | project `.claude/skills/aim/` | `.claude/agents/aim-*.md` |

The standard install inherits supplier model defaults. Users and organizations
can refine models, tools, skills, MCP servers, permissions, and hooks in the
native files supported by their supplier. The skill owns workflow routing; the
specialists remain project-specific through `aim.roles.yaml` and supplier-native
configuration.

## Configure or Refresh

Run `/aim configure-agents`. AIM reads `aim.roles.yaml`, `aim.profile.yaml`, and
freshness-triggered project evidence, then shows a reviewed update plan. It does
not silently overwrite hand-written native configuration. Use
`/aim calibrate-repo` first when repository facts are still unverified.

## What Stays Shared

- PO, TDO, Dev, and Reviewer keep their canonical responsibilities.
- One Done Increment is active at a time.
- The main AIM thread alone owns `.aim/state.json` and gate transitions.
- Review happens before acceptance.
- Unavailable native delegation falls back to the sequential AIM loop.

## What May Differ

Platforms may differ in agent format, automatic delegation, concurrency,
available tools, models, permissions, and UI. AIM uses those differences
deliberately. Native support means equivalent method semantics, not identical
supplier mechanics.

## Storage and Sharing Policy

The public Agent Skill uses the standard skills CLI's selected target and scope.
The adaptive installer writes the small project configuration and selected
native adapter files after a reviewed preview, with local-only, external, or
fuller embedded footprints available for protected repositories and automation.
These are storage and sharing choices, not different AIM editions. Older
Personal, Team, and Enterprise flags remain migration compatibility inputs.

See [Project-agent configuration](../workflow/project-agent-configuration.md)
and [Install AIM](../workflow/install-aim-2.0.md).
