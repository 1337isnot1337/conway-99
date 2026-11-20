# Two-round parity-discovery continuation

The authorized continuation completed in 102.834132 seconds. It made two native
LP calls, using 4.142286305 cumulative native seconds, and stopped with case 4
unresolved. Both new rational points passed separate full exact replay. One new
58-coordinate parity cover was independently certified and added.

| Stage | Exact point denominator | Positive max-min numerator | Accepted rows |
| --- | ---: | ---: | ---: |
| After the two saved covers | 721,941,453 | 7,871,053 | 167,117 |
| After the new 58-coordinate cover | 67,336,409,858 | 732,404,911 | 167,118 |

Each numerator is divided by its row's denominator. Both points satisfy every
original native row, every original coordinate cover, all 112 proved zero
coordinates, the inherited parity equalities and cuts, and every cut registered
before that point. All 1,102 surviving selectors are strictly positive.

## The new cover

At the first point, discovery found an odd-support cover from original Gram
rows 62, 102, 117, 118, 119, 121, 122, 123, 124, 127, 158, 188, 321, 433, 452,
and 470. Their right-hand sides sum to 25. With the proved zero coordinates
removed, their full integer coefficient sum has the form

\[
\sum_{a\in S}x_a+2\sum_a\lfloor c_a/2\rfloor x_a=25,
\qquad c_a\ge0.
\]

The odd support S has 58 coordinates. For nonnegative integer selectors its sum
is odd and at least one. The first point violates this cover by
187,056,174 / 721,941,453. The complete original coefficient vector, support,
and source-point witness are saved in `discovery-00/cut-00.json`. A separate
proof-only stage checked the original Gram identity and exact deficit in
0.057052 seconds. The signed row appended to the LP is
\(-\sum_{a\in S}x_a\le-1\), with its unit-box lower bound.

The first discovery visited all 123,123 positions in its ordered iterator,
including 82,073 distinct equations, and retained this one cut. The second
discovery, at the second accepted point, visited the same number of raw
positions, including 82,072 distinct equations, and retained no cut. The two
discoveries took 15.962 and 14.208 seconds. These are the owner-recorded search
statistics. The separate acceptance stage checked only complete cut proofs;
it did not independently replay either full candidate family or certify
exhaustion.

The final registry contains exactly the initial two saved covers and this one
new cover. The final point passes all three. There is no later rejecting cut
outside that point's accepted prefix. The final bindings-only audit checked
68 stage-artifact references and this prefix relationship without another
scan, solve, or point-arithmetic pass.

## Preserved launch error and scope

The first invocation used a mistyped preparation path and failed before it
could load the mathematical preparation or create a numerical/search stage.
Its three logs and zero-call record remain under the separate run01 name. The
corrected invocation used a new run02 directory and unchanged frozen sources,
inputs and resource limits.

The terminal status is `UNRESOLVED: no checked new cut from bounded discovery`.
The rational point certifies feasibility of the stated real relaxation. It is
not a Boolean incidence, a 99-vertex graph, or a global feasibility certificate.
The continuation proves no new zero coordinate and no case-4 exclusion.
