<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/engineering-delivery.md
-->

# Engineering delivery

This canonical contract defines product engineering evidence and role-skill
selection. It supplements existing acceptance authority; it adds no approval
gate and does not select a model or authorize delegation.

## Start with the hard part

Reuse binding requirements, valid quality goals, prior decisions, relevant skills
and durable project knowledge across sessions. Mature input normally shortens
preparation: resolve only consequential gaps or contradictions, without reducing
implementation or verification quality. A new increment alone warrants neither
new onboarding nor full recalibration. Read and apply relevant skill instructions;
listing skill names is not quality evidence.

Translate binding requirements into observable outcomes before implementation.
For a bounded product, keep one cohesive delivery unless an earlier independently
useful result would change a real decision. Do not turn a PRD into a sequence of
administrative Epics. Resolve a consequential uncertain technical assumption with a bounded
investigation or executable experiment before depending on it; reuse sufficient
existing evidence rather than adding an experiment by ritual.
An experiment is evidence inside the work, not a substitute for the product.

Use a compact evidence table in the existing increment or review artifact:

| Requirement | Independent check | Result and artifact | Limitation |
| --- | --- | --- | --- |
| Binding requirement identifier | Input, oracle and expected behavior | Passed, failed or unverified; command and evidence | What the check does not establish |

Do not add a separate report when the existing artifact carries the evidence.
Reuse passed checks while their inputs and assumptions remain unchanged. Repeat
only affected checks after a change; run the required final integration checks
once. A green project test suite alone does not prove the PRD is satisfied.

Keep the exit status and result of each required check. A later successful shell
command must not conceal an earlier failed test. Advance an evidence-dependent
phase only after its required checks pass; a failed fix stays in implementation
until the affected regression passes. Preserve failed attempts as history.

## Integrated product quality and correction

Before substantial implementation, concretize decisive qualities in the existing
requirements or delivery plan: observable characteristics, relevant references or
examples that would fail the assignment. PO owns overall quality; TDO translates
it into Story criteria and integrated checks. Shared quality contracts may be
referenced instead of copied. This adds no form or approval gate.

Judge the functioning product: behavior, comprehensibility, visual expression,
interaction between parts and relevant user experience. For a game this can mean
movement feel, feedback, presentation and learning the mechanics. Technical tests
prove what they exercise; they do not alone establish good design or experience.
Do not hide a failure of the whole behind individually satisfied Story criteria.
Keep human/AI code readability, appropriate components, maintainability, loading
and runtime performance, and security in scope where relevant.

Correct material requirement and quality defects within the mandate, then
re-review and verify affected criteria and integrations. A final defects list is
insufficient when correction is authorized and feasible. Reuse still-relevant
unchanged evidence. Distinguish agreed quality defects from optional improvements
or reviewer taste; suggestions do not become requirements without authority.
If tools and evidence cannot assess a decisive experience quality, mark it
unverified; working code or a still image cannot prove what they do not show.
If quality and resources conflict, expose the conflict and recommend a concrete
path within the existing owner decision process; do not silently lower quality.

## Useful copy in context

Every text should help its intended audience understand, navigate, act, decide or
experience the product. Rewrite or remove empty sales claims, obvious layout
descriptions, repetition and text that only fills a visual template. Keep an
explanation when it adds a next step, limitation or consequence of a choice.
A description that fits unrelated products unchanged deserves scrutiny; standard
functional labels such as “Save”, “Settings” and “Cancel” need no novelty.

Headings, subheadings and eyebrow text each need a purpose. Identify the content,
task, actual state or concrete benefit; omit an extra visible heading when the
context is already clear. Preserve necessary accessible names, understandable
navigation and semantic structure when removing decorative text.

Functional views do not receive advertising language by default. Marketing may
persuade through concrete supported claims. Words such as “smart”, “powerful”,
“seamless”, “best” or “AAA” cannot replace information or evidence; this is not a
banned-word list. Personality, humor, narrative and drama belong when they serve
the product. Instructions, buttons, status and errors must describe real behavior:
never assert saved data, safety or undo support that the product does not provide.
Product copy stands on its own in the audience's current context; private chats,
AI mistakes and discarded alternatives belong only in intentionally historical
artifacts when relevant.

PO owns audience and communicative purpose; TDO owns relevant acceptance criteria
and coherence; Dev writes and adapts text; Reviewer inspects comprehensibility,
relevance, redundancy, tone and factual claims in the rendered view or equivalent
use context. A word list or automated text check is insufficient. Meaningless or
misleading copy is a product quality defect, not automatically optional polish.

## Correctness, boundaries and readability

For domain algorithms, use independently sourced known answers or a separate
reference implementation, including settings and provenance. Round trips through
the same implementation can preserve the same bug in both directions.
Choose counterexamples from the requirements before reading the implementation.
Use targeted fault injection when it tests a consequential assertion gap.
For a finite set of advertised algorithm variants, choose a small set of
independent expected outputs that covers every variant and the risky
interactions. List which oracle covers which variant in the existing evidence
table. Self-generated examples and round trips do not fill an oracle gap;
report an uncovered variant explicitly and strengthen its check before claiming
coverage. Avoid an unnecessary Cartesian product of every setting.

For maintenance, start from the requested behavior change and its actual seams.
Reuse the existing architecture and still-valid evidence. Keep setup, planning
and review scoped to the delta and integration risk; a small addition does not
justify repeating the original product's discovery or performance campaign.

Keep domain logic independent of presentation. Separate asynchronous job
lifecycle, result snapshots, presentation and domain responsibilities where
they change independently. A returned result owns the input snapshot that
produced it; subsequent form edits must not silently change its meaning. Specify
worker/API messages at both ends and exercise cancellation, restart, stale
responses and handoff through the public UI/API boundary when relevant.

Use normal source formatting, named operations and the native formatter when
available. Generated/minified distribution files are different from maintained
source. Component count and line count do not establish maintainability. Review
whether a successor can find the change point and alter one behavior without
touching unrelated responsibilities. Avoid abstraction without a concrete seam.

## Runtime performance and resource use

Development time, model cost and product execution time are separate metrics.
For a compute-, I/O- or memory-intensive requirement, establish a representative
workload, correctness oracle and resource budget before optimizing. If the PRD
has no number, label the proposed engineering target as a target, not a new
user requirement. Record environment, workload hash, warmup, at least three raw
runs and median. Measure peak memory or another relevant resource as well as
elapsed time. Report timeouts, errors, first useful result and completion
separately; never substitute a result limit for equivalent work.

For a new batch operation or I/O loop, inspect work per item and the maximum
supported batch, even when an old single-item benchmark still passes. Count
queries, remote calls and transferred fields; measure the changed path at a
small and maximum valid input with the same correctness checks. Reuse setup and
unchanged evidence instead of repeating an unrelated performance campaign. A
missing numeric PRD target permits an explicit engineering investigation; it
must not turn unmeasured new-path performance into a claimed optimization.

Profile the hot path. Prefer reducing algorithmic work, redundant I/O,
allocation and repeated computation over cosmetic micro-optimizations. Bound
caches, inputs and concurrency. Cache invalidation is a correctness condition.
Keep a simpler oracle while changing a hot path, then repeat the same correctness
and performance workload. Report regressions and tradeoffs rather than calling
code optimized because it is shorter or asynchronous.

## Security applicability

Identify actual trust boundaries, data sensitivity, exposed entry points,
privileged operations and project policy. Select applicable controls, record
their source/version, map each to implementation and positive/negative checks,
and state exclusions. For web applications use relevant
[OWASP ASVS requirements](https://owasp.org/projects/asvs?tab=main); for delivery
practices consult [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final).
Neither reference makes every control applicable to every product.

Check untrusted input, authorization, injection, secrets, dependency provenance,
unsafe file/network access and denial-of-service boundaries where they exist.
Treat local HTTP servers as exposed to hostile browser origins: validate Host
against the actual listener as well as Origin. Test rejected requests through
the real HTTP boundary. Do not claim all standards are satisfied from a scanner,
passing tests or this checklist; report the controls actually verified.

## Knowledge that remains usable

Keep transient implementation status in runtime evidence. Durable profiles
contain verified commands, architecture and constraints, with source paths.
Native agent files are thin loaders: they must not copy feature status, command
lists or architecture facts from the profile. Read current evidence when the
relevant dependencies change. Update contradicted facts in the same delivery;
preserve human edits and separate product claims from proposed decisions.

For facts whose drift would mislead a successor, keep a compact version-1 JSON
evidence record with `claims`: each has `id`, `claim`, `document` and `sources`.
Document and source references contain `path` and `sha256`. Record only files
that actually support the claim, including relevant tests/configuration.
Use the trusted package helper `scripts/aim_engineering.py --repo <repo>
fingerprint <files...>` to obtain hashes, and `check <evidence.json>` to detect
changed, deleted or unsafe references. Store the record alongside existing
local review evidence. The helper never executes commands or certifies semantic
truth. Missing records are **unverified**, not fresh by default; unchanged
hashes mean only that the reviewed evidence did not change. Re-review the claim
before refreshing hashes. Negative claims need a bounded inventory/search too;
hashing one file does not prove a feature is absent elsewhere.

When a capability changes, review existing descriptions of its boundary too:
adding file import, persistence or a network call can invalidate an old absence
claim even if new usage instructions are accurate. Preserve historical review
records as history. Check affected prior claims before relying on them for the
current delivery, then record re-reviewed or superseded claims in the current
evidence; do not silently refresh old hashes or call stale evidence current.

## Scoped knowledge consumption

Use richer reuse evidence only for facts whose interpretation or reuse matters;
do not wrap every obvious source comment in a record. Put durable applicability
on the existing profile entry: `appliesTo` is a block list of locality IDs (or
only `repository`), `expectedUse` names a concrete next decision/check, and
`recheckWhen` is a block list of relevant changes. Keep run observations outside
the durable profile; it must not point into `.aim/` history.

`scripts/aim_engineering.py --repo <repo> knowledge --locality <id>` inventories
selected rules and their dependency closure, including per-rule fingerprints.
Add `--record <record.json>` to check version1 delivery evidence: `claims` contains
`category`, `id`, `ruleSha256`, and fingerprinted `sources`. An optional
`observation` has `outcome` (`used`, `helped`, `contradicted`, `not-used`), `summary`
and fingerprinted `artifacts`. A claimed benefit remains reported-only; loading
instructions does not establish benefit. Contradictions remain visible despite
matching hashes. Commands in evidence are never run. Unknown scope, stale sources
or failed observations require relevant human/agent reasoning and actual product
checks; refreshing hashes cannot make a false claim true.

Unrelated profile edits do not invalidate a per-rule fingerprint. If a selected
rule's assumptions or scope change, inspect current behavior before refreshing
its record. Preserve old observations as history and append current evidence.
At resume, read the active checkpoint, actual diff and affected rules before
trusting old review/test results. Resume from the smallest affected boundary;
do not regenerate unchanged plans or replay an already performed external action.

## Role skills and empty projects

Every role has a bundled engineering skill. Load only the active role's skill:
`role-skill-po.md`, `role-skill-tdo.md`, `role-skill-dev.md`, or
`role-skill-reviewer.md`. `aim.roles.yaml` binds role-specific project skills by
id, source and status. A skill is applied only after its actual instructions
are located and read. Expertise labels are not proof that a skill is installed.

An empty repository is not a reason for a calibration interview. Read the
provided requirements, goal, Epic or PRD, provision the bundled role skills and
derive **provisional capability candidates**. The read-only helper
`scripts/aim_engineering.py --repo <repo> skills --requirements <path>` reports
source lines and low-confidence keyword hints; it is not a semantic classifier.
Explicit input overrides conventional root PRD discovery. Match candidates to
skills actually available, inspect their instructions, and select only relevant
ones. Do not install a guessed package, invent expertise, infer the model, or
treat a mentioned framework as an approved choice. Record unavailable skills
with a concrete fallback. Refine once the stack and first implementation exist;
refresh affected bindings when requirements, dependencies or architecture change.

For already-authorized Auto delivery, perform this provisional selection inside
startup. Do not redirect a concrete product request into onboarding because a
profile is absent. Preserve real scope and Gate A/B decisions under the existing
authority, initialize through the trusted helper once, then address any consequential
unresolved product assumption. Reuse sufficient evidence; do not run an experiment
merely because implementation is starting. This does not replace a required Strict decision or grant
new authority. Record startup work only in the existing evidence artifact.

## Spend effort where it changes the result

Quality ambition is bounded by the assignment, resource limits and applicable
approvals. Assess cumulative time, cost, product, quality, external effects and
reversibility across all agents before a material deviation. No numeric budget
means proportionate work, not unlimited resources or an invented expansion
threshold. A complexity label alone cannot change cost profile, product priority
or ambition. Use the existing plan/decision surfaces, not a per-tool checklist.

Any evaluation must stay within its authorized campaign, run count and predefined
quality criteria. Record comparable starting conditions, models, resources and
assessment, and retain failed attempts and uncertainty. Aggregate gains cannot
hide an unacceptable loss of an important quality requirement; faster or cheaper
work is not improvement when the product becomes materially worse. This contract
authorizes no new comparison campaign, extra products or runs.

Load the active role, current checkpoint, selected locality and affected facts.
Read the full method or other role instructions only to resolve a specific
missing contract. Keep role transitions compact; planning and synthesis may stay in one session.
Allocate implementation and independent material review using
`adaptive-execution.md`; a sequential role switch is explicitly self-review. In Strict, combine compatible
planning material in one presentation while retaining each required decision.
In Auto, honor existing authorization without repeated requests. Calibration,
handoffs and documentation must earn their cost through a better decision or
verified result. Record avoidable overhead in the comparison, not as product
value. Quality and security checks remain proportional to the actual risk.

### Separate delivery time from repository improvement

When measuring a learning cycle, attribute intervals to setup, calibration,
configuration, reflection, knowledge-maintenance, implementation, verification,
coordination or waiting. Report repository improvement separately and retain the
combined total; do not hide its cost or require every improvement to repay itself
in the same task. Assess later benefit through fewer repeated failures, less
rediscovery, clearer change boundaries or measured runtime/resource gains.

The read-only package helper `scripts/aim_engineering.py --repo <repo> timing
<record.json>` summarizes one sequential session. Its input is version 1 with
`intervals`, each containing a unique `id`, `activity`, `start` and `end`:

```json
{"version":1,"intervals":[{"id":"verify-profile","activity":"calibration","start":"2026-09-29T10:00:00Z","end":"2026-09-29T10:01:00Z"}]}
```

Record actual timezone-aware timestamps at phase boundaries in existing run
evidence; do not estimate a split after completion. The helper rejects overlaps
and reversed intervals, exposes unattributed gaps and does not certify what work
occurred. Keep parallel sessions separate: summed agent time is not elapsed wall
time. Report unavailable token/currency cost as unavailable, never derive it from
duration. `setup` is a separate coarse category for mixed startup work; do not
silently count it as calibration, implementation or verified repository
improvement. Use finer categories only when their actual boundaries were recorded.
Product runtime measurements remain separate from agent work time.
