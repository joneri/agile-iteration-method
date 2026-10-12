# Frozen M4 search results

Run 1 is the functional run and benchmark warmup; runs 2–4 of `pairs-0` are
the scored benchmark measurements. `cancel` is the separately interrupted run.

| Variant | Case | Run | Status | Checked starts | Returned | Seconds |
| --- | --- | --- | --- | ---: | ---: | ---: |
| aim | impossible | [1](m4-search-aim-impossible-1.json) | impossible | 0 | 0 | 0 |
| aim | multiple | [1](m4-search-aim-multiple-1.json) | complete | 17576 | 20 | 0.185 |
| aim | none | [1](m4-search-aim-none-1.json) | complete | 17576 | 0 | 1.478 |
| aim | offset-auto | [1](m4-search-aim-offset-auto-1.json) | complete | 17576 | 2 | 2.213 |
| aim | offset-known | [1](m4-search-aim-offset-known-1.json) | complete | 17576 | 2 | 1.299 |
| aim | pairs-0 | [1](m4-search-aim-pairs-0-1.json) | complete | 17576 | 2 | 0.241 |
| aim | pairs-0 | [2](m4-search-aim-pairs-0-2.json) | complete | 17576 | 2 | 0.274 |
| aim | pairs-0 | [3](m4-search-aim-pairs-0-3.json) | complete | 17576 | 2 | 0.241 |
| aim | pairs-0 | [4](m4-search-aim-pairs-0-4.json) | complete | 17576 | 2 | 0.242 |
| aim | pairs-0 | [None](m4-search-aim-pairs-0-cancel.json) | incomplete | 0 | 0 | 0.066 |
| aim | pairs-1 | [1](m4-search-aim-pairs-1-1.json) | complete | 17576 | 2 | 0.271 |
| aim | pairs-10 | [1](m4-search-aim-pairs-10-1.json) | complete | 17576 | 1 | 0.283 |
| aim | pairs-3 | [1](m4-search-aim-pairs-3-1.json) | complete | 17576 | 1 | 0.259 |
| aim | pairs-6 | [1](m4-search-aim-pairs-6-1.json) | complete | 17576 | 1 | 0.276 |
| aim | step-crib | [1](m4-search-aim-step-crib-1.json) | complete | 17576 | 1 | 0.283 |
| naked | impossible | [1](m4-search-naked-impossible-1.json) | complete | 0 | 0 | 0 |
| naked | multiple | [1](m4-search-naked-multiple-1.json) | result_limit | 19 | 20 | 0.002 |
| naked | none | [1](m4-search-naked-none-1.json) | complexity_limit | 0 | 0 | 0.004 |
| naked | offset-auto | [1](m4-search-naked-offset-auto-1.json) | complexity_limit | 0 | 0 | 0.003 |
| naked | offset-known | [1](m4-search-naked-offset-known-1.json) | complexity_limit | 0 | 0 | 0.004 |
| naked | pairs-0 | [1](m4-search-naked-pairs-0-1.json) | complete | 17576 | 2 | 14.129 |
| naked | pairs-0 | [2](m4-search-naked-pairs-0-2.json) | complete | 17576 | 2 | 13.477 |
| naked | pairs-0 | [3](m4-search-naked-pairs-0-3.json) | complete | 17576 | 2 | 13.276 |
| naked | pairs-0 | [4](m4-search-naked-pairs-0-4.json) | complete | 17576 | 2 | 13.486 |
| naked | pairs-0 | [None](m4-search-naked-pairs-0-cancel.json) | cancelled | 21 | 0 | 0.02 |
| naked | pairs-1 | [1](m4-search-naked-pairs-1-1.json) | complexity_limit | 0 | 0 | 0.002 |
| naked | pairs-10 | [1](m4-search-naked-pairs-10-1.json) | complexity_limit | 0 | 0 | 0.003 |
| naked | pairs-3 | [1](m4-search-naked-pairs-3-1.json) | complexity_limit | 1471 | 0 | 1.553 |
| naked | pairs-6 | [1](m4-search-naked-pairs-6-1.json) | complexity_limit | 0 | 0 | 0.003 |
| naked | step-crib | [1](m4-search-naked-step-crib-1.json) | complete | 17576 | 1 | 6.015 |
