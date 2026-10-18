# Better software. From the same AI.

This is the historical AIM 3.2 M3/M4 pair. The original M3 reference identifies
**3.2.0**, not 3.2.1. See [AIM's latest assessed Enigma results and limits](aim-enigma-evaluation.md)
for later frozen assessments; the results below remain unchanged.

We asked GPT-6 Luna to build the same web app twice: once with AIM 3.2 and
once without. The app had to simulate historic Enigma cipher machines and
find settings that decode a message. We tested both products, then gave them
the same larger upgrade: add a more complex, four-rotor machine while keeping
the original features working.

**AIM delivered the stronger product in both tests.** At initial delivery,
Luna + AIM scored **93.5/100 against 49.8/100**. After the upgrade, it scored
**93.5/100 against 62.8/100**. The advantage held as the task grew. The review
also favored AIM's interface and code structure.

| Two assessment rounds | Luna + AIM | Luna alone |
| --- | ---: | ---: |
| Test 1: initial product score | **93.5/100** | **49.8/100** |
| Test 1: new search challenges with known solutions | **9/9** | **0/9** |
| Test 1: external machine checks | **123/123** | **1/123** |
| Test 2: upgraded product score | **93.5/100** | **62.8/100** |
| Test 2: new search challenges with known solutions | **8/8** | **1/8** |
| Test 2: external machine checks | **243/243** | **243/243** |

[Read the original test and its frozen evidence](aim-3.2-enigma-m3-case.md).
The upgrade assessment and its separate evidence follow below.

The study follows one pair of builds through two stages. The original
three-rotor stage is called M3; the four-rotor follow-up is called M4. These
names describe the machines being implemented, not different AI models.
Both builds used GPT-6 Luna at high reasoning effort.

The harder assignment made the product difference clear:

| Frozen M4 product outcome, assessed 1 October 2026 | Luna + AIM 3.2 | Luna alone |
| --- | ---: | ---: |
| Weighted product score, out of 100 | **93.5** | **62.8** |
| External M3/M4 machine vectors passed | **243/243** | **243/243** |
| New positive M4 search cases with a valid candidate | **8/8** | **1/8** |
| Returned M4 candidates validated against Py-Enigma | **32/32** | **22/23** |
| Same complete M4 search, median | **0.242 s** | **13.477 s** |

**A strong win for AIM in this pair.** Both simulators now pass the machine
vectors. AIM's advantage is the work users need next: finding valid settings,
opening them with the right inputs, and understanding the result. Its measured
complete M4 search runs **55.7× faster**. That is application search runtime.

AIM earned its process as the task grew. This result challenges the claim that
AIM adds only overhead: the extra delivery work accompanied a much better
functioning product on the new acceptance cases.

## What changed, and what the user received

The original brief asked for a local browser app that simulates Enigma I/M3 and
searches unknown start positions and plugboard pairs using a known plaintext
fragment, or crib. The common M4 follow-up added a stationary Beta/Gamma rotor,
three distinct moving rotors from I–VIII, thin reflectors, four rings and start
positions, and 0–10 plugboard pairs. M3 remains part of the contract. For M4
search, rotor order, reflector, rings and the Greek rotor's start are known;
the three moving starts and plugboard are unknown.

AIM found valid candidates in all eight new positive M4 cases: 0/1/3/6/10
plugboard pairs, known/unknown crib placement, and a later crib crossing rotor
stepping. Every returned AIM candidate checked against Py-Enigma was valid.
A partial plugboard can explain a crib without recovering the entire message;
the app makes that uncertainty visible.

Luna alone found valid candidates in one of those eight cases. Its own M4
example also works. Six new positive cases stop honestly at a complexity limit;
they are incomplete searches, not proven false zero-results. In the remaining
case, `step-crib`, it reports a candidate that does not match the crib. The
search constructs rotor mappings from the message start instead of the later
crib position, then returns the candidate without rejecting its mismatched
preview. The external replay verifies **22 of 23** returned candidates.

Candidate transfer also exposes a product difference: after a search, changing
the ring fields and opening an old result preserves the original search's
settings in AIM. Luna alone reads the newer form values and opens the wrong
configuration. AIM's saved search request has a clear owner in the code.

The review favors AIM's typography, hierarchy, grouping, explanations and
candidate status. Its machine, search, worker, search snapshot and views have
clearer responsibilities. These are reasoned UI and code assessments; the
functional and runtime results above are measured separately.

## A 55.7× faster complete application search

The benchmark is M4 `pairs-0`: Beta–VII–IV–V, B-Thin, rings QELP, no plugboard,
a 30-letter crib at offset zero and known Greek start M. Both apps fully check
**17,576 moving start positions** and return the same two valid candidates.
The candidate cap of 20 does not truncate either search.

| App | Warmup, s | Three measured runs, s | Median |
| --- | ---: | --- | ---: |
| Luna + AIM | 0.241 | 0.274 / 0.241 / 0.242 | **0.242 s** |
| Luna alone | 14.129 | 13.477 / 13.276 / 13.486 | **13.477 s** |

Runs alternated on the same Apple M5 Pro with Node 26.7.0, in separate
processes, with a 20-second limit. No run timed out. This measures the apps'
search cores in Node/V8; it does not measure browser animation or coding-agent
speed. Fast incomplete results do not qualify as a faster complete search.
The ratio applies to this workload. Process memory was not measured.

## Frozen M3 and M4 results stay separate

M4 is a follow-up to the same two products, not a new independent pair. Its
frozen versions contain changes made after the original M3 assessment.

| Assessment | Product scores, AIM / Luna alone | Machine vectors | New positive search cases | Complete search runtime ratios |
| --- | --- | --- | --- | --- |
| Original M3, 30 September | 93.5 / 49.8 | 123/123 / 1/123 | 9/9 / 0/9 | 40.9× and 14.5×, two M3 workloads |
| M4 follow-up, 1 October | 93.5 / 62.8 | 243/243 / 243/243 | 8/8 / 1/8 | 55.7×, one M4 workload |

Luna alone corrected its previous M3 ring/notch defect during the M4 change.
The earlier 1/123 result remains true of the original version; it does not
describe the current M4 simulator. [The frozen M3 case and its evidence](aim-3.2-enigma-m3-case.md)
retain the original scores, runtime measurements and candidate checks.

## Method and scoring

The M4 test plan was locked before the M4 source review, with the original
predeclared KPI weights. Both builders used GPT-6 Luna with high reasoning,
the same original PRD and the same M4 assignment. AIM included a separate Luna
reviewer. The PRD SHA-256 is
`59ab6a803dd15e40a68f20f56b2ffcc081b3a0ac60aec873f5c93c2d733a9493`.
The frozen manifest identifies 55 AIM files and 14 Luna-only files; the integrity
check records zero changed or missing originals. No product fixes were made by
the assessment.

| KPI | Weight | AIM, out of 10 | Luna alone, out of 10 |
| --- | ---: | ---: | ---: |
| Enigma correctness | 25% | 10.0 | 10.0 |
| Cracking and valid results | 30% | 9.5 | 3.0 |
| Other requirements | 15% | 9.0 | 7.5 |
| Performance and stability | 10% | 9.5 | 4.0 |
| Usability | 10% | 8.5 | 7.5 |
| Maintainability and test protection | 10% | 8.5 | 6.0 |

Weighted sums are 93.5 and 62.75, the latter rounded to 62.8. Product scores
were locked before cost assessment. The search budget defect primarily affects
cracking, transfer affects other requirements, and complete search time affects
performance. The same root cause is not deducted again for each symptom.
File count, framework choice and AIM documents do not earn points.

The 243 machine checks comprise 123 frozen M3 vectors and 120 new M4 vectors,
including ciphertext and final positions, Beta/Gamma, thin reflectors, varied
rings/plugboards and double notches. All reference data uses Py-Enigma 1.0.2.
Luna alone consulted Py-Enigma's rotor implementation during its M3 correction:
these tests establish conformance to a shared external reference. The eight new
positive search cases are generated outside the apps' examples, and every
returned candidate is checked against that reference after the search.

This is an AIM author's Codex-based product comparison. It is not an external
third-party audit. The result is a strong win for these frozen products; one
sequential pair cannot establish a general AIM advantage across models or tasks.

## Agent time and calculated token cost

The M4 agent passes lasted **30:44 with AIM and 19:53 without AIM**. Luna alone
submitted sooner, but its submitted version fails central search cases. Its
time to a product that passes those cases is unknown. Both runs were sequential,
under observed service slowness; elapsed time is not a controlled estimate of
the method's causal effect. AIM's prior pending M3 acceptance and longer thread
remain part of its actual conditions.

| M4 text-token calculation | Luna + AIM, including reviewer | Luna alone |
| --- | ---: | ---: |
| Uncached input tokens | 612,053 | 517,994 |
| Cached input tokens | 17,966,336 | 15,977,088 |
| Output tokens, including reasoning | 73,095 | 46,766 |
| Calculated Standard credits | 6.94 | 5.87 |
| API price equivalent | $0.277 | $0.235 |

The recorded rates are 2.5/0.25/12.5 Standard credits and
$0.10/$0.01/$0.50 per million uncached input/cached input/output tokens.
AIM's extra calculated M4 consumption is **1.06 Standard credits**, or
**about $0.042 in API price equivalent**. This is a calculation from logged
text tokens and the recorded rates, not a Codex subscription invoice. Cached
input and reasoning output are not counted twice. Tool fees and human time
are outside this calculation.

A shorter submission and roughly four cents less calculated consumption do not
establish a product win for a version missing the central search behavior.
Repair cost and time have not been measured. The M3 and M4 agent-pass totals
likewise measure consumed resources, not delivery of two equivalent products.

## Remaining scope and public evidence

Both apps retain the earlier Unicode normalization defect. AIM's 64-node
budget can leave other crib searches incomplete; eight successful cases are
not a guarantee for all possible M4 keys. Browser review covered desktop and
390×844 without horizontal overflow. Physical mobile, screen readers, detailed
keyboard navigation and UI cancellation during a long M4 search were not
retested. AIM's automated tests do not cover candidate transfer through the UI.
Future maintenance savings have not been measured with a new agent.

The public snapshot supports inspection and reference replay. Product source
and private chat logs are excluded, so it is not a complete app rebuild kit.
Absolute workstation paths and private session identifiers have been removed
from the manifest and token record; other copied result files retain their
bytes. The summary records source-report hashes and public payload hashes.

- [Summary, exact scores, runtime medians and payload hashes](evidence/2026-10-01-luna-aim32-enigma-m4/summary.json)
- [Locked M4 test plan and common assignment](evidence/2026-10-01-luna-aim32-enigma-m4/m4-testplan.md), [original PRD](evidence/2026-09-30-luna-aim32-enigma/enigma-prd.md)
- [120 M4 vectors](evidence/2026-10-01-luna-aim32-enigma-m4/m4-vectors.json), [123 frozen M3 vectors](evidence/2026-09-30-luna-aim32-enigma/vectors.json), [recorded machine results](evidence/2026-10-01-luna-aim32-enigma-m4/m4-known-answer-results.json)
- [M4 search inputs](evidence/2026-10-01-luna-aim32-enigma-m4/m4-cases.json) and [candidate validation](evidence/2026-10-01-luna-aim32-enigma-m4/m4-candidate-validation.json)
- [Benchmark run index](evidence/2026-10-01-luna-aim32-enigma-m4/benchmark.json): links warmup and all six scored runs
- [Search and cancellation result index](evidence/2026-10-01-luna-aim32-enigma-m4/search-results.md): links all 30 raw result files
- [Frozen file manifest](evidence/2026-10-01-luna-aim32-enigma-m4/m4-version-manifest.json), [original integrity check](evidence/2026-10-01-luna-aim32-enigma-m4/m4-original-integrity.json)
- [Token counts, recorded rates and calculation](evidence/2026-10-01-luna-aim32-enigma-m4/m4-token-cost.json)
- [Read-only replay script](evidence/2026-10-01-luna-aim32-enigma-m4/verify-reference.py): requires `py-enigma==1.0.2`; checks hashes, reference vectors, candidate validity, score arithmetic, medians and token calculation. It does not run either product or reproduce application timing.

Documentation: CC BY 4.0. Attribution: Jonas Eriksson, Agile Iteration Method.
