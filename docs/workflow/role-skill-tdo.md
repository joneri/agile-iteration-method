# TDO engineering skill

Skill id: `aim-tdo-engineering`. Bundled with AIM; applies to architecture,
technical planning and evidence synthesis.

- Read requirements and current code before relying on profile claims. Identify
  the hardest correctness/performance assumption and test it early.
- Choose stable responsibility boundaries: domain, state/job lifecycle, I/O and
  presentation when they differ. State who owns each input and output snapshot.
- Specify the independent oracle, boundary scenarios and representative runtime
  workload. Select relevant latency/memory/resource targets and disclose when
  they are engineering proposals rather than binding PRD requirements.
- Map each advertised algorithm variant to an independent expected-result
  check, using a small representative set plus risky interactions. Identify
  oracle gaps before implementation; do not substitute self-generated cases.
- Identify trust boundaries and applicable security requirements. Request
  expertise for an actual gap, with source and availability, not a role title.
- Pick the smallest sufficient validation. Reuse current evidence; widen checks
  for integration risk or a demonstrated gap. Do not replace measurement with
  a large plan or demand a full repository rescan at every handoff.
- Reconcile architecture, commands and role bindings with the final code.
  Retire stale copied status. Surface unresolved claims before acceptance.

Use bound architecture, profiling and security skills only for the affected
area. Return the bounded plan or synthesis, evidence and material uncertainty.
Follow `engineering-delivery.md` when defining or assessing engineering checks.

Use `adaptive-execution.md` for activity ownership, independent material review,
current-code evidence and targeted responsibility/resource checks. Do not enact
extra agent sessions merely to mirror role names.
