# AIM: measured Enigma results and remaining limits

AIM's latest frozen Enigma product assessment scored **96.5/100**, passed
**123/123 simulator vectors**, and solved **9/9 new positive search cases**.
All **114/114 retained candidates** passed independent crib, placement and
preview checks. The retained GPT-6 Luna-only application scored **49.8/100**;
the earlier AIM result was **93.5/100**.

The product result is strong, while the native delivery remains unfinished:
one selected performance goal failed and required browser proof is missing.
The product score does not establish completed AIM delivery, user acceptance,
or either original 50% reduction target.

Evidence as of **18 October 2026**. Exact latest test provenance is
**AIM 4.4.0-rc.11**, GPT-6 Luna, high reasoning effort: one fresh build and one
separate reviewer. Later AIM source revisions do not inherit a new Enigma test
from this report. The historical reference is **3.2.0**, not 3.2.1.
[The public comparison export](evidence/2026-10-18-enigma-comparison/comparison.json)
contains exact retained metrics, nulls, source-artifact hashes and limits.

## The same model, with and without AIM

| Enigma M3 product outcome | GPT-6 Luna without AIM | GPT-6 Luna with AIM, latest assessed delivery |
| --- | ---: | ---: |
| Product score /100 | 49.8 | 96.5 |
| Simulator vectors passed | 1/123 | 123/123 |
| New positive search cases with a valid candidate | 0/9 | 9/9 |

The Luna-only result is the frozen **30 September 2026** M3 build; the latest
assessed AIM delivery is from **18 October 2026**. Both used GPT-6 Luna with
high reasoning effort, the same original PRD, 123 simulator vectors, 14 search
cases and six category weights. The baseline's exact weighted score is 49.75,
published as 49.8. The [original paired comparison](aim-3.2-enigma-m3-case.md)
and its [unchanged summary](evidence/2026-09-30-luna-aim32-enigma/summary.json)
retain the baseline and its original AIM counterpart, which scored 93.5.

These are retained results, **not a new paired experiment**. Dates, prompts,
internal goals, assistance, budgets and delivery completion differ. The score
comparison does not isolate AIM's causal contribution, establish a general
advantage or prove completion of the native delivery. Subsequent source
versions do not inherit this score. No baseline or product has been rerun for
this presentation change. The AIM-version trend below is a secondary view.

## What was tested

The unchanged M3 brief asks for a local browser app that simulates Enigma I/M3,
searches unknown start positions and plugboard settings from a known plaintext
fragment, and transfers candidate settings into the simulator. Results must
show ambiguity, completion status, progress and cancellation.

The latest assessment reused the original PRD, 123 independent simulator
vectors, 14 search cases and six category weights. Every retained candidate
was replayed against Py-Enigma 1.0.2. Its search completed all 14 original cases
without timeout or error. The ambiguous case displayed 100 proposals while
finishing the feasible scan; a display cap did not stop the search.

The fixed browser checklist passed **14/15** obligations. A results heading
produced a 391 px document at a 390 px viewport, although primary controls fit.
One additional bounded probe found inconsistent non-ASCII crib validation
between the UI and core. That probe is outside the fixed denominator; the
supported non-ASCII policy is ambiguous, so it is a minor UI finding rather
than an established failure of supported A–Z searches. No material central-flow
finding was established in the assessed scope.

## Retained product outcomes

These are stored outcomes, including failures and missing results. Product
scores and method validity are separate. Older runs are not retroactively
certified by a later activation guard.

| Frozen AIM version | Product score /100 | Simulator | Positive cases with valid crib | Valid retained candidates | Retained limit or outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| 3.2.0 | 93.5 | 123/123 | 9/9 | 35/35 | Historical reference; Unicode limitation |
| 4.3.0 | 88.5 | 123/123 | 8/9 | 133/133 | Automatic-placement timeout; Unicode |
| 4.4.0-rc.1 | — | 123/123 | 8/9 | 69/69 | Unscored; timeout, Unicode, stale handoff, production worker 404 |
| 4.4.0-rc.2 | 91 | 123/123 | 9/9 | 113/113 | Unicode limitation |
| 4.4.0-rc.3 | 82.75 | 123/123 | 7/9 | 213/215 | Invalid later-offset candidates; timeout |
| 4.4.0-rc.4 | 86.25 | 123/123 | 8/9 | 17,589/17,589 | Valid long crib rejected by a 48-character limit |
| 4.4.0-rc.5 | 83.25 | 123/123 | 7/9 | 112/116 | Invalid candidates; mobile and validation findings |
| 4.4.0-rc.6 | 79.5 | 123/123 | 7/9 | 17,584/17,584 | Invalid method attribution: no native ledger |
| 4.4.0-rc.7 | 84.25 | 123/123 | 3/9 | 203/203 | Method validity unknown; six positive-case timeouts |
| 4.4.0-rc.8 | — | — | — | — | No full Enigma product run |
| 4.4.0-rc.9 | 68 | 1/123 | 1/9 | 102/104 | Ring defect; invalid terminal evidence; native review not reached |
| 4.4.0-rc.10 | — | — | — | — | Bounded component checks; no full Enigma product run |
| 4.4.0-rc.11 | **96.5** | **123/123** | **9/9** | **114/114** | Valid guard, failed unfinished native delivery |

Candidate populations and display caps differ. Valid candidate precision does
not measure positive-case coverage; matching preview is a separate predicate
where recorded. The latest 114/114 includes all three checks. A dash means
unmeasured or unavailable, not zero or a successful result.

The category weights remain correctness 25%, cracking validity 30%, other
requirements 15%, performance/stability 10%, usability 10%, and
maintainability/test protection 10%. All retained category scores are below.

| Version | Correctness | Cracking | Other requirements | Performance | Usability | Maintainability |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.2.0 | 10 | 9.5 | 9 | 9.5 | 8.5 | 8.5 |
| 4.3.0 | 10 | 9.5 | 9 | 5 | 8.5 | 8 |
| 4.4.0-rc.1 | — | — | — | — | — | — |
| 4.4.0-rc.2 | 10 | 9.5 | 9 | 6.5 | 9 | 8.5 |
| 4.4.0-rc.3 | 10 | 7 | 9.5 | 6 | 9 | 7.5 |
| 4.4.0-rc.4 | 10 | 7.5 | 9.5 | 7 | 9 | 8.5 |
| 4.4.0-rc.5 | 10 | 7 | 9.5 | 8.5 | 7 | 7.5 |
| 4.4.0-rc.6 | 10 | 7.5 | 8 | 3 | 8.5 | 8.5 |
| 4.4.0-rc.7 | 10 | 9.5 | 7.5 | 2 | 8.5 | 9 |
| 4.4.0-rc.8 | — | — | — | — | — | — |
| 4.4.0-rc.9 | 1 | 9.5 | 10 | 4 | 9 | 9 |
| 4.4.0-rc.10 | — | — | — | — | — | — |
| 4.4.0-rc.11 | 10 | 10 | 10 | 9 | 9 | 8.5 |

Scores are out of ten. The weighted sum is the category score divided by ten,
multiplied by its weight. Historical Unicode deductions were assigned to
different categories, and one RC9 calibration statement conflicts with the
RC7 source. The stored RC7 summary and native ledger also disagree about its
internal performance target. These contradictions remain open; no score or
historical source has been rewritten. Direct outcome counts are the stronger
comparison where calibration differs.

## Runtime, build time and recorded tokens

| Version | Complete no-result search, s | Complete shared-example search, s | Build wall, s | Uncached input tokens | Cached input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3.2.0 | 0.183 | 0.207 | 3,178.849 | — | — | — |
| 4.3.0 | 4.114838 | 14.809235 | 1,398.866 | 452,318 | 20,694,400 | 102,749 |
| 4.4.0-rc.1 | 1.669425 | 19.114594 | 889.857 | 257,545 | 12,728,320 | 72,574 |
| 4.4.0-rc.2 | 2.333927 | 5.649268 | 868.095 | 356,975 | 24,736,896 | 105,170 |
| 4.4.0-rc.3 | 0.140293 | 1.673058 | 1,431.759 | 376,132 | 18,899,968 | 123,147 |
| 4.4.0-rc.4 | 1.743315 | 1.816387 | 2,093.638 | 599,976 | 45,964,032 | 198,808 |
| 4.4.0-rc.5 | 0.234299 | 0.407248 | 1,420.646 | 391,925 | 27,908,608 | 115,650 |
| 4.4.0-rc.6 | 12.994635 | 13.041231 | 869.055 | 247,414 | 11,705,728 | 59,287 |
| 4.4.0-rc.7 | 3.977839 | 9.263665 | 1,896.187 | 565,147 | 21,979,776 | 153,351 |
| 4.4.0-rc.8 | — | — | — | — | — | — |
| 4.4.0-rc.9 | 0.349379 | 0.866485 | 1,943.614 | 553,013 | 32,776,320 | 167,156 |
| 4.4.0-rc.10 | — | — | — | — | — | — |
| 4.4.0-rc.11 | **0.113098** | **0.114326** | 2,243.502 | 700,746 | 34,486,272 | 211,244 |

Runtime columns are retained medians for the two named external workloads;
they are separate from the internal A/B workloads below. The latest external
measurement used the shipped asynchronous search with UI/worker defaults,
Node 26.7.0, one warmup and three measured runs. Both workloads checked 17,576
starts. Raw latest samples and exact medians are in the
[comparison export](evidence/2026-10-18-enigma-comparison/comparison.json).

Historical direct-core timing and later asynchronous implementations use
different paths, yields and limits. Build windows also differ: the reference
is a completed main turn, whereas the latest 2,243.502 seconds ends with an
unfinished native delivery under a 40-minute cap. These are observed resource
figures, without a controlled cross-version speedup claim.

Tokens cover the named builder/reviewer scope where available; RC9 had no
reviewer. Older windows start at session creation or recorded dispatch and
are not identical accounting scopes. Cached input is included in total input;
reasoning is included in output. The latest 349 outer tool calls include
product work and are not 349 method/status rounds. Actual currency cost,
account usage percentage, pure administration and a comparable complete
method-context denominator remain unknown. Neither 50% target is proven.

## Why delivery is still unfinished

The frozen native receipt is revision 5, `in_progress`, with valid activation
and submission guards, outcome `failed`, and next action `correct_or_decide`.
The selected internal targets require a complete all-placement search over
100-letter ciphertext and a 10-letter crib, through core, adapter and browser.
The original PRD contains no numerical five-second SLA.

| Internal workload or obligation | Retained result |
| --- | --- |
| Witness A, core median | 4,391.337 ms |
| Witness A, browser median | 4,637.8 ms; below 5,000 ms |
| Witness B, core median | **5,518.997 ms; above 5,000 ms** |
| Witness B, browser and whole-message load proof | Missing |
| Native variant and no-result checks | `unmeasured` |
| Native Gate D, validation and user acceptance | Not reached or claimed |

The native combined A record contains six samples and a 4,473.728 ms median;
it does not replace separate path medians or missing B proof. The long browser
cancellation exercise recorded a 100 ms heartbeat and 807 ms cancellation
latency, on a different workload from historical cancellation checks. It is
not a controlled cancellation-speed comparison.

The separate reviewer caught an early offset error and later reported the
delivery was not ready for Gate D. Two coordinator interventions clarified
complete scan scope and requested measured diagnosis. No parent product repair
was made. This is observed assisted behavior; it does not prove autonomous
future adherence, complete recovery or causal benefit from learning cards.

## Evidence and interpretation

This is the AIM author's Codex-based evaluation, with independent reference
data and a separate same-model reviewer; it is not a third-party audit.
One run, changed internal goals, prompts, learning and budgets cannot establish
general superiority or an isolated causal method-version effect.

The [sanitized public export](evidence/2026-10-18-enigma-comparison/comparison.json)
includes retained historical rows, latest numeric results and source-artifact
hashes. It excludes workstation paths, private session identities, transcripts,
product source and protected inventories. It supports inspection and arithmetic
checks, rather than a complete product rebuild or new runtime measurement.
Frozen source artifacts and earlier raw drafts remain preserved separately.

The [historical M3 pair](aim-3.2-enigma-m3-case.md) retains its original
with/without-AIM result and reference replay package. The
[historical M4 follow-up](aim-3.2-enigma-case.md) is a separate upgrade assessment,
not an M4 result for the latest tested AIM version. The
[evaluation protocol](paired-evaluation-protocol.md) distinguishes fixed external
product scoring from method readiness in future runs.

Documentation: CC BY 4.0. Attribution: Jonas Eriksson, Agile Iteration Method.
