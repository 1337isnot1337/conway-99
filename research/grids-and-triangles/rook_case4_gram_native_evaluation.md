# Stronger native constraints reject the recovered case4 Gram point

The exact rational Gram point from `rook_case4_exact_gram_point.md` is not a
feasible point of the later native selector relaxation.

An optimizer-free integer evaluation checked every published row, using the
common denominator648602182798933000000000000.

| Family | Rows checked | Violations |
| --- | ---: | ---: |
| Gram equations | 630 | 0 |
| Original-signature capacities | 186 | 0 |
| Core-triple capacities | 1365 | 1 |
| Binary Gram no-goods | 30 | 0 |
| Uncapped exterior-row inequalities | 60 | 21 |
| Earlier proved zero units | 14 | 0 |

The single violated triple capacity has index710 and core sites{8,10,29}.
Its exact excess over1 is

```text
1945650185977812 / 648602182798933000000000000.
```

The violated exterior-row inequalities have indices2 through22, inclusive,
with targets

```text
139,143,199,220,281,434,449,582,606,638,674,
694,698,706,820,905,917,997,1119,1122,1179.
```

The saved result lists every exact left side, right side and positive
difference. Both initial cuts0 and1 pass; all cuts23 through59 also pass.

The tiny triple violation reflects the explicit rational choice of the
two free coordinates. No inference about other choices on that support
follows. A two-dimensional repair was assessed but not implemented.
The current work instead reconstructs the complete selector relaxation
from public inputs, preserving every optional column not already proved zero.

This evaluation does not check the full coordinate-cover registry and does
not prove case4 impossible. It establishes that Gram feasibility does not
settle the stronger selector relaxation.

The source is `experiments/workspace/rook_case4_gram_native_evaluation.js`.
It binds the raw published native model and the raw exact Gram result,
uses BigInt arithmetic throughout the evaluation, and performs no new
reconstruction, optimizer call or support search. A fresh invocation of
that source reproduced all22 violations.
