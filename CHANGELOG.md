# Changelog

## 2026-04-04 - AIM 1.4.2 adapter installation and layering clarification
- Clarified that `.github/agents/aim*.agent.md` are required AIM instruction-layer files rather than Copilot-only decoration.
- Clarified that `.github/prompts/` are optional Copilot prompt helpers rather than the canonical AIM contract.
- Updated `README.md`, `AGENTS.md`, and `docs/workflow/agile-iteration-method.md` to align installation guidance and instruction-layer precedence.
- Updated installation, quick-start, Copilot-layer, Claude bridge, and helper prompt docs to keep Codex, Copilot, and Claude Code explanations consistent.
- Kept Claude Code as a separate adapter layer that extends AIM without replacing `AGENTS.md`.

## 2026-04-03 - AIM 1.4.1 release alignment and packaging cleanup
- Renamed the active workflow doc family from `1.3` to `1.4`, including quick start, install, troubleshoot, doc map, migration, usage guides, interaction examples, and the reference run.
- Renamed the active feature-contract doc family from `aim-1.3-*` to `aim-1.4-*`.
- Updated `AGENTS.md` and `docs/workflow/agile-iteration-method.md` so AIM 1.4 is the active operational framing while keeping explicit lineage notes for AIM 1.2 core semantics and the accepted AIM 1.3 runtime model.
- Updated Copilot agent and prompt packaging to present AIM 1.4 as the current packaged surface.
- Moved the packaged upgrade path from `1.2-to-1.3` to `1.2-to-1.4`.
- Kept Claude Code support as a first-class adapter layer with `AGENTS.md` still canonical.

## 2026-04-02 - AIM 1.4 Claude Code adapter release
- Promoted Claude Code to a first-class AIM platform adapter in the public docs.
- Added the Claude bridge contract in `CLAUDE.md`.
- Updated `README.md` to present AIM 1.4 as the current release and to sell AIM as a Codex/Copilot/Claude Code operating model.
- Added AIM 1.4 release notes:
  `docs/workflow/release-aim-1.4.md`.
- Updated the AIM 1.3 document map to include the new release note.

## 2026-03-28 - AIM 1.3 runtime and operator model
- Added AIM 1.3 Epic: `docs/epics/aim-1.3-unified-runtime.md`.
- Added AIM 1.3 runtime architecture split across core, runtime, repo-aware policy, and platform adapters.
- Added official `.aim` workspace contract and `state.json` checkpoint model.
- Added shared bootstrap and resume model for Codex and Copilot.
- Added canonical AIM 1.3 state transition model.
- Added normalized repo-aware runtime context contract.
- Added validator support contract and quick-check result classes.
- Added AIM 1.2 -> 1.3 migration guide and migration support contract.
- Added explicit Codex/Copilot adapter contract and parity matrix.
- Updated `README.md` to present AIM 1.3 as the current operator-facing model.
- Added AIM 1.3 operator docs:
  `docs/workflow/release-aim-1.3.md` and
  `docs/workflow/troubleshoot-aim-1.3.md`.

## 2026-02-24 - AIM 1.2 foundation
- Added AIM 1.2 Epic: `docs/epics/aim-1.2-repo-aware-execution.md`.
- Added repository-profile and load-order rules to `AGENTS.md`.
- Added execution mode model (`Strict`, `Auto`) with explicit Epic flag:
  `Auto-approve until Epic complete`.
- Added mode visibility and final full-review requirement for Auto mode.
- Locked canonical role names to `PO`, `TDO`, `Dev`, `Reviewer` and documented alias mapping.
- Added Swedish short trigger support:
  `Starta en AIM-loop med denna EPIC: ...`.
- Updated workflow and Copilot-layer docs for Codex/Copilot parity and repository-aware loading.
- Added migration assets for AIM 1.1 -> 1.2:
  `.github/prompts/migrate-aim-1.1-to-1.2.prompt.md` and
  `docs/workflow/migrate-aim-1.1-to-1.2.md`.
- Added AIM 1.2 release draft:
  `docs/workflow/release-aim-1.2.md`.
- Updated planner/builder/reviewer subagent docs to include canonical-role and mode-context guidance.
- Added AIM 1.2 feature contract and Epic closure evidence:
  `docs/features/aim-1.2-repo-aware-execution.md` and
  `docs/epics/aim-1.2-repo-aware-execution.md`.

## 2026-02-23 - AIM 1.1
- Added optional Copilot layer documentation: `docs/workflow/copilot-layer.md`.
- Added Copilot custom-agent templates in `.github/agents/`.
- Added Copilot prompt templates in `.github/prompts/` for faster setup/start.
- Added Copilot handoff UI buttons in `aim` agent flow (`Approve`, `Request changes`, `Replan`, `Status`, `Continue`).
- Updated feature documentation path from `docs/features-explanations/` to `docs/features/`.
- Updated Epic documentation path from `docs/runbooks/` to `docs/epics/`.
- Clarified kickoff contract: PO creates Epic from desired outcome, TDO creates Done Increment from Epic.
- Added migration prompt: `.github/prompts/migrate-aim-1.0-to-1.1.prompt.md`.
- Added migration guide: `docs/workflow/migrate-aim-1.0-to-1.1.md`.
- Added publish draft: `docs/workflow/release-aim-1.1.md`.
- Updated AIM docs and templates to use `docs/features/`.
- Updated Copilot orchestrator flow to keep Gate A and Gate B explicit.
- Commit-after-increment changed from required to optional policy.
- Added contributor acknowledgment for `@liamwears` in `CONTRIBUTORS.md`.

## 2026-01-30 – Autopost v3 stabilisering
- Bankade drafts kan raderas utan fel i delete‑route.
- Autopost använder senaste trading‑day close för effectiveDate och close‑vs‑close‑beräkning.
- Daily snapshot‑grafen visar alltid dagens värde (senaste punkt) i callout.
- Förslag renderas även vid `partial` data (preview‑only), medan `invalid` fortsatt suppressar.

## 2026-01-26 – Buyplan 2.0
- Köpkapital stöder både likvida medel och simulerat belopp, tydligt markerat i flödet.
- Köpplanen är regelmedveten med auto‑regel som hanterar restbelopp utan att bryta hårda tak.
- Yield‑skydd använder samma yield som portföljen och flaggar endast när total yield sänks.
- Pris och buy‑beräkningar använder marknadskurs; snittpris visas enbart som kontext.
- Timing‑rekommendationer visas när data finns, med tydlig fallback när timing saknas.
- Köpplanen kan skapa köptransaktioner med ursprungstext och uppdatera portfölj/ledger.
- Quote‑transparens: varningar för gamla/saknade kurser, refresh‑knapp och per‑rad status.
