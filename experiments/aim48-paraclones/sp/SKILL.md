---
name: aim-48-sp
description: Run the unpublished AIM 4.8 SP candidate using pinned Superpowers for all graph design and orchestration, with shared AIM product governance.
---

# AIM 4.8 SP experimental orchestration

Read `references/experiment-governance.md` and `brief.json` once. The bundled AIM
product contracts remain available under `references/` for requirements, quality,
evidence, authority and acceptance semantics.

All graph design, work decomposition, assignment, task scheduling, subagent and
reviewer orchestration, correction routing and continuation in this candidate
come from the pinned unmodified Superpowers source under `vendor/superpowers/`.
Do not use AIM Native orchestration/default graph/campaign helpers, `executionPlan`
or `activity` as a second graph controller. Shared native AIM product lifecycle
may remain without an executionPlan. Superpowers task scratch is task execution
evidence, not a second authoritative product backlog.

For plan construction read `vendor/superpowers/skills/writing-plans/SKILL.md`.
For execution select and follow the applicable Superpowers route:
`vendor/superpowers/skills/subagent-driven-development/SKILL.md` for suitable
independent task delegation, or `vendor/superpowers/skills/executing-plans/SKILL.md`
for a coherent inline execution. Follow the chosen route's linked briefs,
review-package scripts, review/fix-loop references and final branch review.
Use its task-result protocol, dispatch decisions and progress workspace.

The following are explicit identical experiment/owner constraints, not hidden
Native improvements: model stays GPT-6 Luna Max for every agent; total arm budget
and maximum concurrency remain binding; existing product acceptance rules and
source/profile protection remain in force. Upstream role/model or publication
instructions cannot expand those permissions. The frozen brief and budget are
the user's approval of this isolated build; no routine design/plan approval stop
is needed. Record any genuine incompatibility and continue other useful work.

Read native-host adaptation references only if the selected route needs them.
Retain actual graph/task/dispatch/review evidence so compliance can be assessed
after the product has been scored. Do not copy Native campaign handling into
this candidate to make both controllers behave alike.
