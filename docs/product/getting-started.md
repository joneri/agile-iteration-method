# Your First AIM Journey

This path takes a new user from installation to the first accepted increment.

You do not need to read the full AIM method first.

## 1. Install AIM

AIM has two maintained installation paths. Both deliver the complete AIM
method; the public Agent Skill is not AIM Lite and is generated from the same
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

## Shape and run a Portfolio

After calibration, AIM can reuse verified repository knowledge across sessions
and load the runtime, decisions, accepted delivery evidence, code, and docs that
matter to the current question. It does not keep every repository byte in one
prompt or treat old history as automatic truth.

Start the control room from the authoritative Codex task for this repository:

```text
/aim ui
```

That launch connects eligible Start and Approve actions to the same Codex task
when Codex uses ChatGPT-managed usage. AIM UI shows **Codex connected** when the
route is available and **View only** with setup instructions when it is not.
The read-only board and reviewed handoff remain usable in either state.

Use AIM Discuss to shape the product direction before creating work:

```text
/aim discuss "What outcomes belong in our next Roadmap?"
```

Discuss is analysis only. When the direction is ready, promote it explicitly:

```text
/aim to-backlog
```

Paste the reviewed Epics, include them in the same message, or use
`/aim to-backlog from docs/product-plan.md` for one explicit source. AIM creates
planned `INC-*` candidates. Review their order and scope in the Portfolio tab,
then run:

```text
/aim start "PORTFOLIO" mode:auto
```

AIM freezes the eligible ordered snapshot and asks for one bounded Portfolio
mandate. After approval, AIM runs every included Epic through the complete
PO/TDO/Dev/Reviewer/TDO/PO loop without repeating decisions already covered by
that mandate. Follow the movement in AIM UI—or step away.

AIM returns control when scope changes, effects become unsafe, evidence is
contradictory, concurrency conflicts, or an operator decision is required.
`/aim continue` resumes the preserved checkpoint after the issue is resolved.

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

## 5. Start an Epic

Describe the outcome, not a list of files to edit.

```text
/aim start "EPIC: Make checkout recovery clear and reliable for users whose payment confirmation is delayed"
```

Choose:

- **Strict** when you want explicit approval at each important gate
- **Auto** when the direction is clear and you want AIM to continue between increments unless escalation is needed

Start with Cost Control for narrow, reversible work.
Use Standard or Deep when risk and uncertainty justify more context and verification.

## 6. Review Gate A

Gate A confirms the Epic.

Check:

- is the outcome clear?
- are important non-goals visible?
- is acceptance understandable?
- are trust, migration, deployment, or user-facing risks identified?

Approve when AIM is solving the right problem.
Request a change when the framing is wrong.

## 7. Approve the Next Increment

AIM proposes one Done Increment at a time.

A good increment:

- delivers recognizable value
- is small enough to review
- includes the relevant implementation and verification
- does not depend on several imaginary future increments before it makes sense

In Strict mode, Gate B waits for approval.
In Auto mode, AIM may continue when the approved Epic makes the next step unambiguous and no escalation condition is present.

## 8. Build With Confidence

AIM implements the increment, reviews it, validates it, and corrects blocking findings.

At the final checkpoint you should see:

- what changed
- what was verified
- what risks remain
- whether the Epic is complete
- what decision is needed

You can approve, request a change, continue with another increment, or close the Epic.

## A Good First Epic

Prefer an outcome like:

```text
EPIC: Let a new contributor install the project and run its checks without private setup knowledge.
```

Avoid a loose task pile like:

```text
Update README, refactor setup script, maybe fix CI, add tests if needed.
```

The Epic gives AIM a destination.
The increment gives AIM a controlled next step.

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
/aim start "EPIC: ..."
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
/aim start "EPIC: ..."
```

### Claude

Install the public skill directly for Claude Code:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method \
  --agent claude-code \
  --yes
```

Run `/aim start "EPIC: ..."`. Legacy installed commands remain compatible. If
skill routing is unavailable, state:

```text
EPIC: ...
Mode: Strict
Cost profile: Standard
```

## Where To Go Next

- [What AIM is](what-is-aim.md)
- [Platforms and project agents](platforms-and-adoption.md)
- [Detailed installation](../workflow/install-aim-2.0.md)
- [Canonical workflow](../workflow/agile-iteration-method.md)
- [Troubleshooting](../workflow/troubleshoot-aim-2.0.md)
