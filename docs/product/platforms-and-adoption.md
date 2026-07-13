# Platforms and Project Agents

AIM is one delivery system with one adaptive installation. Select the suppliers
already used by the project; AIM installs each supplier's native front door and
project-agent format without changing the shared role-and-gate loop.

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

The normal installation writes the small project configuration and selected
native adapter files after a reviewed preview. Advanced local-only, external,
or fuller embedded footprints remain available for protected repositories and
automation. Older Personal, Team, and Enterprise flags are accepted only as
migration compatibility inputs, not product editions.

See [Project-agent configuration](../workflow/project-agent-configuration.md)
and [Install AIM](../workflow/install-aim-2.0.md).
