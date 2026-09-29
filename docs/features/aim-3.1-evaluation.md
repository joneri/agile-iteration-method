# AIM: benefits and measured results

AIM helps you carry software work across sessions and tools, reuse project
knowledge, discuss decisions with your repository, and coordinate implementation
and review. Our latest data test also produced a concrete resource-efficiency
result: the AIM-built program used **59% less peak RAM with 12% shorter runtime**
than the program built by the same model without AIM.

## Less memory. Faster code.

The completed data comparison measured the programs produced by AIM and ordinary
GPT-6 Astra High on the same host and workloads:

| Product performance | Observed result with AIM |
| --- | --- |
| Maximum RAM used during execution | **59% lower** |
| Time to run the measured workload | **12% shorter** |
| Follow-up stages with lower peak RAM | **3 out of 3** |
| Follow-up stages with shorter runtime | **3 out of 3** |

Peak RAM was approximately **25 MB for the AIM-built program versus 62 MB** for
the program built without AIM. Peak RAM means the greatest amount of resident
working memory used at any point during a run.

For a user running that workload, the benefit is concrete: less RAM occupied and
less time waiting for the program to finish. A smaller memory footprint can also
leave more room for other work on the same machine. Hosting-cost savings and
higher concurrent capacity were not measured in this test.

These figures come from three follow-up stages of one evolving data product,
using a frozen development candidate before AIM 3.1. They are observations from
that test, rather than a performance guarantee for every project.

## Benefits beyond a single coding task

| AIM capability | What it gives you |
| --- | --- |
| **Continue across Codex, Claude Code and GitHub Copilot** | Pick up saved AIM work in another supported tool, with the same workflow and project knowledge. The next tool needs AIM and access to the same current repository and saved state. |
| **Discuss with your repository** | Explore ideas, architecture and tradeoffs using relevant code and project context, without changing code or starting implementation. |
| **Reuse verified project knowledge** | Build on known commands, structure, conventions and decisions instead of repeating the same basic orientation in every session. Relevant code is still checked when needed. |
| **Follow work through AIM UI** | See delivery status, evidence and the next decision in one control room. Users returning from early 3.0 also get the accumulated startup, work-preservation, action-tracking and recovery improvements. |
| **Match skills and agents to the project** | Connect available skills to roles and allocate bounded work with explicit ownership and dependencies, where the host supports native agents. |
| **Review the code that actually changed** | Check review evidence against current files and keep material changes under separate review before acceptance. |

These are product capabilities, not additional performance measurements. Shared
saved state, Discuss and the four canonical roles were already AIM strengths
before 3.1; the release strengthens skill bindings, work allocation and evidence
checks. See the [feature guide](../product/features.md) for operating details.

## What was verified for AIM 3.1

- **472 passing regression tests** in the release validation.
- **Three supported tool integrations:** isolated official skills CLI checks for
  Codex, Claude Code and GitHub Copilot.
- **Independent review:** development and release rechecks with no remaining
  material findings in the reviewed changes.
- **Validated publication:** package consistency, documentation, knowledge
  evidence, product coherence and release artifacts passed their checks.

The checks cover AIM's own tooling and distribution. They do not turn the
resource-efficiency result into a claim that every generated product is correct.

## How to read the comparison

The data test ran on 29 September 2026 with the same GPT-6 Astra High model,
local host, tools and per-stage budgets in both arms. Each arm continued its own
product through four fresh sessions. The tested AIM package was frozen candidate
15, with product metadata 3.0.8, rather than the final 3.1 release.

Each measured follow-up stage used a warmup and three scored process launches.
The headline percentages use the geometric mean of stage 2–4 median ratios:
**0.408 for peak resident RAM** and **0.875 for program runtime**. The three stages
belong to one product, not three independent projects. The figures measure the
generated program, not model context, agent memory or token consumption.

There was a development tradeoff: AIM took **56.47 minutes** to build and review
the chain, versus **23.88 minutes** without AIM. Automatic assessor groups passed
for both, but blind review found one unresolved material-moderate behavior defect
in each product and judged follow-up maintainability a tie. AIM retained a
filesystem-handling defect; the other product lost a valid request ID on a deeply
nested invalid query. The unresolved AIM defect failed the protocol's mandatory
correctness guard, so the resource gains did not qualify as an overall protocol
win. General development-speed or defect-rate superiority is not established.

The earlier UI comparison was nonconfirmatory because of asymmetric host failures.
The experiment is paused after 16 of 48 planned builder sessions. Raw measurements,
the frozen protocol and review evidence are retained separately. Reviewers saw
some process-related wording in product documentation, but no arm map or cost
results. Backend model revisions and complete child-token accounting were
unavailable. Further comparative claims need fresh, unexposed tasks.
