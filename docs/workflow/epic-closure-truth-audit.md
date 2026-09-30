> License: CC BY 4.0 (documentation).
> Author: Jonas Eriksson.

# AIM Epic closure truth audit

## Purpose

Prevent an accepted Increment, successful POC, green internal checks, or user
approval from being misreported as a completed Product Epic.

Gate E accepts one Increment. Epic closure is a different transition and must
be supported by a contained JSON truth audit. AIM should create more coherent
Done Increments whenever the Epic outcome is not fully proven.

## Outcome classes

Every new Epic declares exactly one field in `epic.md`:

```text
Outcome class: Product
```

Allowed values are `Product`, `Pilot`, and `POC`.

Every acceptance criterion must also have a stable identity. A numbered list is
normalized to `AC-1`, `AC-2`, and so on; explicit `AC-*` labels are also
supported. Closure requires an exact set match, so omitting a criterion or
inventing a closure-only criterion fails closed.

- `POC` proves only its explicitly bounded technical or product hypothesis.
  Synthetic issues, fixtures, mocks, and assisted walkthroughs may be valid.
- `Pilot` proves the bounded pilot outcome in its representative operating
  context and requires representative user-journey verification.
- `Product` proves the declared user outcome in its representative operating
  context and requires representative user-journey verification.

Closure evidence must match the class approved at Gate A. A successful POC may
lead to another Increment or a new Product Epic, but it may not silently upgrade
its own claim.

## Required JSON artifact

Write the artifact inside the authoritative workspace's `decisions/` directory
and bind its repository-relative path as `epicClosureEvidence` in state only
through `scripts/aim_runtime_contract.py close` or the combined
`scripts/aim_decisions.py apply` commit. The transition also records
`epicClosureEvidenceSha256`, so later modification invalidates closure. Each
referenced evidence item is an object containing `path`, `sha256`, and `kind`.
The transition also records `epicClosureEvidenceSetSha256`, a deterministic
aggregate over every referenced path, kind, size, and byte digest. References
must name non-empty regular files contained in the same Epic workspace;
traversal, symlinks, oversized files, and digest mismatch fail closed. External
URLs or observations belong inside those evidence files rather than acting as
unverified references themselves.

Apply must provide the previewed source-state SHA-256, closure-artifact SHA-256,
and evidence-set SHA-256. A change to any bound byte after preview fails without
a runtime-state write. Apply revalidates immediately before its atomic write and
verifies the published state afterward.

```json
{
  "schemaVersion": "1.0",
  "epicId": "EPIC-EXAMPLE",
  "outcomeClass": "product",
  "recommendation": "close",
  "acceptanceCriteria": [
    {
      "id": "AC-1",
      "status": "proven",
      "evidenceClass": "representative",
      "evidence": [
        {
          "path": "evidence/black-box.json",
          "sha256": "<64 lowercase hex characters>",
          "kind": "black_box_result"
        }
      ]
    }
  ],
  "counterevidence": {
    "searched": true,
    "unresolvedFindings": [],
    "evidence": [
      {
        "path": "evidence/negative-test.md",
        "sha256": "<64 lowercase hex characters>",
        "kind": "negative_test"
      }
    ]
  },
  "blackBoxValidation": {
    "status": "passed",
    "representative": true,
    "operatorAssistance": false,
    "entryPoint": "documented public entry point",
    "scenario": "representative user journey",
    "expectedOutcome": "declared user-visible result",
    "actualOutcome": "observed user-visible result",
    "performedBy": "reviewer",
    "startedAt": "2026-08-30T19:55:00Z",
    "completedAt": "2026-08-30T20:00:00Z",
    "evidence": [
      {
        "path": "evidence/black-box.json",
        "sha256": "<64 lowercase hex characters>",
        "kind": "black_box_result"
      }
    ]
  },
  "remainingGaps": [],
  "contradictions": [],
  "decisionAuthority": "user",
  "authorityEvidence": [
    {
      "path": "decisions/epic-closure-authority.md",
      "sha256": "<64 lowercase hex characters>",
      "kind": "authority_decision"
    }
  ],
  "decidedAt": "2026-08-30T20:00:00Z"
}
```

Every criterion needs a stable identifier, `proven` status, and at least one
concrete evidence reference. Product and Pilot criteria require
`evidenceClass: representative`. The black-box evidence must exercise the
advertised user journey from the user's normal entry point. The implementing
agent may run it, including automated end-to-end tests against the real
product. These journey checks do not waive independent material-change review
under `adaptive-execution.md`. Unassisted operation is required only when the
user or project acceptance criteria require it. Knowledge of
the implementation and implementation-team assistance do not disqualify an
otherwise representative run; mocks or assertions that bypass the actual
journey do not substitute for it.

The existing `blackBoxValidation` and `black_box_result` names remain for
compatibility. The result file is machine-readable JSON repeating the audit
metadata. `performedBy` identifies the actual person, agent, or test runner
with a non-empty description (for example `Dev`, `reviewer`, or `Playwright
run by the implementing agent`). `operatorAssistance` records a boolean; both
`true` and `false` are permitted and must match between audit and result.
Do not describe self-verification as independent observation. Counterevidence
binds at least one concrete `negative_test` artifact.

Closure authority is a separate, contained `authority_decision` Markdown
record. It identifies the Epic, explicitly approves Epic closure, and matches
`decisionAuthority`. Portfolio authority also records its mandate provenance.
Gate E acceptance alone is not this decision. A clearly presented combined
proposal may record both logical decisions from the same actual user response;
see [combined decisions](streamlined-decisions.md). The read-only readiness
check omits authority validation, never quality checks or required evidence.

## Required negative search

Before `close`, actively test or inspect the most credible ways the product
claim could be false. Select checks from the Epic rather than mechanically
reusing this list:

- fresh start from the documented user entry point
- repeat and resume after interruption
- stale state, existing resources, and duplicate-effect behavior
- refusal and recovery paths
- external-system triggers and callbacks actually required by the claim
- separation between fixture/demo surfaces and live runtime data
- output/state agreement after partial external success

Record unresolved findings. Do not omit a known failure because the successful
path passed later.

## Disposition

- `close`: all criteria are proven, the evidence class matches, required
  black-box validation passed, and no unresolved gaps or contradictions remain.
- `continue`: any approved Epic criterion remains partial, synthetic-only,
  contradicted, or unproven, or relies on assistance when that criterion requires
  unassisted operation. TDO proposes the next coherent Done Increment.
- `split`: only genuinely new value outside the approved Epic moves elsewhere.
  Unmet existing criteria stay in the current Epic.

Decision authority and evidence are independent. A user or Portfolio mandate
may authorize a valid closure, but neither can make invalid evidence true.

## Mechanical limit and review duty

The contract can prove containment, byte identity, field completeness,
separation of authority, and whether a structured result claims the required
properties. It cannot independently know that a human or external system told
the truth. Reviewer work therefore remains essential: inspect the actual
entry point and result, attempt credible falsification, compare the evidence to
the Epic claim, and reject circular or unsupported claims and falsely labelled
independence. An implementer-authored real-journey result still needs critical
review; authorship alone does not invalidate it. The JSON
record makes that review inspectable and tamper-evident; it does not replace it.

Historical `epic_complete` states without these three closure bindings remain
readable as preserved history, but AIM UI labels them `legacy_unverified` and
Portfolio completion does not treat them as verified current Product truth.
Partially bound or tampered modern closure is contradictory.
