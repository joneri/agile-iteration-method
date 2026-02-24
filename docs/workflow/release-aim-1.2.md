> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM 1.2 release notes

## Release summary

AIM 1.2 keeps the core loop stable and formalizes repository-aware execution.

Main outcomes:
- repository profile is first-class in `AGENTS.md`
- explicit layer order for Codex/Copilot parity
- explicit execution modes (`Strict`, `Auto`) with guardrails
- canonical role naming locked to `PO`, `TDO`, `Dev`, `Reviewer`

## Why teams will care immediately

- You get speed without chaos:
  natural-language kickoff, command kickoff, and Copilot button flow all align to the same method behavior.
- You get consistency across tools:
  Codex and Copilot now run from the same repo-defined rules and role semantics.
- You get safer autonomy:
  `Auto` mode increases throughput, but AIM still enforces role flow, gate logic, traceability, and final full review.
- You get less onboarding friction:
  migration paths are explicit and copy-paste ready for both 1.0 and 1.1 repositories.

## Promoted features

### 1) Repository-aware execution model
- `AGENTS.md`
- `docs/workflow/agile-iteration-method.md`
- `.github/agents/aim.agent.md`

### 2) Execution modes with visible state
- `Strict` (default)
- `Auto` (Epic flag: `Auto-approve until Epic complete`)
- final full review required before Epic completion in `Auto`

### 3) Canonical role naming and alias mapping
- Canonical: `PO`, `TDO`, `Dev`, `Reviewer`
- Non-canonical aliases must map explicitly:
  - `Planner` -> `TDO`
  - `Builder` -> `Dev`

### 4) Migration path for existing AIM repos
- `/migrate-aim-1.0-to-1.1`
- `/migrate-aim-1.1-to-1.2`
- `docs/workflow/migrate-aim-1.0-to-1.1.md`
- `docs/workflow/migrate-aim-1.1-to-1.2.md`

## Contributor acknowledgment

AIM 1.2 includes contributor input from:
- [@liamwears](https://github.com/liamwears)

See:
- `CONTRIBUTORS.md`

## Suggested publish text (short)

AIM 1.2 is out.

What is new:
- repository profile + explicit load order for repo-aware behavior
- mode model (`Strict`/`Auto`) with visible execution context
- canonical role naming across docs, prompts, and agents
- migration path from AIM 1.1 to AIM 1.2

## Suggested publish text (promoted)

AIM 1.2 is the most complete operational version of AIM so far.

Why this release stands out:
- one repository-driven behavior model across Codex and Copilot
- canonical roles locked (`PO`, `TDO`, `Dev`, `Reviewer`) to eliminate role-name drift
- execution modes built for real-world tradeoffs:
  `Strict` for controlled delivery, `Auto` for high-velocity Epic execution with full trace and final review
- copy-paste migration paths for both legacy tracks (`1.0 -> 1.1`, `1.1 -> 1.2`)

If your team wants fast AI delivery with clear ownership and stable method semantics, AIM 1.2 is the release to adopt.

## Suggested publish checklist

1. Confirm `README.md` and `CHANGELOG.md` are updated.
2. Confirm `AGENTS.md` reflects AIM 1.2 semantics.
3. Confirm `.github/agents/` and `.github/prompts/` are present.
4. Confirm migration docs for both 1.0 -> 1.1 and 1.1 -> 1.2 are present.
5. Tag release as `v1.2.0`.
