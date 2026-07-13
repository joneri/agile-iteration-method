# Your First AIM Journey

This path takes a new user from installation to the first accepted increment.

You do not need to read the full AIM method first.

## 1. Install AIM

From the repository where you want to use AIM, run:

```bash
curl -fsSL https://joneri.github.io/agile-iteration-method/install.sh | bash
```

The public bootstrap fetches the current maintained `main` archive and starts
the guided installer from a temporary directory. The installer asks which
repository to install AIM into; it does not assume the current shell directory is
the target. You do not need to clone the AIM source repository.

To test a specific branch or tag:

```bash
curl -fsSL https://joneri.github.io/agile-iteration-method/install.sh | AIM_REF=main bash
```

The guided installer:

- completes filesystem paths with Tab
- lets you select one or more adapters
- creates an editable project role profile and supplier-native specialists
- shows a compact preview
- protects collisions with explicit choices
- asks before writing
- can apply in the same session

Installation is manifest-driven, rollback-protected, and safe to rerun.

There is one standard installation. Protected repositories can still select an
advanced local-only or external footprint, but they do not install a different
edition of AIM. Older Personal, Team, and Enterprise flags remain migration
compatibility inputs only.

Already have AIM 1.x or older AIM helper files in the target repository?
Run `/aim upgrade` before continuing.
Upgrade refreshes installed AIM-owned surfaces through the reviewed installer plan and keeps active `.aim/` runtime state intact.

For automation, pass installer flags after `bash -s --`, such as
`--target /path/to/repo`, `--non-interactive`, or `--format json`.
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

## 4. Start an Epic

Describe the outcome, not a list of files to edit.

```text
/aim start "EPIC: Make checkout recovery clear and reliable for users whose payment confirmation is delayed"
```

Choose:

- **Strict** when you want explicit approval at each important gate
- **Auto** when the direction is clear and you want AIM to continue between increments unless escalation is needed

Start with Cost Control for narrow, reversible work.
Use Standard or Deep when risk and uncertainty justify more context and verification.

## 5. Review Gate A

Gate A confirms the Epic.

Check:

- is the outcome clear?
- are important non-goals visible?
- is acceptance understandable?
- are trust, migration, deployment, or user-facing risks identified?

Approve when AIM is solving the right problem.
Request a change when the framing is wrong.

## 6. Approve the Next Increment

AIM proposes one Done Increment at a time.

A good increment:

- delivers recognizable value
- is small enough to review
- includes the relevant implementation and verification
- does not depend on several imaginary future increments before it makes sense

In Strict mode, Gate B waits for approval.
In Auto mode, AIM may continue when the approved Epic makes the next step unambiguous and no escalation condition is present.

## 7. Build With Confidence

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

Install the AIM skill and run:

```text
/aim start "EPIC: ..."
```

### GitHub Copilot

Load the repository AIM skill, then request:

```text
/aim start "EPIC: ..."
```

### Claude

Load the project AIM skill and run `/aim start "EPIC: ..."`. Legacy installed
commands remain compatible. If skill routing is unavailable, state:

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
