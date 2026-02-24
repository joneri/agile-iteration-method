# Changelog

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
