# Changelog

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
