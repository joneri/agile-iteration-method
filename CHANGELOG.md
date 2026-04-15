# Changelog

## 2026-04-15 - AIM 1.6 cost control and budget-aware runtime depth
- Added explicit cost profiles: `Standard`, `Cost Control`, and `Deep`.
- Clarified that cost profile controls runtime depth while `Strict` and `Auto` still control approval flow.
- Documented Cost Control as full AIM with narrower context, compact checkpoints, no subagents by default, and escalation to Standard or Deep when risk appears.
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
