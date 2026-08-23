# Changelog

## 2026-08-23 - AIM 2 minor release v2.7.0
- Added Portfolio Auto as a bounded whole-Backlog route: one explicit mandate
  locks an immutable ordered snapshot and coordinates each included Epic
  sequentially through the complete PO/TDO/Dev/Reviewer/TDO/PO loop.
- Aligned Portfolio Auto with the visible AIM UI Backlog by excluding candidates
  that already carry `runtimeIncrementId`, preventing previously activated work
  from being replayed by a later mandate.
- Added an explicit timestamp-guarded `archive` command for validated completed
  or stopped Portfolio runs. Archived evidence remains byte-for-byte contained
  under `.aim/archive/`; active, paused, stale, malformed, symlinked, and
  colliding requests fail without mutation.
- Reshaped AIM UI around stationary Epic swimlanes, open-work-only Delivery,
  safe `Start Epic` actions, stable polling and filters, and dedicated completed
  history without moving Gate or runtime authority into the browser.
- Added AIM DATA delivery outcomes: contained Epic and accepted-Increment
  counts, trailing 7/30-day throughput, median Gate B-to-Gate E elapsed time,
  and deterministic evidence-linked acceptance history.
- Made delivery metrics fail closed around missing, malformed, contradictory,
  fallback, future, duplicate, and escaped evidence while preserving valid
  totals and accessible desktop/mobile presentation.
- Published the Portfolio Auto demonstration through the release-facing Pages
  artifact and synchronized canonical, adaptive, and public Agent Skill
  distributions.

Compatibility: AIM runtime contract remains `2.0` and runtime-state schema
remains `1.0`. The installer manifest advances from `0.9` to `1.0` for the
Portfolio-run helper and bounded chat-owned checkpoint writes. Public skill
package format advances from `6` to `7` because the package gains the Portfolio
run helper and schema. Existing canonical Epic workspaces require no migration.

Migration: update the public Agent Skill with
`npx skills update agile-iteration-method --yes`. Adaptive installations can
rerun the reviewed preview/apply installer flow. Before starting a new
Portfolio mandate where `.aim/portfolio-run.json` is already terminal, use the
trusted helper's explicit `archive` command with the observed `updatedAt`.

Known limitations: Portfolio Auto remains sequential and chat-owned; it does
not authorize later Backlog additions, unsafe or external effects, browser
writes, or silent scope expansion. AIM DATA reads local contained evidence and
does not provide product telemetry, remote analytics, cross-repository
aggregation, or pre-release-versus-production baseline comparison.

## 2026-08-22 - AIM 2 patch release v2.6.1
- Added `/aim to-backlog` as a first-class cross-adapter planning command for
  turning pasted Epic descriptions or one explicitly named source into
  not-yet-activated AIM UI Backlog cards.
- Added bare, inline, and `from <source>` command forms with a newcomer-first
  chat flow that reports the import result and starts or reopens AIM UI.
- Added a package-owned backlog helper with deterministic `EPIC-*` and `INC-*`
  identities, bounded validation, idempotent related updates, conflict
  detection, repository containment, symlink defenses, and atomic writes to
  `.aim/portfolio-backlog.json` only.
- Preserved AIM authority boundaries: source content remains untrusted evidence,
  imported cards remain planned and inactive, and the command cannot create
  runtime state, pass Gates, change roles, or start agents.
- Shipped the command and helper through Codex, Claude Code, GitHub Copilot, the
  adaptive installer, and the generated public Agent Skill, with focused UI,
  installer, adapter, package, safety, and full-repository validation.

Compatibility: AIM runtime contract remains `2.0`, runtime-state schema remains
`1.0`, and installer manifest remains `0.9`. Public skill package format
advances from `5` to `6` because the package gains the executable backlog
helper. Existing runtime and portfolio-backlog files require no migration.

Migration: update the public Agent Skill with
`npx skills update agile-iteration-method --yes`. Adaptive installations can
rerun the reviewed preview/apply installer flow to receive the command helper
and updated adapter surfaces.

Known limitations: `/aim to-backlog` reads only pasted input, one explicitly
named repository-contained file, or an attachment already available to the
active platform. It does not recursively discover roadmaps or fetch arbitrary
URLs. AIM UI remains read-only; activation and Gate decisions stay in chat.

## 2026-08-22 - AIM 2 minor release v2.6.0
- Made AIM UI a first-class, chat-controlled AIM surface. Bare `/aim ui`
  starts or reopens the current repository, while `start`, `open`, `status`,
  and `stop` provide explicit lifecycle control for any local repository.
- Added truthful onboarding for repositories that do not yet contain `.aim`.
  The UI can open immediately without creating runtime state and points the
  user back to `/aim calibrate-repo` in the authoritative chat.
- Added a repo-aware local launcher with loopback-only binding, per-repository
  instance identity, free-port allocation, concurrent-start serialization,
  stale-metadata protection, verified stop behavior, and bounded quiet logs.
- Promoted `/aim ui` through the canonical command contract and Codex, Claude
  Code, and GitHub Copilot adapters, including supplier-native slash-command
  entry points where supported.
- Advanced the public Agent Skill to package format `5` and bundled the
  executable AIM UI server, launcher, and web assets so public-skill users get
  the same chat-driven UI capability as adaptive installations.
- Expanded launcher, installer, adapter, publication, and browser-level
  validation, and rewrote the empty state around a clear chat-first next step.

Compatibility: AIM runtime contract remains `2.0`, runtime-state schema remains
`1.0`, and installer manifest remains `0.9`. Public skill package format
advances from `4` to `5`. No runtime-state or profile migration is required.

Migration: update the public Agent Skill with
`npx skills update agile-iteration-method --yes`. Adaptive installations can
rerun the reviewed preview/apply installer flow to receive the launcher and
updated adapters.

Known limitations: AIM UI remains a local loopback Beta rather than a hosted
service. Literal slash-command routing depends on the supplier; the portable
skill and plain-language AIM intent remain the fallback. The UI projects AIM
state and routes decisions to chat—it does not become a second state writer.

## 2026-08-22 - AIM 2 minor release v2.5.0
- Introduced AIM UI Beta as a multi-Epic control room where independently
  authoritative AIM workspaces share one delivery-first Kanban without giving
  the browser ownership of gates or runtime state.
- Added a portfolio backlog for planned Increments across Epics, chat-owned
  focus and concurrent-capacity controls, the three newest accepted Increments
  in Done, and complete history in Closed Increments.
- Added bounded card actions for Activate, Approve, and Change. Each action
  opens a user-owned Codex intent with an exact authority path, identity,
  decision point, timestamp, freshness checks, and replay protection.
- Separated workflow position from decision readiness: cards move when the
  authoritative process enters the right state, while Approve and Change only
  appear after AIM has published the completed decision handoff.
- Made polling visually quiet by preserving stable card nodes and animating
  only genuine column changes with brief transform-only motion, including a
  reduced-motion path.
- Recentered the interface on Delivery flow and moved portfolio summaries,
  People and agents, and Closed Increments into dedicated tabs.
- Added malformed-input limits, path containment, partial-workspace warnings,
  backward-compatible single-Epic discovery, and deterministic resolution of
  workspace-local authority.
- Headlined AIM UI Beta on the public website with dedicated release artwork,
  refreshed AIM 2.5 brand images, social metadata, product guidance, and
  publication checks.

Compatibility: AIM runtime contract remains `2.0`, runtime-state schema remains
`1.0`, public skill package format remains `4`, and installer manifest remains
`0.9`. Existing single-Epic state remains readable. Older state without an
explicit UI decision-readiness marker retains its safe legacy mapping.

Migration: no runtime-state or profile migration is required. Rerun the
adaptive installer through its reviewed preview/apply path to refresh AIM UI in
an existing installation, or update the public Agent Skill for the latest AIM
workflow guidance.

Known limitations: AIM UI is Beta and remains a local loopback control room. It
does not provide hosted accounts, remote portfolio aggregation, autonomous
agent orchestration, or writable gate control. Multi-Epic presentation combines
independently authoritative workspaces; it does not permit concurrent writers
to one shared runtime-state file.

## 2026-08-21 - AIM 2 minor release v2.4.0
- Added AIM UI v1, a dependency-free browser control room that projects the
  active local Epic and related Done Increments into a live five-column Kanban.
- Made Epic provenance structural: the active Epic is the visual board rail and
  every increment card carries its Epic identity in a multi-Epic-shaped read
  model while v1 execution remains single-Epic.
- Separated canonical PO, TDO, Dev, and Reviewer ownership from optional bounded
  helper-agent activity, with explicit unavailable states instead of inferred
  supplier telemetry.
- Added deterministic state-to-column movement, automatic polling, evidence
  links, attention states, malformed-input handling, responsive behavior,
  keyboard focus, contrast, and reduced-motion support.
- Kept the UI read-only through loopback defaults, GET/HEAD-only HTTP behavior,
  `.aim`-restricted evidence resolution, path-traversal protection, restrictive
  browser policy, and byte-preservation regression tests.
- Added collision-safe AIM UI packaging to every adaptive installer footprint:
  repo-writing footprints receive `scripts/aim_ui.py` and `aim-ui/`, while
  zero-repo-write footprints receive the same payload under the user's external
  AIM installation.
- Advanced the adaptive installer manifest from 0.8 to 0.9 for the new payload
  boundary, with idempotence, collision, scope, and installation coverage.
- Refreshed public product guidance, website presentation, and AIM 2.4 release
  artwork while keeping portable Agent Skill installation non-executable.

Compatibility: AIM runtime contract remains `2.0`, runtime-state schema remains
`1.0`, public skill package format remains `4`, and existing profile schemas,
roles, gates, state ownership, and `.aim` artifacts remain compatible. Installer
manifest version advances to `0.9`.

Migration: no runtime-state or profile migration is required. Rerun the adaptive
installer through its reviewed preview/apply path to add AIM UI to an existing
installation. Public Agent Skill-only users continue to receive the complete AIM
workflow and may select the adaptive path separately when they want UI files.

Known limitations: v1 reads one local repository and one active Epic. It does not
provide writable workflow controls, remote aggregation, user accounts, multi-Epic
execution, AIM DATA analytics, or a portable supplier-native agent telemetry API.

## 2026-08-21 - AIM 2 patch release v2.3.2
- Added a public Draft 2020-12 schema for canonical `.aim/state.json`, with
  independently versioned `stateSchemaVersion: 1.0`, documented extension
  fields, and publication through Pages and the portable Agent Skill.
- Added dependency-free, read-only legacy-state normalization and explicit
  current, legacy-compatible, blocked, unsupported, and contradictory
  classifications without automatic state rewriting.
- Made new Epics choose cost depth afresh instead of inheriting a completed
  Epic's `Deep` profile, while incomplete Epics retain their persisted profile.
- Allowed Gate B to de-escalate as well as escalate cost depth when rationale,
  visible decision, and persisted state agree.
- Defined Cost Control's trace and validation budget and separated AIM cost
  depth from supplier model or reasoning-effort selection.
- Enforced runtime schema, Gate B state/decision alignment, missing-schema
  handling, adapter parity, public package inventory, and publication behavior
  with expanded regression and product-coherence tests.
- Raised the public Agent Skill package format to 4 for the added runtime-state
  schema and kept generation deterministic across its 20-file package.
- Included the post-v2.3.1 mainline additions for Google site verification,
  refreshed public-skill provenance, and reference-quality Done Increment
  decomposition guidance in the v2.3.2 source tag.

Compatibility: AIM runtime contract remains `2.0`; installer manifest remains
`0.8`; repo-profile, Personal-hints, and project-role schemas remain unchanged.
The new runtime-state schema is version `1.0`, and public skill package format
advances from `3` to `4` because the package inventory gains one schema file.

Migration: existing active state without `stateSchemaVersion` remains readable
through a read-only normalized view. AIM does not rewrite active or historical
state during validation, install, or upgrade. Add the version only through an
explicit main-thread migration or when initializing new canonical state.

Known limitations: cost selection and legacy normalization remain part of the
instruction-led AIM runtime rather than a new deterministic execution engine.
Project-specific state extensions are allowed, but cannot replace canonical
fields or take ownership of gates and acceptance.

## 2026-08-02 - AIM 2 patch release v2.3.1
- Made completed Reflect analysis operator-ready: every run now states whether
  action is recommended and presents one concrete next step or an explicit
  no-action conclusion.
- Added `promote`, `correct`, `remove`, `defer`, and `no-action` dispositions so
  operators can distinguish durable candidates from duplicates, unsupported
  observations, stale rules, and work that needs more evidence.
- Required copy-ready `remember-repo` or `forget-repo` AIM intents when they can
  be represented safely, with reviewed profile, documentation, or Epic paths
  as the fallback for more complex changes.
- Added command quoting and escaping rules so untrusted repository evidence
  cannot introduce shell, tool, or secondary AIM actions.
- Required Reflect to say directly when no promotion or removal is warranted,
  eliminating the clarification turn previously needed to discover what to do
  with a report.
- Preserved approval-controlled promotion: Reflect and Reflect-all still write
  temporary reports only and stop before every durable change.
- Propagated the completion contract through portable, Codex, Claude Code, and
  GitHub Copilot routes, public product guidance, validator enforcement,
  regression coverage, and the generated public Agent Skill.

Compatibility: AIM runtime contract `2.0`, installer manifest `0.8`, public
skill package format `3`, profile schemas, roles, gates, discovery boundaries,
and existing AIM 2.3 commands remain compatible.

Migration: no runtime-state, profile, schema, installer, or command migration is
required. Refresh installed Agent Skills through the standard skills CLI to
receive the operator-ready Reflect completion behavior.

Known limitations: Reflect remains a model-operated workflow rather than a
standalone report renderer. Proposed commands depend on verified candidate
quality and remain user-owned; AIM does not execute them during reflection.

## 2026-07-30 - AIM 2 minor release v2.3.0
- Added `/aim reflect` for evidence-backed knowledge synthesis in the current
  AIM project.
- Added `/aim reflect-all` for safe inventory and synthesis across selected
  local AIM projects.
- Added provenance, current-source verification, confidence, contradiction,
  classification, destination, and promotion-action requirements for every
  reflection candidate.
- Kept reflection read-only: reports live temporarily under `.aim/analysis/`,
  durable knowledge changes remain separately reviewed, and discovered
  repositories are never modified.
- Added explicit discovery-root, preview, exclusion, symlink, duplicate-clone,
  secret, workload, and trust boundaries for multi-project reflection.
- Added the canonical Reflect workflow, complete adapter parity, generated
  public-skill packaging, public product documentation, and GitHub Pages
  presentation.
- Made the existing audience-context integrity principle prominent at the
  README, feature-guide, and GitHub Pages front doors.
- Updated the dark hero, light logo, and Open Graph social artwork to display
  AIM 2.3.
- Positioned AIM Reflect as going beyond memory cleanup for repository work:
  it adds current-code verification, cross-project synthesis, provenance, and
  approval-controlled promotion to the useful shadow-output pattern popularized
  by agent-memory systems such as Anthropic Dreams.

Compatibility: AIM runtime contract `2.0`, installer manifest `0.8`, public
skill package format `3`, profile schemas, roles, gates, and existing AIM 2.2
commands remain compatible.

Migration: no runtime-state or profile migration is required. Refresh installed
Agent Skills through the standard skills CLI to receive the Reflect commands and
canonical reflection contract.

Known limitations: Reflect is an agent workflow rather than a background daemon.
Cross-project quality depends on the selected repositories and available AIM
history. Reflection proposes knowledge; it never guarantees that a candidate is
correct or promotes it automatically.

## 2026-07-29 - AIM 2 patch release v2.2.3
- Added an explicit trust boundary that treats repository profiles, hints,
  source files, command output, and documentation as untrusted evidence rather
  than AIM instructions.
- Preserved repository awareness while preventing embedded directives from
  changing roles, gates, state, scope, acceptance, precedence, or tool policy.
- Applied the boundary before repository ingestion across the portable, Codex,
  GitHub Copilot, and Claude Code entry routes.
- Added cross-adapter ordering and generated-package regression checks for the
  Snyk W011 mitigation.
- Updated `/aim status` to report the current AIM product release separately
  from the stable runtime contract version.

Compatibility: AIM runtime contract `2.0`, installer manifest `0.7`, public
skill package format `3`, profile schemas, adapters, commands, roles, gates, and
all AIM 2.2.2 behavior remain compatible.

Migration: no runtime-state, profile, schema, or installer migration is
required. Refresh installed Agent Skills through the standard skills CLI to
receive the new trust boundary and status behavior.

Known limitations: the trust boundary governs how repository content is
interpreted; it does not sanitize or suppress that content, and material trust
conflicts still require corroboration or escalation. Local validation cannot
guarantee how a proprietary external scanner classifies the published package.

## 2026-07-21 - AIM 2 patch release v2.2.2
- Rebuilt the public Agent Skill front door around AIM's user value, delivery
  loop, and a concrete first journey before adapter and runtime details.
- Added a complete command guide that explains when to use every AIM command,
  what it does, and what happens next.
- Clarified the default Strict experience and how Auto preserves the same gates,
  ownership, escalation, and final human acceptance.
- Added regression checks for newcomer-first ordering, English-only public copy,
  complete command-table rows, and retained security boundaries.

## 2026-07-16 - AIM 2 patch release v2.2.1
- Replaced the Codex-specific public Agent Skill launcher with a portable front
  door for Codex, GitHub Copilot, and Claude Code.
- Improved the skills.sh opening with AIM's user outcome before package details.
- Removed misleading canonical-reference aliases and made omitted source-only
  documents explicit.
- Added a safe data-only installer-manifest contract and truthful package
  inventory and provenance.
- Added portability, closure, YAML, provenance-hash, and security regression
  checks; public package format is now version 3.

## 2026-07-13 - AIM 2 release v2.2.0
- Retired the remote pipe-to-shell bootstrap after ecosystem security audits
  identified unnecessary remote-code-execution risk; adaptive setup now starts
  from a locally reviewable source checkout and the legacy bootstrap fails
  closed.
- Removed target-repository script execution and external source dependencies
  from the portable public skill, with generated-package security regression
  checks.
- Replaced newcomer-facing Personal, Team, and Enterprise editions with one adaptive installation while retaining old flags as migration compatibility inputs.
- Added `aim.roles.yaml` and supplier-native PO, TDO, Dev, and Reviewer project specialists for Codex, Claude Code, and GitHub Copilot.
- Added `/aim configure-agents` so users can preview and refresh stack-aware role configuration as a project evolves.
- Extended installer detection, schemas, validation, clean-room packaging, and tests for native project-agent configuration, including React and Playwright specialization.
- Added supplier-native AIM skills for the complete `/aim` command family in
  Codex, Claude Code, and GitHub Copilot, with readiness receipts and safe fallback.
- Moved the Codex user skill to the current `$HOME/.agents/skills` discovery
  path while preserving `.codex/agents` for project specialists.
- Added product-versioned release manifests, documentation quality checks, a
  concise feature guide, and a refreshed v2.2.0 website.
- Added the generated, self-contained `agile-iteration-method` public Agent
  Skill for official skills CLI installation across Codex, GitHub Copilot, and
  Claude Code without creating an AIM Lite fork.
- Added deterministic public-skill generation, canonical-source provenance,
  semantic parity tests, isolated official-CLI installation validation, and
  release-gate drift protection.

## 2026-06-11 - AIM 2 release v2.1.0
- Added the Enterprise `external` footprint so protected repositories can install the full AIM distribution and selected home-scope adapter packages outside the target repository with zero repo writes by default.
- Added Enterprise external repo-awareness memory at `~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml`, with larger external memory documents under `~/.aim/repo-awareness/<repo-fingerprint>/docs/`.
- Updated Codex, Claude, and GitHub Copilot adapter guidance so `/aim calibrate-repo` and `/aim remember-repo` write to the correct durable store for the active operating mode instead of defaulting to repo files.
- Added public one-command installation from GitHub Pages, guided target-repository prompting, maintained-branch bootstrap behavior, and release asset validation.
- Added first-run onboarding guidance, `/aim upgrade` guidance, `/aim remember-repo` examples, and validation that keeps advanced command inventories behind help.
- Improved the GitHub Pages launch page with an image-only hero, install command copy button, and copy-success feedback.
- Hardened AIM 2 validation for Strict-mode gate approval wording, durable `.aim/` runtime boundaries, Enterprise zero-repo-write defaults, external footprint schema support, and release readiness.

## 2026-06-08 - AIM 2.0 public launch bootstrap
- Added the original public one-command Pages bootstrap at `install.sh` (retired
  in v2.2.0 after security review).
- Made the bootstrap maintainable by default: it follows the current `main` archive while still allowing `AIM_REF` overrides for a specific branch or tag.
- Changed the bootstrap so it no longer injects the current shell directory as the install target; the guided installer asks for the target repository unless `--target` is passed explicitly.
- Updated the Pages launch experience, README, first-time journey, and install guide so new users can install AIM without cloning the source repository.
- Added a tag-driven GitHub Release workflow that depends on the reusable release-readiness gate and publishes versioned Pages, install, and manifest assets.
- Extended publication validation and tests so release readiness checks the public install command, executable bootstrap, main-archive behavior, and versioned release assets.

## 2026-06-07 - AIM 2.0 release
- Cut the official **AIM 2.0** release, promoting the rebuilt method, runtime, repo-awareness, and adapter model to the current public line (previous release: AIM 1.7).
- Shipped a validated public launch: GitHub Pages and release artifacts now pass a reusable release gate (`.github/workflows/release-readiness.yml`) covering compilation, tests, AIM validator health, schema/public-ID correctness, package integrity, and deterministic artifact assembly.
- Published the canonical JSON Schemas at stable URLs and documented the AIM 2.0 release and publication model in `docs/workflow/release-publication-model.md`.
- Consolidated the AIM 2.0 story across `README.md`, `docs/product/`, and the GitHub Pages site, with license metadata included in public and full-footprint distributions.
- Established `v2.0` as the source tag family for the released, gate-passing commit.

## 2026-06-06 - AIM 2.0 public product and onboarding story
- Rebuilt `README.md` as a concise public front door with the AIM 2.0 product story and website artwork.
- Added `docs/product/` for newcomer-focused explanation, first-time onboarding, platform support, and adoption modes.
- Created a six-step path from guided installation through repository calibration to the first AIM Epic.
- Separated public product narrative from canonical workflow, support/reference, and maintainer documentation.
- Added validator checks for the required public documentation journey.

## 2026-06-06 - AIM 2.0 guided-first installer
- Added target path Tab completion, arrow-key mode selection, and adapter multi-select.
- Made Personal the guided mode default and connected preview to reviewed apply in one session.
- Added explicit `--dry-run` preview-only behavior while preserving non-interactive defaults.
- Added an interactive target prompt when required input is missing in a terminal.
- Replaced the default raw action dump with a compact plan summary and optional terminal color.
- Added `y` overwrite, `n` keep, `a` overwrite-all-remaining, and `q` quit decisions for apply collisions.
- Extended guided prompting to missing target, mode, and adapter inputs while preserving flag and non-interactive defaults.
- Added a final default-no apply confirmation after guided collision decisions.
- Clarified that prompts are concise and sequential, not sticky terminal UI.
- Preserved detailed `--verbose`/`--raw`, JSON, plan-file, force, and non-interactive workflows.
- Added focused installer tests for prompting, rendering, collision safety, and automation behavior.

## 2026-06-06 - AIM 2.0 two-layer repo-awareness
- Split persistent repo-awareness into a compressed `aim.profile.yaml` layer and load-on-demand AIM-owned operational docs.
- Added structured operational-doc pointers with work, role/gate, risk, command, and calibration triggers.
- Extended validation for pointer completeness, operational-doc structure, missing targets, and prose-heavy profile values.

## 2026-06-06 - AIM 2.0 repo-awareness calibration
- Added the canonical cheap-first `/aim calibrate-repo` flow and equivalent AIM Epic path.
- Added structured shared repository knowledge, readiness, confidence, evidence, document-loading, remember, and forget behavior.
- Moved persistent Personal hints to `~/.aim/repo-awareness/<repo-fingerprint>/hints.yaml` and prohibited stable repo-awareness under `.aim/`.
- Added native Codex, Copilot, and Claude calibration entrypoints plus installer bootstrap readiness.
- Extended validation with schema categories, stable IDs, loading states, runtime separation, adapter parity, and a human-visible calibration summary.

## 2026-06-06 - AIM 2.0 root-file independence
- Removed AIM-owned `AGENTS.md` and `CLAUDE.md` from the product surface.
- Made `aim.profile.yaml` the primary shared repo-awareness source and added the canonical progressive-loading model.
- Kept Codex, Copilot, and Claude entrypoints native through optional adapter-owned packages.
- Updated validation so canonical AIM docs are required while generic root instruction files are rejected from the AIM product surface.
- Added `install/aim-install-manifest.yaml`, which forbids copying, creating, modifying, requiring, or reading `CONTRIBUTING.md` in target repositories.

## 2026-06-03 - AIM 1.7 GitHub Pages website update
- Updated the GitHub Pages website on `gh-pages` from AIM v1.6.1 to AIM v1.7 messaging.
- Added the AIM 1.7 cost-discipline story, GitHub Copilot AI Credits angle, and Cost Comparison link to the site.
- Corrected stale website copy about Claude Code helper files.

## 2026-06-03 - AIM 1.7 cost-comparison evidence
- Added a public cost-comparison feature doc explaining why AIM 1.7 should reduce waste versus AIM 1.6-style normal use and undisciplined vibe coding.
- Linked the comparison from the README, 1.7 quick start, document map, and cost-saving method doc.
- Kept the comparison qualitative and behavior-based instead of inventing exact savings percentages or token counts.

## 2026-06-03 - AIM 1.7 release-surface hardening
- Aligned active README, contribution, Copilot role, and prompt-helper surfaces so they present AIM 1.7 as the current release.
- Corrected Claude Code packaging claims so the repo no longer says `.claude/` helper files are shipped when only `CLAUDE.md` is present.
- Preserved the stable AIM 1.6 runtime-family docs as intentional deeper guidance under the 1.7 front door.

## 2026-06-03 - AIM 1.7 cost-saving front door
- Promoted the public release line to AIM 1.7 while keeping the accepted AIM runtime contract stable.
- Repositioned AIM unapologetically as the cost-saving method for GitHub Copilot, Codex, Claude Code, and similar coding-agent platforms.
- Added a dedicated cost-saving method doc and new 1.7 front-door docs for install, quick start, release framing, and document routing.
- Made GitHub Copilot AI Credits after the June 1, 2026 billing change a first-class part of the operator story.

## 2026-05-11 - AIM 1.6.1 Codex bundled skill onboarding
- Added first-run Codex guidance so AIM 1.6 commands surface the repo-bundled skill path and local Codex install target.
- Updated the bundled Codex skill to explain how to install or refresh the full local package at `~/.codex/skills/agile-iteration-method/` from `adapters/codex/agile-iteration-method/`.
- Added Codex picker metadata at `adapters/codex/agile-iteration-method/agents/openai.yaml` so the app card presents AIM 1.6.1 instead of stale older labels.
- Documented the stale picker case where `SKILL.md` is current but `agents/openai.yaml` still shows an older AIM version.
- Added `docs/workflow/codex-skill-onboarding.md` as the canonical workflow contract for Codex skill onboarding behavior.
- Removed stale packaged-skill references to missing helper scripts and reference docs so the repo-bundled skill is usable as a single copied skill file.

## 2026-04-15 - AIM 1.6 cost control and budget-aware runtime depth
- Added explicit cost profiles: `Standard`, `Cost Control`, and `Deep`.
- Clarified that cost profile controls runtime depth while `Strict` and `Auto` still control approval flow.
- Documented Cost Control as full AIM with narrower context, compact checkpoints, no subagents by default, and escalation to Standard or Deep when risk appears.
- Added `docs/workflow/light-front-door.md` and updated onboarding so first-run users choose start, continue, or validate before reading deeper docs.
- Updated README, AGENTS, workflow docs, feature docs, prompt helpers, Copilot metadata, and Claude bridge files to present AIM 1.6.

## 2026-04-14 - AIM 1.5 repository surface cleanup
- Removed old pre-1.5 workflow docs, release notes, migration guides, and prompt helpers from the active repository surface.
- Kept the current AIM 1.5 docs and the then-relevant AIM 1.4 to 1.5 upgrade bridge.
- Updated Copilot, Claude Code, adapter, and contribution docs so they no longer advertise removed legacy files.
- Removed stale AIM 1.2 Epic and feature-contract artifacts.
- Removed macOS `.DS_Store` files from the working tree.

## 2026-04-13 - AIM 1.5 release framing, modularity, and onboarding alignment
- Promoted the latest documentation work to AIM 1.5.
- Made the main 1.5 feature explicit in the public docs: small Done Increments are defined by behavioral scope, not by keeping file count artificially low.
- Added the current AIM 1.5 public doc family for install, quick start, doc map, troubleshoot, usage guides, interaction examples, reference run, release notes, and 1.4 to 1.5 migration.
- Updated `README.md`, `AGENTS.md`, `docs/workflow/agile-iteration-method.md`, packaged prompt helpers, and packaged agent metadata to present AIM 1.5 as the current release.
- Added the AIM 1.4 to AIM 1.5 upgrade path.
