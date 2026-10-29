# Bounded tool-result witness

Checked 2026-10-29 in a Codex desktop session exposing `functions.exec` and
OpenAI Docs MCP. This is one representative instruction-contract witness, not
a provider benchmark or evidence of general agent compliance.

The runnable synthetic example is `tests/fixtures/tool_efficiency/recipe.py`;
run `python3 -m unittest discover -s tests -p test_tool_efficiency.py`.
It generates 1,000 issue records. Literal expected relevant IDs are ISSUE-7,
ISSUE-42 and contrary ISSUE-99. The tests also move counterevidence to the end,
add a new relevant contrary record, reject missing evidence, retain the failed
secondary branch and page-2 cursor, and exercise effect ordering and unknown
outcome handling with isolated fake effects. The no-capability fallback is an
ordinary bounded source-call example, not a claim that a provider was disabled.

| Snapshot | Replayed raw-result bytes | Serialized selected result bytes |
| --- | ---: | ---: |
| Synthetic issue response | 531,590 | 798 |
| One native OpenAI Docs MCP response | 38,013 | 707 |

Both comparisons use the same retained raw snapshot for baseline and projection;
the full baseline was not emitted to model context. The synthetic projection's
raw reference is included in its size. Values are UTF-8 compact JSON sizes, not
token counts. Paths/identifiers in a different run can change the exact counts.

`native-witness.json` records the actual native call and emitted projection. The
program obtained the documentation through the MCP tool, checked the four
required evidence topics, retained the full tool response locally and emitted
only routing/evidence requirements, source URL, omissions and raw reference.
The necessary local raw snapshot is retained at
`.aim/analysis/tool-efficiency/native-mcp-raw.json`; the witness records its
SHA-256. It is review evidence in this worktree, not an extra installed resource.
The public original can be inspected at the source URL, but a later fetch is
not guaranteed to reproduce the recorded snapshot. Synthetic raw/effect/check
observations and the native gate records also remain under `.aim/analysis/`.

The first native program failed after the successful fetch because `TextEncoder`
was unavailable in the host V8 runtime. Recovery reused that response without
another provider call. The report retains this failure, two outer programs,
one nested MCP fetch and one raw-retention call. Code/retention arguments are
extra traffic; the smaller selected result does not establish fewer whole-run
bytes, model steps, tokens, elapsed time or subscription cost. Those unavailable
measurements remain unknown. No side effect was replayed and no external write
was performed. Existing AIM traces can measure observable call envelopes but
cannot automatically count nested operations or model inference steps.

The fixture demonstrates the recipe's behavior. Canonical instructions and
packaged route availability require separate review and distribution checks;
passing these tests alone cannot prove what every host or model will do.
