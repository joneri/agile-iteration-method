# AIM 3.1: evidence and limits

The 3.1 release combines tested AIM tooling corrections with stronger
project skill configuration, adaptive activity allocation, independent review
and scoped knowledge guidance. Its release package checks are separate from the
earlier product comparisons below.

## What the new controls establish

Actual profile consumers validate role skill bindings and instruction paths.
Calibration distinguishes verified localities from whole-repository coverage.
Review checks reject stale or missing changed-file evidence. Installed runtime
tests exercise startup and recovery dependencies. These are concrete checks of
AIM's own behavior, not a guarantee that every resulting product is correct.

The four canonical roles and project-native agents already existed in 3.0.8.
The additions strengthen their skill bindings, actual work allocation, review
separation and evidence checks. Native agent execution remains conditional on
the host's capabilities and permissions. AIM does not automatically install
arbitrary skills or guarantee an optimal staffing choice.

## Development comparison, 29 September 2026

An earlier frozen experimental package (candidate 15, product version 3.0.8)
was compared with ordinary GPT-6 Astra High on the same local host, tools and
per-stage budgets. Each arm retained its own product and notes through four
fresh sessions. The 3.1 release was not the package used in that comparison.

One completed data/compute chain showed:

| Measure | AIM candidate 15 | Ordinary Astra |
| --- | ---: | ---: |
| Total builder wall time, including setup, maintenance and review | 56.47 min | 23.88 min |
| Unresolved material-moderate findings in blind review | 1 | 1 |
| Follow-up maintainability judgment | Tie | Tie |

On the preregistered workloads, the geometric mean of stage 2–4 median ratios
was 0.408 for peak resident memory and 0.875 for program runtime: approximately
59% less peak memory and 12% shorter runtime. Each stage used a warmup and three
scored process launches. Memory was lower in all three measured stages of this
one chain. These are measurements of the generated program, not the model's
context usage, token bill or the memory consumption of AIM itself.

The blind review found that the ordinary product lost a valid request ID on a
deeply nested invalid query. The AIM product retained a baseline filesystem
handling defect: a symlink loop could be reported as an empty archive outside
the corrected streaming entry point. The automatic assessor groups passed, but
the unresolved documented behavior violation blocked the mandatory correctness
guard. Consequently, the numerical memory improvement did not qualify as an
overall AIM win under the locked protocol.

An earlier UI/API chain also established no AIM win and had asymmetric host
failures affecting native child-agent creation. It is retained as nonconfirmatory.
A prospectively reviewed symmetric CLI-host correction preceded the data chain.
The broader experiment stopped at a user-requested pause after 16 of 48 planned
builder sessions; remaining sessions were not silently treated as completed.

## Supported interpretation

The results show a useful resource-efficiency observation and real improvements
to AIM's checks. They do not establish generally faster development, a lower
product defect rate, uniformly better memory use, or superiority over ordinary
Astra. Three stages of one evolving product are not three independent projects.
Nor do differently scoped earlier tests prove a controlled before/after speed
improvement in AIM itself.

Blind reviewers saw product documentation that contained some process-related
words and local measurement claims, but no arm map or experiment cost results.
File ownership and instruction boundaries provided isolation on a shared host;
this was not an operating-system sandbox. Backend model revisions and complete
child-token accounting were unavailable. No monetary saving is claimed.

The frozen protocol, products, raw measurements, failures and review evidence
are retained separately from this distributable package. Changed candidates
need new unexposed tasks for further comparative claims. The evidence should
remain attached to any public discussion of these measurements.
