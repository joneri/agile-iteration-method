# Changelog

## 2026-06-11 - AIM 2 release v2.1.0
- Added the Enterprise `external` footprint so protected repositories can install the full AIM distribution and selected home-scope adapter packages outside the target repository with zero repo writes by default.
- Added Enterprise external repo-awareness memory at `~/.aim/repo-awareness/<repo-fingerprint>/memory.yaml`, with larger external memory documents under `~/.aim/repo-awareness/<repo-fingerprint>/docs/`.
- Updated Codex, Claude, and GitHub Copilot adapter guidance so `/aim calibrate-repo` and `/aim remember-repo` write to the correct durable store for the active operating mode instead of defaulting to repo files.
- Added public one-command installation from GitHub Pages, guided target-repository prompting, maintained-branch bootstrap behavior, and release asset validation.
- Added first-run onboarding guidance, `/aim upgrade` guidance, `/aim remember-repo` examples, and validation that keeps advanced command inventories behind help.
- Improved the GitHub Pages launch page with an image-only hero, install command copy button, and copy-success feedback.
- Hardened AIM 2 validation for Strict-mode gate approval wording, durable `.aim/` runtime boundaries, Enterprise zero-repo-write defaults, external footprint schema support, and release readiness.

## 2026-06-08 - AIM 2.0 public launch bootstrap
- Added the public one-command install bootstrap at `install.sh`, published through GitHub Pages as `curl -fsSL https://joneri.github.io/agile-iteration-method/install.sh | bash`.
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
