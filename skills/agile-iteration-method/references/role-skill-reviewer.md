<!--
GENERATED FILE. DO NOT EDIT DIRECTLY.
Generated from canonical Agile Iteration Method sources.
Regenerate with: python3 scripts/build_public_skill.py
Source: docs/workflow/role-skill-reviewer.md
-->

# Reviewer engineering skill

Skill id: `aim-reviewer-engineering`. Bundled with AIM; applies to review.

- Derive counterexamples from the binding requirements before adopting the
  implementation's examples. Verify public behavior and independent known
  answers; round trips and tests mirroring the code are insufficient alone.
- Check the oracle-to-variant mapping for every advertised algorithm variant.
  Probe a consequential variant absent from the main example; use a bounded
  mutation when it can reveal a blind spot. Green tests are not coverage proof.
- Try the consequential integration seams: edited inputs after a result,
  cancellation, repeated runs, stale async messages and result handoff. Check
  negative and ambiguous outcomes without demanding a unique answer where the
  data admits several valid answers.
- Inspect what the tests would miss. Use a bounded fault injection when useful;
  test count and passing commands are not measures of assertion strength.
- When reviewing changed mutations, probe a relevant post-commit read failure
  and the next user/consumer action. Check actual side effects and stale action
  controls, not only the displayed warning. Apply the outcome distinctions in
  `adaptive-execution.md`; unrelated changes need no such probe.
- Check performance on equivalent work, reporting raw trials, median, limits
  and memory/resource data. Keep first result separate from completion.
- Trace applicable security controls to rejection tests at actual boundaries.
  Distinguish a verified control from an untested compliance claim.
- Assess a real follow-up change: can a successor locate and change one
  responsibility safely? Check source formatting, coupling and duplicated logic.
- Cross-check durable documentation and native loaders against current code.
  Hash freshness helps find drift; it does not establish semantic correctness.
  Check old absence claims when capabilities change and distinguish historical
  evidence from claims re-reviewed for the current delivery.

Report reproducible findings with severity and evidence. Keep inspection
read-only except isolated test artifacts. Do not accept work or modify runtime
state. Re-review changed behavior after a fix, not every previously passed fact.

Use `adaptive-execution.md` for activity ownership, independent material review,
current-code evidence and targeted responsibility/resource checks. Do not enact
extra agent sessions merely to mirror role names.
