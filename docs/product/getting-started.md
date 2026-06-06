# Your First AIM Journey

This path takes a new user from installation to the first accepted increment.

You do not need to read the full AIM method first.

## 1. Install AIM

From the AIM source repository, run:

```bash
python3 scripts/aim_install.py
```

The guided installer:

- completes filesystem paths with Tab
- lets you choose a mode with arrow keys
- lets you select one or more adapters
- shows a compact preview
- protects collisions with explicit choices
- asks before writing
- can apply in the same session

Installation is manifest-driven, rollback-protected, and safe to rerun.

If AIM was already installed and the AIM package changed later, run `/aim upgrade` before continuing.

For automation, use flags with `--non-interactive` or `--format json`.
For preview only, use `--dry-run`.

## 2. Calibrate the Repository

Run:

```text
/aim calibrate-repo
```

Calibration starts with cheap, obvious repository evidence.
It identifies likely technologies, commands, important folders, validation paths, and documents that should load only when needed.

Review uncertain or trust-sensitive facts before they become reusable repository knowledge.

If your platform does not expose slash commands, ask AIM to verify and refine repo awareness for the repository.

## 3. Start an Epic

Describe the outcome, not a list of files to edit.

```text
/aim start "EPIC: Make checkout recovery clear and reliable for users whose payment confirmation is delayed"
```

Choose:

- **Strict** when you want explicit approval at each important gate
- **Auto** when the direction is clear and you want AIM to continue between increments unless escalation is needed

Start with Cost Control for narrow, reversible work.
Use Standard or Deep when risk and uncertainty justify more context and verification.

## 4. Review Gate A

Gate A confirms the Epic.

Check:

- is the outcome clear?
- are important non-goals visible?
- is acceptance understandable?
- are trust, migration, deployment, or user-facing risks identified?

Approve when AIM is solving the right problem.
Request a change when the framing is wrong.

## 5. Approve the Next Increment

AIM proposes one Done Increment at a time.

A good increment:

- delivers recognizable value
- is small enough to review
- includes the relevant implementation and verification
- does not depend on several imaginary future increments before it makes sense

In Strict mode, Gate B waits for approval.
In Auto mode, AIM may continue when the approved Epic makes the next step unambiguous and no escalation condition is present.

## 6. Build With Confidence

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

Select the AIM agent, then run:

```text
/aim start "EPIC: ..."
```

### Claude

Use the installed AIM start command.
If command packaging is unavailable, state:

```text
EPIC: ...
Mode: Strict
Cost profile: Standard
```

## Where To Go Next

- [What AIM is](what-is-aim.md)
- [Platforms and adoption modes](platforms-and-adoption.md)
- [Detailed installation](../workflow/install-aim-2.0.md)
- [Canonical workflow](../workflow/agile-iteration-method.md)
- [Troubleshooting](../workflow/troubleshoot-aim-2.0.md)
