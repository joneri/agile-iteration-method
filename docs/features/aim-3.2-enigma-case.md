# Same Luna. Same brief. A convincing win for AIM 3.2.

**93.5/100 with AIM. 49.8/100 without it.** In this completed Enigma comparison,
the same GPT-6 Luna model, at high reasoning effort, worked from the same PRD.
Luna + AIM 3.2 delivered the stronger product against predefined KPI weights:
better reference correctness, useful results on new search cases, a more polished
interface and clearer code structure.

The difference shows up where users need the software to work:

| Product outcome | Luna + AIM 3.2 | Luna alone |
| --- | ---: | ---: |
| Weighted product score, out of 100 | **93.5** | **49.8** |
| Passed independent Py-Enigma vectors | **123/123** | **1/123** |
| New positive cracking cases with a valid candidate | **9/9** | **0/9** |
| Returned candidates validated against Py-Enigma | **35/35** | **21/21** |

AIM earned its process in this pair. It produced software that handled the new
acceptance cases, rather than merely passing its own examples. The result
challenges the claim that AIM adds only overhead: here, the extra delivery work
accompanied a convincing improvement in the delivered product.

## What the user received

The brief asked for a local browser app that simulates a historical three-rotor
Enigma I/M3 and searches for possible settings from ciphertext and a known
plaintext fragment, or crib. Rotor order, reflector and rings are known; start
positions and plugboard pairs are unknown. Results must be inspectable and
transfer correctly into the simulator. Progress, cancellation, examples and
useful desktop/mobile layouts are part of the product.

The AIM app passed the reference vectors across rotor orders, reflectors, varied
rings, plugboards and historical stepping. It found valid candidates in all nine
new positive search cases, including known/unknown crib placement and a crib
crossing rotor stepping.

The Luna-only app's own example worked. Its 21 returned candidates were all
valid. Its weaknesses were missed valid results: a ring/notch stepping error,
incorrect handling of later crib placement, and a global search-budget stop
that ended many new cases before any start position was fully checked. One
positive case completed the full search and incorrectly returned no candidate.
An incomplete search was not counted as a successful negative result.

The visual assessment also favored AIM: more considered typography, spacing,
hierarchy, explanations, unresolved plugboard-letter display and result preview.
Code review found clearer boundaries between machine logic, search, worker,
views and the saved search request. Candidate transfer retained the search's
original settings after the form changed; the Luna-only app read the newer form
values and opened the wrong configuration. Design and maintainability are
reasoned qualitative assessments, not instrumented aesthetic measurements.

## Faster application searches

Both apps completed the same two benchmark workloads. These figures measure the
**applications' search cores in Node/V8**, not the speed of their coding agents.

| Complete search workload | AIM app, median | Luna-only app, median | Runtime ratio |
| --- | ---: | ---: | ---: |
| Shared positive example from the Luna-only app | **0.207 s** | 8.467 s | **40.9× faster with AIM** |
| Full search with no candidate | **0.183 s** | 2.654 s | **14.5× faster with AIM** |

Each workload fully checked 17,576 start positions in both apps. One warmup was
followed by three alternating measurements per app on the same Apple M5 Pro,
using the same inputs and a 30-second limit. The candidate cap of 20 did not
truncate either workload. No measured run timed out. Fast, incomplete searches
are excluded from these comparisons. The ratios apply to these two specific
workloads; they are not a promise that every AIM-built app will run 41× faster.

## Method and scoring

The pair was assessed on 30 September 2026 using the Enigma test plan and KPI
weights fixed on 27 September, before the original comparison's implementations
were inspected. This is a new completed pair, not a rescore of the earlier
products. Both builders used `gpt-6-luna` with `high` reasoning. One used AIM
3.2, including a separate Luna reviewer; the other was instructed to work
without AIM. Their PRDs are byte-identical:
`59ab6a803dd15e40a68f20f56b2ffcc081b3a0ac60aec873f5c93c2d733a9493`.

| KPI | Weight | AIM, out of 10 | Luna alone, out of 10 |
| --- | ---: | ---: | ---: |
| Enigma correctness | 25% | 10.0 | 4.0 |
| Cracking and valid results | 30% | 9.5 | 3.0 |
| Other PRD requirements | 15% | 9.0 | 7.5 |
| Performance and stability | 10% | 9.5 | 6.0 |
| Usability | 10% | 8.5 | 8.0 |
| Maintainability and test protection | 10% | 8.5 | 5.5 |

The weighted sum is each score divided by 10, multiplied by its percentage
weight: 93.5 and 49.75, with the latter rounded to 49.8. Scores incorporate
tested behavior and reasoned assessment. A root cause receives its primary
deduction in one KPI; the same ring defect is not deducted again as a separate
search fault. File count, framework choice and the mere presence of AIM
documents earn no points.

The 123 vectors were generated before the two new apps were inspected. Their
reference is Py-Enigma 1.0.2, checked against its published guide vector and the
basic `AAAAA → BDZGO` example. All returned candidates were replayed with that
reference. Five separate AAA-ring simulator vectors passed in the Luna-only app,
isolating plugboard behavior from its ring/notch fault. The full search dataset
also includes ambiguous, impossible, negative and Unicode cases; the 9/9 claim
refers specifically to the nine new positive cases, not every case in the suite.

This is an AIM author's Codex-based product comparison, not an external
third-party audit. “Independent” describes the reference library and test data
relative to the apps' own code and examples.

## Development time and remaining limits

Luna alone finished its main build turn faster: **14:52 versus 52:59 with AIM**,
or about 3.56× sooner. AIM included a parallel review of approximately 3:40;
summed agent work was about 56:39, while elapsed main-turn time remained 52:59.
Human time, token prices, total currency cost and the time needed to repair the
Luna-only product were not measured. A faster initial build and a stronger
delivered product are separate outcomes.

Both apps retain a Unicode normalization defect: some non-A–Z characters become
ASCII letters when uppercased and unexpectedly advance the machine. AIM's
64-node budget may still leave other valid crib searches incomplete. Both apps
could improve small help text; AIM's tabs lacked expected arrow-key navigation.
UI checks used 1440×1000 and 390×844 browser viewports, not a physical mobile
device or a screen reader. UI integration coverage was absent from AIM's own
automated product tests. Memory use was not measured in this pair.

The outcome establishes a convincing AIM win for these two frozen products. A
single pair cannot isolate the causal contribution of the method or establish
superiority across all models, tasks and projects. Follow-up repair, maintenance
and additional fresh pairs would answer different questions.

## Public evidence

The public snapshot includes the identical brief, frozen test inputs, recorded
results, benchmark repetitions and product-file hashes. Absolute workstation
paths have been removed from the version manifest. Other copied data files
retain their original bytes. Product source code and private chat logs are not
included, so this package supports inspection and reference replay rather than
a complete rebuild of the two apps.

- [Machine-readable summary and evidence hashes](evidence/2026-09-30-luna-aim32-enigma/summary.json)
- [Identical PRD](evidence/2026-09-30-luna-aim32-enigma/enigma-prd.md)
- [123 vectors](evidence/2026-09-30-luna-aim32-enigma/vectors.json) and [14 search inputs](evidence/2026-09-30-luna-aim32-enigma/cases.json)
- [AIM vector results](evidence/2026-09-30-luna-aim32-enigma/luna-aim-32-smoke.json) and [Luna-only vector results](evidence/2026-09-30-luna-aim32-enigma/luna-naked-smoke.json)
- [AIM search results](evidence/2026-09-30-luna-aim32-enigma/luna-pair-search-aim.json) and [Luna-only search results](evidence/2026-09-30-luna-aim32-enigma/luna-pair-search-naked.json)
- [Candidate replay results](evidence/2026-09-30-luna-aim32-enigma/luna-pair-candidate-validation.json) and [plugboard isolation](evidence/2026-09-30-luna-aim32-enigma/luna-pair-panel-isolation.json)
- [Warmup and scored runtime measurements](evidence/2026-09-30-luna-aim32-enigma/luna-pair-benchmark.json)
- [Version manifest](evidence/2026-09-30-luna-aim32-enigma/luna-pair-version-manifest.json) and [original integrity check](evidence/2026-09-30-luna-aim32-enigma/luna-pair-original-integrity.json): 40 AIM files and 13 Luna-only files, zero changed originals
- [Reference-replay script](evidence/2026-09-30-luna-aim32-enigma/verify-reference.py): validates the frozen vector answers and recorded candidates using Py-Enigma 1.0.2

Run the replay script in a Python environment containing `py-enigma==1.0.2`.
It reads the public snapshot and prints checks without modifying the data.
The scoring summary also records the original source report's SHA-256, the test
environment and exact development durations. Product-specific search timings
in the diagnostic result files are single runs; only the repeated benchmark
file supplies the runtime medians above.

Documentation: CC BY 4.0. Attribution: Jonas Eriksson, Agile Iteration Method.
