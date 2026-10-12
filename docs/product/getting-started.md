# Your First AIM Journey

This path takes a new user from an intent to accepted User Stories. You do not
need to supply an Epic or read the full method first. PO discovers outcomes and
needs; TDO refines and plans delivery with PO. Chat and terminal agents are
complete paths without AIM UI. Continue resumes authorized work; it does not
approve a waiting decision. See [User Stories](../workflow/user-stories.md).

## 1. Install AIM

AIM has two maintained installation paths. Both deliver the complete AIM
method; the public Agent Skill is full AIM, not AIM Lite and is generated from the same
canonical sources as the adaptive installation.

### Public Agent Skill

Use the standard skills CLI when you want a portable, self-contained AIM skill
for Codex, GitHub Copilot, Claude Code, or another compatible agent:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method
```

The installed skill contains the full role loop, gates, operating modes,
repository calibration, project-agent configuration, scope escalation, and
sequential fallback. It does not require the AIM source repository to remain
available locally.

Update it through the standard CLI:

```bash
npx skills update agile-iteration-method --yes
```

After installation, `/aim configure-agents` can still generate or refresh
project-specific native specialists from `aim.roles.yaml`.

See [Public Agent Skill distribution](../workflow/version-and-installation.md)
for agent-specific commands, versioning, generation, and publication details.

### Adaptive Installer

Use the adaptive installer when you want AIM to inspect a target repository,
offer one or more native adapters, seed project-specific role configuration,
and apply the selected repository footprint. Keep the source visible and begin
with a no-write preview:

```bash
git clone --depth 1 https://github.com/joneri/agile-iteration-method.git aim-source
cd aim-source
python3 scripts/aim_install.py --dry-run
```

Review the checkout and the preview, then rerun with `--apply` only when the
plan is correct. The installer asks which repository to install AIM into; it
does not assume the current shell directory is the target. AIM no longer
recommends a remote pipe-to-shell bootstrap.

The guided installer:

- completes filesystem paths with Tab
- lets you select one or more adapters
- creates an editable project role profile and supplier-native specialists
- shows a compact preview
- protects collisions with explicit choices
- asks before writing
- can apply in the same session
- installs the read-only AIM UI into repo-writing footprints or the external AIM
  home distribution for zero-repo-write footprints

Installation is manifest-driven, rollback-protected, and safe to rerun.

There is one standard installation. Protected repositories can still select an
advanced local-only or external footprint, but they do not install a different
edition of AIM. Older Personal, Team, and Enterprise flags remain migration
compatibility inputs only.

Already have AIM 1.x or older AIM helper files in the target repository?
Run `/aim upgrade` before continuing.
Upgrade refreshes installed AIM-owned surfaces through the reviewed installer plan and keeps active `.aim/` runtime state intact.

For automation, pass installer flags directly, such as `--target
/path/to/repo`, `--non-interactive`, or `--format json`.
For preview only, use `--dry-run`.

## 2. Calibrate the Repository

Run:

```text
/aim calibrate-repo
```

Calibration starts with cheap, obvious repository evidence.
It identifies likely technologies, commands, important folders, validation paths, and documents that should load only when needed.

Review uncertain or trust-sensitive facts before they become reusable repository knowledge.

The installer also seeds `aim.roles.yaml` from cheap observable evidence. After
calibration, inspect or improve the role specialists:

```text
/aim configure-agents
```

AIM shows proposed changes before refreshing Codex, Claude, or Copilot native
agent files. You can also edit `aim.roles.yaml` or the supplier-native files
manually.

If your platform does not expose slash commands, ask AIM to verify and refine repo awareness for the repository.

## Follow the Story board

Run `/aim ui` to open the local control room. User Stories are the moving cards;
each shows its Epic context. A delivery can select Stories from different Epics.
The browser reflects saved evidence and cannot accept work itself.

Use `/aim discuss "Which users and outcomes should we consider?"` for read-only
exploration before starting. To turn the idea into requirements and delivery,
use `/aim start "<desired outcome>"` as described below.

Existing Roadmap, Portfolio and Epic/Increment runs remain available as legacy
work. Their original commands and approvals remain valid for those records;
they do not become User Stories automatically.

## 3. Remember Important Project Context

After calibration, teach AIM durable facts that should guide future work.
Good memory candidates are short product facts, tone rules, project constraints,
team habits, validation expectations, or areas that deserve special care.

Example:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. User-facing language should be nuanced, calm, and empathetic toward both the cats and future owners."
```

AIM maps the request into structured repo-awareness, shows the proposed change,
and stores stable shared facts in `aim.profile.yaml` or personal preferences in
user-level hints. It should not store reusable project knowledge in `.aim/`.

## 4. Reflect on Completed Work

When the repository already has completed AIM history, ask it to propose
knowledge worth keeping:

```text
/aim reflect
```

To compare selected local AIM projects:

```text
/aim reflect-all
```

Reflect-all previews discovery roots, repositories, exclusions, and workload
before reading unapproved project content. Both commands create temporary
candidate reports. Their completion response tells you whether anything needs
attention and gives one concrete `remember-repo`, `forget-repo`, reviewed edit,
or Epic path. When no durable change is justified, Reflect says that no action
is needed. You still decide whether to run or approve the proposed action.

## 5. Start with intent

Describe the problem or desired result:

```text
/aim start "Make checkout recovery clear for customers and help support staff resolve delayed payment confirmations"
```

PO identifies the relevant Epics and Stories for those different users. A
customer may need a reliable payment status; a support specialist may need a
safe way to find the delayed confirmation. These needs retain separate identity,
priority and acceptance criteria even when delivered together.

Choose Strict for explicit plan approval and acceptance. Auto progresses within
existing authorization and returns for scope changes, risks and final acceptance.
Cost Control suits narrow reversible work; Standard or Deep provide more context
and verification when warranted. None of these settings replaces user authority.

## 6. Refine needs and choose the delivery

PO owns Story value, criteria and ordering. TDO refines feasibility, dependencies
and verification with PO, then proposes which ready Stories to implement next.
A delivery can span Epics; a Story need not cover every aspect of its Epic.

Check that the proposal names the selected Stories, their user needs, criteria,
implementation boundaries, integration checks and remaining scope. Gate A
confirms direction and requirements; Gate B approves the selection and plan.
A clearly scoped decision may cover both.

## 7. Build, review and validate

Dev implements the approved selection. Reviewer examines current behavior and
risks. TDO verifies evidence for every selected Story criterion and for the
integrated result. Defects return for correction. The board shows these stages
without pretending that elapsed time or a successful build proves acceptance.

## 8. Accept Stories and assess Epics

Review the demonstration, criterion evidence and limitations. Gate E accepts
the named Story selection; the current helper requires every selected Story to
be proven before accepting that delivery. Its working result is an increment.

PO then separately assesses the Epic outcomes. Finishing the delivery can leave
one or several Epics open. Closing an Epic requires its whole-outcome evidence
and a separate scoped decision. A Sprint is an optional timebox and does not
change these acceptance rules.

## Platform Starts

### Codex

Install the public skill directly for Codex:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method \
  --agent codex \
  --yes
```

Then run:

```text
/aim start "<desired outcome>"
```

### GitHub Copilot

Install the public skill directly for GitHub Copilot:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method \
  --agent github-copilot \
  --yes
```

Then request:

```text
/aim start "<desired outcome>"
```

### Claude

Install the public skill directly for Claude Code:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method \
  --agent claude-code \
  --yes
```

Run `/aim start "<desired outcome>"`. Legacy installed commands remain compatible. If
skill routing is unavailable, state:

```text
Start AIM from this intent: <desired outcome>
Mode: Strict
Cost profile: Standard
```

## Where To Go Next

- [What AIM is](what-is-aim.md)
- [Platforms and project agents](platforms-and-adoption.md)
- [Detailed installation](../workflow/install-aim-2.0.md)
- [Canonical workflow](../workflow/agile-iteration-method.md)
- [Troubleshooting](../workflow/troubleshoot-aim-2.0.md)
