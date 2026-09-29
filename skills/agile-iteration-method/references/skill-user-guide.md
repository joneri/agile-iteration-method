<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/skill-user-guide.md
-->

# AIM user guide

Read for installation, onboarding or the full command overview.

## Why AIM

AI coding agents are fast, but speed alone does not keep a product coherent.
Without a delivery method, scope can expand silently, implementation can outrun
the goal, and apparent progress can become a collection of partial changes that
no user can evaluate.

AIM gives AI-assisted development a clear delivery shape:

- **Start from an outcome.** Define the user or product result before choosing
  implementation tasks.
- **Deliver one useful increment.** Build a small version of the whole behavior,
  not an isolated piece that only becomes valuable later.
- **Review before acceptance.** Separate implementation from correctness and
  risk review.
- **Keep human control.** You approve the Epic, the next increment, and the
  delivered result. AIM stops when intent, scope, trust, or evidence is unclear.
- **Reuse repository knowledge.** AIM remembers verified commands, constraints,
  documentation, and risk areas without loading the whole repository every time.

The result is less wandering, less repeated context, and a visible path from an
idea to software that can be demonstrated and judged.

## AIM Reflect

Completed delivery history contains useful lessons, but history is evidence—not
automatic truth.

- `/aim reflect` finds reusable knowledge in the current AIM project.
- `/aim reflect-all` previews selected local AIM projects and finds
  project-specific, cross-project, personal, and AIM-product insights.

Every candidate carries provenance, current-source verification, confidence,
contradictions, a proposed durable destination, and an explicit promotion
action. Reports stay temporary under `.aim/analysis/`; reflection never changes
profiles, docs, source, active state, or another repository.

Agent-memory systems such as Anthropic Dreams consolidate accumulated memories
and session history. **AIM Reflect goes beyond memory cleanup for repository
work**: it asks whether a lesson is still true in current code, where it belongs,
which projects support it, and who approved keeping it.

## How AIM Delivers Software

Every Done Increment follows one explicit loop:

`PO -> TDO -> Dev -> Reviewer -> TDO -> PO`

- **PO** defines the desired outcome and decides whether the result delivers
  enough value.
- **TDO** chooses the next end-to-end Done Increment and defines how it will be
  demonstrated and validated.
- **Dev** implements exactly the approved increment.
- **Reviewer** looks for correctness problems, regressions, unsafe assumptions,
  and missing evidence.
- **TDO** turns implementation and review into a practical acceptance checkpoint.
- **PO** accepts the increment, requests a correction, or decides what comes next.

Gate A approves the Epic. Gate B approves the next Done Increment. Gate E accepts
the delivered result. Implementation and review checkpoints happen in between,
but AIM does not ask you to approve routine internal handoffs.

This is the default `Strict` experience: AIM pauses at each hard gate for your
decision. `Auto` still reports the same gates and preserves the same ownership,
but it continues between increments while the approved direction remains clear.
Risk and scope changes always return to you. Final Epic acceptance also returns
to you in ordinary Auto; Portfolio Auto instead uses its already approved,
bounded mandate as the explicit PO authority for each eligible separate Epic
closure.

## Start Here

### 1. Install AIM

Install the complete public Agent Skill from the repository:

```bash
npx skills add joneri/agile-iteration-method --skill agile-iteration-method
```

Choose Codex, GitHub Copilot, or Claude Code when the skills CLI asks where AIM
should be installed. If AIM is already installed, update it with:

```bash
npx skills update agile-iteration-method --yes
```

### 2. Calibrate the repository

Let AIM identify the technologies, commands, documentation, and risk areas it
may safely reuse:

```text
/aim calibrate-repo
```

Calibration is reviewable repository knowledge, not permission to change code.

### 3. Start with an outcome

Describe the result you want rather than supplying a task list:

```text
/aim start "EPIC: Make checkout recovery clear and reliable when payment confirmation is delayed"
```

AIM first frames the Epic for your approval. It does not begin implementation
until the outcome and the first Done Increment are understood.

## Your First AIM Journey

The steps below describe the default `Strict` experience. In `Auto`, AIM reports
the same checkpoints but may continue without pausing when no escalation applies.

1. **Frame the outcome.** PO turns your request into an Epic with value,
  boundaries, and acceptance criteria. In Strict mode, you approve or adjust it
  at Gate A.
2. **Choose one useful increment.** TDO proposes the smallest end-to-end behavior
  that can be demonstrated and evaluated. In Strict mode, you approve or adjust
  it at Gate B.
3. **Build and review.** Dev implements the approved scope. Reviewer checks the
   result independently. AIM corrects local defects before presenting the work.
4. **Evaluate evidence.** TDO explains what changed, what was verified, and how
   to test or demonstrate it.
5. **Keep the decision.** PO asks you to accept the increment or request
   changes. After acceptance, PO evaluates the Epic and recommends exactly one
   disposition: close, continue, or split. The disposition remains yours in
   ordinary runs; a bounded Portfolio Auto mandate carries that authority for
   its eligible Epics. AIM preserves the checkpoint for the next session.

At any point, `/aim help` recommends one useful next action based on the current
state instead of showing a wall of internal options.

## Complete Command Guide

You can use the commands directly or express the same intent in plain language.
When literal slash commands are unavailable, AIM preserves the same behavior and
state transitions through the platform's native skill route.

### Start and continue delivery

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim start "EPIC: ..."` | You have a new desired outcome. | Creates or resumes the Epic framing process and presents Gate A. | Review the Epic and approve it or request a change. |
| `/aim start "PORTFOLIO" mode:auto` | You want AIM to finish the visible Backlog sequentially. | Previews one immutable snapshot and asks for one bounded Portfolio mandate. | After approval, AIM runs included Epics through the full loop and pauses only on escalation. |
| `/aim continue` | An AIM run already exists. | Reads the durable checkpoint and continues from the current role and gate. | AIM performs the next automatic step or presents the next decision. |
| `Start working according to AIM` | You want to begin but prefer plain language. | Maps the request to AIM startup without changing method semantics. | AIM detects whether to calibrate, start, or resume. |

### Find the right next action

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim help` | You are unsure what to do now. | Detects the current onboarding or runtime state and recommends one action. | Follow the named command or resolve the named blocker. |
| `/aim status` | You want a concise progress report. | Shows the AIM release from the trusted package's `VERSION` or `manifest.json` `productVersion`, separately from `.aim/state.json` `aimVersion`, then the active Epic, increment, role, mode, cost profile, gate, and expected next step. | Continue automatically or make the decision the status identifies. |
| `/aim config` | You need to understand effective AIM policy. | Shows repository awareness, role configuration, validation preferences, ownership, and adapter fallback behavior. | Adjust configuration only when the reported policy is wrong or incomplete. |

### Discuss without starting delivery

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim discuss [question]` | You want to explore product direction, architecture, a tradeoff, or recent delivery without starting work. | Loads only relevant AIM and repository evidence under a strict read-only boundary. | Continue the discussion, or separately invoke the one recommended promotion action if you choose. |

### Open and control AIM UI

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim ui` | You want the current repository's control room. | Starts or reuses the trusted package-owned, loopback-only AIM UI and opens it. | AIM reports one clickable local URL. |
| `/aim ui start [repo]` | You want a control room for the current or an explicit repository. | Resolves the repository, selects a free port, and starts or reuses its UI without creating `.aim`. | The UI opens with runtime evidence or truthful onboarding. |
| `/aim ui open [repo]` | The repo's UI is already running. | Verifies and reopens the matching instance. | The existing local URL opens. |
| `/aim ui status [repo]` | You want to know whether the repo's UI is running. | Verifies process, repository, and instance identity. | AIM reports running/stopped and the URL when available. |
| `/aim ui stop [repo]` | You want to stop only this repo's UI. | Verifies the matching instance before signalling it and removes stale metadata safely. | Runtime state and repository files remain unchanged. |

### Populate AIM UI Backlog

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim to-backlog` | You want to create a Roadmap by pasting several Epic descriptions. | Asks one short question, interprets supplied text as untrusted evidence, and safely merges planned candidates. | AIM reports the result and opens the reviewable Roadmap in the control room. |
| `/aim to-backlog from <source>` | One explicit repository file or available attachment already contains the Roadmap Epics. | Reads only that source, preserves explicit Increment intent, derives one initial candidate where needed, and atomically merges valid `INC-*` candidates. | Ambiguity pauses for review; success opens AIM UI with stationary Epic planning summaries. |
| `/aim repair-catalog <candidate-id>` | Completed runtime-linked history should leave the active Portfolio without becoming Planned work. | Previews one exact workspace, acceptance, catalog, and Backlog transaction and requests explicit approval. | Approved apply archives the workspace unchanged, retires the Backlog record, removes the catalog entry, and writes audit evidence together. |

### Inspect and validate

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim validate` | State looks stale, contradictory, or release readiness matters. | Checks runtime structure, state alignment, repository context, ownership rules, and product coherence. | Continue when healthy, repair recoverable issues, or stop on blocked and contradictory results. |
| `/aim calibrate-repo` | AIM has not learned this repository or its knowledge may be stale. | Verifies the stack, commands, documentation, localities, and risk zones using cheap evidence first. | Review the reusable profile, then start or continue the Epic. |

### Remember repository knowledge

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim remember-repo <category> "<rule>"` | A stable project fact should guide later runs. | Stores a structured shared or personal rule in the correct durable knowledge layer. | Future planning reuses the rule when relevant. |
| `/aim forget-repo <category> "<rule-id>"` | A remembered rule is obsolete or incorrect. | Removes the identified rule without rewriting active runtime evidence. | Later runs stop treating that rule as repository truth. |
| `/aim reflect` | Completed AIM work may contain reusable knowledge. | Verifies current-project evidence, writes a temporary candidate report, and concludes whether action is recommended. | Follow the one concrete recommended action, or stop when AIM says no action is needed. |
| `/aim reflect-all` | Several selected local AIM projects may reveal shared lessons. | Previews safe discovery scope, synthesizes the approved project set, and concludes with an operator-ready next action. | Follow the named promotion path only after reviewing it; discovered projects remain unchanged. |

### Configure and maintain AIM

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `Install AIM` | AIM is not yet available in the active platform. | Routes to the supported installation guidance and identifies the correct skill location. | Reload the platform when required, then calibrate the repository. |
| `/aim upgrade` | The installed skill or adaptive distribution may be outdated. | Uses the standard skills update path or presents a reviewed adaptive-installer plan. | Validate the updated package before resuming active work. |
| `/aim configure-agents` | Native project specialists should match the current stack. | Reviews or refreshes PO, TDO, Dev, and Reviewer configuration from `aim.roles.yaml`. | Selected adapters receive collision-safe specialist updates; active state is unchanged. |

### Control execution

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim mode strict\|auto` | You want to change how AIM pauses at hard gates. | Selects explicit approval pauses or transparent automatic continuation. | The role loop continues under the selected approval policy. |
| `/aim cost standard\|control\|deep` | Work needs a different context and review depth. | Selects normal, budget-focused, or risk-focused execution without weakening AIM roles or gates. | AIM uses that depth and escalates when risk requires more evidence. |
| `/aim replan` | The active unaccepted increment is no longer the right plan. | Returns that increment to Gate B while preserving the Epic and accepted history. | TDO proposes one revised Done Increment for approval. |

### Control a multi-Epic portfolio

When `.aim/ui-portfolio.json` declares several independently authoritative
workspaces, explicit plain-language intents control admission and operator
focus through optional chat-owned `.aim/portfolio-control.json` state:

- `Activate INC-UI-CONTROL-001`
- `Set portfolio capacity to 2`
- `Focus EPIC-BACKLOG-AIM-UI`
- `Show portfolio status`

The main AIM thread counts running canonical workspaces before activating new
work. Full or invalid configured capacity blocks new activation; an already
running Epic can still resume. Lowering capacity below the current running
count reports over-capacity without pausing anything. Focus changes default
chat targeting and read-only UI emphasis, never gates, acceptance, runtime
ownership, or agent authority. Missing control state preserves legacy unbounded
behavior.

**Boundary:** Commands never transfer acceptance, gate progression, or shared
state ownership to a specialist. Installation and validation never execute
similarly named scripts merely because they exist in the target repository.
