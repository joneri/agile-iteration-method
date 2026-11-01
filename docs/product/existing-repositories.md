# Use AIM in an existing repository

AIM can work with the code, architecture and delivery practices your project
already has. Start from a change you need; AIM uses that outcome to prepare
relevant repository knowledge and project-specific roles before planning delivery.

## Start from the project you have

Open the existing repository in your coding agent and
[install the complete AIM skill](getting-started.md#1-install-aim). If AIM is
already installed, reuse it; use `/aim upgrade` when an update is needed.
Keep your normal project instructions and configuration in place.

Describe a useful change and the constraints that matter. For example:

```text
/aim start "Improve checkout recovery in this existing application. Customers must be able to check a delayed payment confirmation without placing a duplicate order. Use the current stack, architecture and test tools. Preserve existing checkout behavior and unrelated local changes. Verify the recovery journey and relevant regressions. I retain scope changes, publication and final acceptance."
```

You do not need to run setup commands before each intent. Within the start, AIM
checks the applicable knowledge and role configuration, refreshes what is missing
or stale, then continues into requirements and planning. Current verified facts
and user-edited agent settings are reused. Starting work does not grant a rewrite,
dependency installation or deployment outside the agreed scope.

For an architectural question before committing to a change, use
`/aim discuss "How does checkout recovery work in this repository?"`.
Discuss reads and explains; it does not calibrate persistently or start delivery.

## How calibration builds repository knowledge

Calibration checks relevant project evidence: build and package metadata,
existing instructions, short maintained documentation, affected code and callers,
test entry points and validation commands. It records what the evidence supports:

- the stack, architecture and local conventions relevant to the work;
- important code areas, their responsibilities and dependencies;
- build, lint, test and user-journey verification commands;
- ownership boundaries, risk zones and project constraints;
- where to find deeper documentation and when to recheck each fact.

A detected framework is an initial clue. A command becomes verified through
appropriate source inspection and checks; a passing profile validator establishes
structure and bindings, not architectural truth or a passing application test.
AIM reports unresolved assumptions and unavailable checks instead of calling
them verified expertise. Calibration is focused on the relevant areas, rather
than an exhaustive audit of the entire codebase.

When repository sharing is selected, compact durable knowledge belongs in
`aim.profile.yaml`, with pointers to maintained project documentation. Other
footprints can use permitted external storage or session context. AIM respects
that choice; intentionally absent repository profiles are not missing setup.
`.aim/` holds delivery state and evidence, not the durable repository profile.

This is how AIM becomes useful in your project: verified, reusable knowledge
that is checked when its sources change. It is not a one-time declaration that
an agent knows every part of the repository.

## How the four roles get the right skills

After calibration, AIM prepares or refreshes the applicable project role
configuration. Where the selected footprint includes it, `aim.roles.yaml` defines
the roles' missions, expertise, skill bindings, validation and write boundaries.

| Canonical role | Project knowledge and skills it needs | Delivery responsibility |
| --- | --- | --- |
| PO — Product Owner | Product purpose, users, domain rules and relevant product skills | Frame Epic outcomes, preserve priority and assess the product outcome. |
| TDO — Technical Delivery Owner | Architecture, dependencies, integration risks and verification methods | Create Stories and criteria, plan coherent delivery and validate the integrated result. |
| Dev | The affected framework, local implementation conventions and available development skills | Implement the approved scope and return working behavior with check results. |
| Reviewer | The original requirements, affected code, regression risks and available review or testing skills | Independently challenge material changes and the evidence behind them. |

Each role starts with its bundled engineering skill:
`aim-po-engineering`, `aim-tdo-engineering`, `aim-dev-engineering` or
`aim-reviewer-engineering`. Relevant project skills are added only when their
actual instructions are available and can be read. A skill name or expertise
label alone does not supply that capability. Missing skills need an explicit
gap and a concrete fallback; AIM does not silently install guessed packages.

For example, a web project may have maintained browser-verification instructions
that Dev and Reviewer should use. A domain guide may matter to PO and TDO.
Select these from the project's actual needs and available instructions.

The canonical roles stay the same across projects. Their project knowledge and
skills change. They are responsibilities, not a requirement to run four agents
at once; material review still requires a separate reviewer.

## Configuration must reach the running agent

When the chosen setup permits repository-native specialists, AIM prepares the
selected platform's thin role definitions:

| Platform | Project-native role files |
| --- | --- |
| Codex | `.codex/agents/aim-*.toml` |
| Claude Code | `.claude/agents/aim-*.md` |
| GitHub Copilot | `.github/agents/aim-*.agent.md` |

These files load the relevant role instructions and current project context.
AIM preserves hand-written overrides and shows collisions before replacement.
Protected or portable setups can use permitted external/session configuration
and bundled instructions without creating these files.

A written agent definition is not proof that the coding platform has loaded it.
AIM should report whether a session reload is needed and which capabilities are
actually available. Your platform starts agents and applies its own model, tool
and permission controls. Preparing a specialist does not launch it or grant it
approval, acceptance or additional resources.

## What to expect before implementation

Ask AIM to give you a compact account of:

- the inspected areas, verified project facts and remaining uncertainties;
- the storage and files it used or changed;
- each role's relevant skills, actual instruction sources and capability gaps;
- the commands and user journeys that will verify this change;
- any reload requirement, then the proposed scope, plan and decision needed next.

With the default Strict mode, approve the proposed plan before implementation.
Auto continues only within authority you have already given. Dev builds the
agreed change, a separate Reviewer checks material work, and TDO validates the
integrated result before PO assesses the outcome. Final acceptance stays with
you unless you explicitly delegate it within a defined mandate.

## Refresh preparation separately when needed

To inspect and refresh setup before selecting a product change, or after a
relevant architecture/tooling change, use these commands in agent chat:

```text
/aim calibrate-repo
```

Then, when the applicable facts are ready:

```text
/aim configure-agents
```

The first refreshes repository knowledge; the second uses it to refresh role
configuration and available skill bindings. They prepare the project; they do
not approve a delivery plan. Normal intent-led starts already perform the
necessary preparation. Refresh affected facts and bindings when their sources
change, rather than rebuilding the whole setup for every Epic.

See the detailed contracts for [calibration](../workflow/repo-awareness-calibration.md),
[project-agent configuration](../workflow/project-agent-configuration.md) and
[role skill selection](../workflow/engineering-delivery.md#role-skills-and-empty-projects).
