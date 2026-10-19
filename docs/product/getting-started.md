# Your First AIM Journey

Start with the product you want. **Ship** is the default: complete the agreed
result before final acceptance. Choose **Loop** for useful Done Increments with
recurring owner feedback. You do not need to supply a backlog or read the full
method first.

Open **AIM UI** with `/aim ui` to follow Stories, the current delivery and its
evidence. The **Graph** view shows recorded dependencies, blockers and bounded
next assignments. Graph engineering makes ownership and prerequisites explicit;
it does not grant agents permission to decide. Chat and terminal remain complete
paths. Continue resumes authorized work and never approves a waiting decision.
See [User Stories](../workflow/user-stories.md) and [AIM UI](aim-ui.md).

## 1. Install AIM

AIM has two maintained installation paths. Both deliver the complete AIM
method; the public Agent Skill is full AIM, not AIM Lite and is generated from the same
canonical sources as the adaptive installation.

### Recommended: one command

Use the standard skills CLI when you want a portable, self-contained AIM skill
for Codex, GitHub Copilot, Claude Code, or another compatible agent:

```bash
npx skills add joneri/agile-iteration-method \
  --skill agile-iteration-method
```

Select your agent and project. Then describe your desired result:

```text
/aim start "Make checkout recovery clear when payment confirmation is delayed"
```

For an agent doing the setup, copy the [short installation instructions](../../github-pages/assets/aim-install-agent.txt).
Node.js/npm runs the installer; Python 3 runs AIM's local helpers. Reopen the
agent session if it does not discover the newly installed skill.

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

### Optional: guided repository setup

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
A portable skill upgrade uses the standard skills CLI. A separate adaptive setup uses its reviewed installer plan. Both preserve active AIM state and accepted history.

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

## Choose delivery and ownership

**Ship is the default:** AIM completes the agreed product outcome before final
acceptance, with internal tests, independent review and correction throughout.
Choose **Loop** to receive useful Done Increments and give feedback before the
next selection. Delivery style is separate from Strict/Auto approvals and cost
depth. Existing deliveries keep their original policies.

Use **Graph engineering** when asking your agent to coordinate the work: name
who owns the outcome, who delivers, their dependencies and the required evidence.
The agent you are speaking with can act as product owner under an explicit
mandate, while an AIM delivery coordinator executes and an independent reviewer
checks the result. For example:

```text
Use AIM in Strict Loop. Act as my product owner and delegate delivery.
Assess each verified increment, request corrections when needed, and select
what comes next. Your mandate covers [outcome and allowed decisions]
within [resource limit]. Keep [reserved decisions] with me.
```

The owner must actually evaluate each result. Agent decisions need the explicit
human delegation and scoped evidence in [User Stories](../workflow/user-stories.md);
a role assignment or Auto setting cannot replace that mandate. Ship completes
its agreed result; it does not itself authorize publication or deployment.

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

## 4. Reuse Learning During Work

AIM recalls relevant shared advice during planning, material review and failure
diagnosis. It shares new verified reusable corrections and independently
confirmed failures with existing proof; an unverified remedy stays proposed.
No manual reflection command or routine report is required. The old `reflect`
and `reflect-all` names are retired compatibility aliases for read-only views.
If a named stale fact,
contradiction or missing lesson remains unresolved, request a targeted audit
with a concrete scope; existing project facts and write authority stay intact.

## 5. Start with intent

Describe the problem or desired result:

```text
/aim start "Make checkout recovery clear for customers and help support staff resolve delayed payment confirmations"
```

PO identifies the relevant Epics; TDO creates Stories for those different users. A
customer may need a reliable payment status; a support specialist may need a
safe way to find the delayed confirmation. These needs retain separate identity,
priority and acceptance criteria even when delivered together.

Choose Strict for explicit plan approval and acceptance. Auto progresses within
existing authorization and returns for scope changes, risks and final acceptance.
Cost Control suits narrow reversible work; Standard or Deep provide more context
and verification when warranted. None of these settings replaces user authority.

## 6. Refine needs and choose the delivery

PO owns Epic outcomes and product priority. TDO owns Story formulation, criteria,
dependencies and verification, then proposes a coherent increment of ready Stories.
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
