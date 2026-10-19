> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# Quick Start AIM

Use this page when AIM is installed and you want to begin real work.

New to the product? Read the [public first-time journey](../product/getting-started.md) first.

The public Agent Skill is the standard portable installation. It provides the
complete AIM method, then guides repository setup through calibration and
project-specialist configuration. The adaptive installer may seed those project
files during its guided setup instead.

Open the repository's local read-only control room at any point with:

```text
/aim ui
```

It starts or reopens the current repo's UI and returns a clickable loopback
URL. `/aim ui start /path/to/repo` targets another repository. A repo without
`.aim` opens an onboarding view without initializing runtime state.

## 1. Start from the desired outcome

Run:

```text
/aim start "<desired outcome>"
```

AIM calibrates missing or stale repository knowledge as part of this start.
For an empty repository it uses the intent to record provisional facts, then
verifies them as implementation takes shape. Calibration checks the smallest
useful set of repository facts:

- technologies and package tooling
- likely validation commands
- important localities
- risk areas
- documents that should load only when relevant

Shared knowledge belongs in `aim.profile.yaml`.
Personal hints belong in user-level storage.
Active work state belongs in `.aim/`.

If slash commands are unavailable, describe the outcome in natural language;
AIM performs the same preparation.

## 2. Add durable context when needed

For later runs, remember important product context when it should guide work:

```text
/aim remember-repo habits "Product context: This app helps people find new homes for cats. User-facing language should be nuanced, calm, and empathetic toward both the cats and future owners."
```

Use this for durable facts, tone, constraints, team habits, and validation
expectations. AIM should show the proposed structured change before storing
shared repository knowledge.

You can also start with explicit mode and cost choices:

```text
Start AIM from this intent: <desired user outcome>
Delivery: Ship
Mode: Strict
Cost profile: Standard
```

An idea or detailed requirements are both valid starting points.
PO owns Epics and product priority. TDO owns Stories, criteria and the coherent
increment, reusing decisions and clarifying only consequential gaps. See
[User Stories](user-stories.md).

## 3. Choose Delivery and Execution Style

**Ship is the default** for complete agreed product delivery. Select **Loop**
explicitly for useful Done Increments and recurring owner feedback. Both include
review, verification and correction. Existing work keeps its frozen policy.

Promote **Graph engineering**: let the current agent coordinate outcome ownership,
delivery dependencies and evidence. "Use AIM in Strict Loop; act as my product
owner within [outcome, allowed decisions and resource limit]" allows an explicitly
delegated owner agent to assess increments. Record the real mandate and actual
scoped decisions through [User Stories](user-stories.md); a role alone grants
no authority. A separate reviewer checks material implementation.

Approval mode is independent:

- `Mode: Strict`: pause at Gate A, Gate B, and Gate E
- `Mode: Auto`: continue authorized work without inventing owner acceptance;
  ordinary Epic closure still requires explicit user approval
- Legacy `Portfolio Auto`: the one approved bounded mandate is the explicit PO
  authority for each separate eligible Epic closure, so AIM advances across its
  immutable snapshot without another user message unless escalation is required

Strict is a good default for first use and trust-sensitive work.
Auto is useful when the outcome and boundaries are already clear.

## 4. Choose Runtime Depth

- `Cost profile: Cost Control`: narrow, reversible, low-risk work
- `Cost profile: Standard`: normal product work
- `Cost profile: Deep`: security, migration, deployment, public APIs, or broad trust-sensitive changes

Cost profile changes context and verification depth.
It does not remove AIM roles, gates, ownership, or escalation.

## 5. Review Gate A

Confirm:

- outcome
- scope boundaries
- acceptance intent
- important risks

Review the relevant Epic direction and Story requirements with the first
delivery plan; one clearly scoped response can approve both.
Use `change: ...` when it needs correction.

## 6. Review the Story selection

AIM proposes ready Stories to deliver, potentially across several Epics.

In Strict mode, Gate B waits for approval.
The plan binds exact Story IDs, criteria, implementation boundaries and checks.
It need not approximate the whole Epic.

Before implementation, agree the product quality goals and how the important
behavior will be measured. Preserve the relevant original intent and Epic
obligations alongside Story criteria. Measure the first working core; a separate
reviewer challenges a material core before the implementation expands.

Use the project's runnable verification entry and maintained map of user
journeys. Check the delivered entry point and complete-result time when relevant.
Keep raw results behind the assessment. Reuse them only while the affected
behavior and dependencies still match; missing, failed or stale evidence needs
correction or a responsible owner decision.

After implementation and review, Gate E reports:

- delivered behavior
- verification evidence
- remaining risk
- criterion-level evidence for every selected Story
- remaining needs and a separate Epic-closure recommendation

Accept the proven Stories or request correction. Epic closure requires separate
whole-outcome evidence and scoped authority. An increment is the working result;
a Sprint is an optional timebox.

## Common Commands

- `/aim ui [start|open|status|stop] [repo]`
- `/aim continue`
- `/aim upgrade`
- `/aim status`
- `/aim validate`
- `/aim configure-agents`
- `/aim calibrate-repo`
- `/aim remember-repo <category> "<rule>"`
- `/aim forget-repo <category> "<rule-id>"`
- `/aim cost standard|control|deep`
- `/aim help`

Learning happens during planning, review and diagnosis. AIM recalls relevant
shared advice and shares new verified reusable corrections with existing proof.
No manual reflection command or routine report is needed. The old `reflect`
and `reflect-all` names are retired compatibility aliases for read-only views.
See [shared learning](reflection.md).

## When AIM Itself Was Updated

Use this flow when AIM instruction files, helper prompts or adapter packaging
have changed since installation.

1. Run `/aim upgrade`
2. Run `/aim calibrate-repo` if repository facts may be stale
3. Start a fresh adapter session when helper files or agent/skill packaging changed
4. Resume with `/aim continue` if work was already in progress

Upgrade refreshes installed AIM surfaces.
Calibration refreshes repo-awareness.
They are related, but not the same action.

## Tune Project Specialists

The adaptive standard setup creates native AIM role files for the selected
adapters and a shared `aim.roles.yaml` profile. A portable public-skill install
does not claim those project files already exist. When a new intent is supplied,
AIM configures missing or stale role files and skill bindings during the same
start. To refresh them separately later, run:

```text
/aim configure-agents
```

Use it after a public-skill installation, when the stack changes, or when PO,
TDO, Dev, and Reviewer need stronger project-specific instructions. AIM previews
the proposed profile and native-file changes before applying them.

There is no edition to choose. Older Personal, Team, and Enterprise flags are
migration inputs only; see [Operating modes](operating-modes.md).

## Need Help?

- [Installation](install-aim-2.0.md)
- [Troubleshooting](troubleshoot-aim-2.0.md)
- [Platform entrypoints](adapter-entry-model.md)
- [Canonical AIM workflow](agile-iteration-method.md)

For the startup storage, host capability and idempotence boundaries, follow
[intent preparation](skill-command-runtime.md#intent-led-start-and-story-continuation).
Use `/aim calibrate-repo` or `/aim configure-agents` for later explicit refreshes.
