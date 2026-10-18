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
- **Make user needs explicit.** PO owns Epic outcomes and product priority.
  TDO owns Stories and criteria and plans a coherent increment.
- **Deliver useful behavior.** Build and verify the selected Stories; their
  integrated working result is an increment. A Sprint is an optional timebox.
- **Review before acceptance.** Separate implementation from correctness and
  risk review.
- **Keep human control.** You approve the relevant direction, selected Stories and
  delivered result. AIM stops when intent, scope, trust, or evidence is unclear.
- **Reuse repository knowledge.** AIM remembers verified commands, constraints,
  documentation, and risk areas without loading the whole repository every time.

The result is less wandering, less repeated context, and a visible path from an
idea to software that can be demonstrated and judged.

## Shared learning during delivery

During delivery AIM recalls relevant shared advice and contributes a new verified
reusable correction or independently confirmed reusable failure with existing
proof. An unverified remedy stays explicitly proposed. This needs no manual reflection command
or new routine report. Agent-performed hooks do not guarantee complete automatic
capture from every repo; missing entries are unknown coverage.

The old `reflect` and `reflect-all` names are retired compatibility aliases for
bounded read-only registry views. They are not a normal learning step and do not
scan repos or promote knowledge. Profiles,
architecture facts and useful successful patterns remain in their maintained
project sources. Ask for a targeted audit when a concrete stale fact,
contradiction or suspected missing lesson cannot be settled by the registry.
Its source scope and stopping point stay bounded by the actual mandate.

## How AIM Delivers Software

Every delivery follows `PO → TDO → Dev → Reviewer → TDO → PO`.
PO owns Epic outcomes and product priority. TDO creates and owns Stories and
criteria for the relevant needs, then proposes a coherent increment of ready
Stories. A selection can include several Epics.
Dev implements the selection, Reviewer checks the actual result, and TDO
validates each Story's criteria and the integration between them.

Gate A confirms direction and requirements; Gate B confirms the selected plan.
These can share one clearly scoped response. Gate E accepts the verified Stories.
Epic closure requires a separate assessment and decision. Strict asks for plan
approval and acceptance; Auto progresses within existing authority but does not
invent final acceptance. See [User Stories](user-stories.md).

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

Describe the result you want, or supply an existing detailed requirement:

```text
/aim start "Make checkout recovery clear and reliable when payment confirmation is delayed"
```

PO owns Epics; TDO creates and owns Stories. AIM presents the relevant direction and
first Story selection together for approval.
Implementation begins only within approved scope.

## Your First AIM Journey

The steps below describe the default `Strict` experience. In `Auto`, AIM reports
the same checkpoints but may continue without pausing when no escalation applies.

1. **Discover needs.** PO preserves intent and owns Epics. TDO creates and owns Stories
   and criteria for the relevant user perspectives.
2. **Choose the next delivery.** PO orders Stories; TDO proposes a feasible
   selection, potentially across Epics, with implementation and verification scope.
3. **Build and review.** Dev implements the selection. Reviewer checks current
   behavior and TDO validates evidence for every Story criterion.
4. **Accept proven behavior.** You accept the named Stories after seeing the
   evidence. Failures remain unfinished and return for correction.
5. **Assess outcomes.** PO separately evaluates which Epics can close and which
   need more work. The backlog retains remaining needs for the next selection.

At any point, `/aim help` recommends one useful next action based on the current
state instead of showing a wall of internal options.

## Complete Command Guide

You can use the commands directly or express the same intent in plain language.
When literal slash commands are unavailable, AIM preserves the same behavior and
state transitions through the platform's native skill route.

### Start and continue delivery

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim start "<desired outcome>"` | You have a new desired outcome. | PO owns Epics and priority; TDO owns Stories and plans a coherent increment. | Review relevant direction and the selected Story plan. |
| `/aim start "PORTFOLIO" mode:auto` | You want AIM to finish the visible Backlog sequentially. | Previews one immutable snapshot and asks for one bounded Portfolio mandate. | After approval, AIM runs included Epics through the full loop and pauses only on escalation. |
| `/aim continue` | An AIM run already exists. | Reads the durable checkpoint and continues from the current role and gate. | AIM performs the next automatic step or presents the next decision. |
| `Start working according to AIM` | You want to begin but prefer plain language. | Maps the request to AIM startup without changing method semantics. | AIM detects whether to calibrate, start, or resume. |

### Find the right next action

| Command | Use when | What it does | What happens next |
| --- | --- | --- | --- |
| `/aim help` | You are unsure what to do now. | Detects the current onboarding or runtime state and recommends one action. | Follow the named command or resolve the named blocker. |
| `/aim status` | You want a concise progress report. | Shows the AIM release from the trusted package's `VERSION` or `manifest.json` `productVersion`, separately from `.aim/state.json` `aimVersion`, then the active Epic, increment, role, mode, cost profile, gate, and expected next step. | Continue automatically or make the decision the status identifies. |
| `/aim graph` | You want to know what can start and what blocks the delivery. | Shows dependencies, recorded activity attempts, current proof and bounded next assignments. | Continue the recommended work through the existing AIM mandate; inspect it visually in AIM UI's Graph tab. |
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
| `/aim cost standard\|control\|deep` | Work needs a different context and review depth. | Selects normal, budget-focused, or risk-focused execution without weakening AIM roles or gates. | AIM uses that depth; material resource changes require applicable authority. |
| `/aim replan` | A legacy Epic/DI increment needs a different plan. | Returns that unaccepted legacy increment to Gate B with its reason and accepted history preserved. | Review the revised legacy plan. Story deliveries preserve their approved scope; see the blocked-commitment limitation in [User Stories](user-stories.md). |

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
