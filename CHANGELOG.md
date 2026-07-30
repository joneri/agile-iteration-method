# Changelog

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
