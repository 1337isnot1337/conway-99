# Three-selector scan at the Schur/path numerical proposal

The scan gives no new inequality. It examines all 42 representative anchors
for both Boolean three-selector families. The 258 published common-core-pair
edge-clique rows also pass exact evaluation at this numerical proposal.
These results do not prove feasibility of the complete F0 model.

## Point and formulas

The point is the lossless output of the single Schur/path query:
`experiments/logs/root-prism-free/f0-schur-path-query-run01/numerical.json`,
SHA256 `bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e`.
Its 15,200 binary floating coordinates have exact common denominator
`147573952589676412928`. The query reports numerical optimality; no exact
primal point or contradiction was obtained.

For three distinct Boolean selectors, the necessary expectation rows are

`Z_ab + Z_bc - Z_ac <= x_b`,

`x_a + x_b + x_c - Z_ab - Z_ac - Z_bc <= 1`.

The first slack is `ac` when `b=0`, and `(1-a)(1-c)` when `b=1`.
The second slack is one exactly when all three bits agree. Both are
nonnegative. Quotient coefficients are added when variables coincide;
only the 389 previously proved zero pair coordinates are removed.

The [point-independent preparation](root_prism_free_f0_three_selector_inequalities.md)
checks the actual twelve core actions and their selector/pair orbits.
Moving an anchor to one of 42 representatives covers every literal row.
No automorphism of the unknown completed graph is assumed.

## Finite scan and result

Each family has `42 * binom(479,2) = 4808202` array evaluations.
The plan selects at most eight numerical candidates per anchor and family,
then accepts only exact positive dyadic gaps. It retains at most 64 new
coefficient rows per family, excluding rows already present in the parent.
All anchors finish in 4.849 seconds, within the 30-second cooperative limit.

Neither family supplies a positive numerical candidate. The largest reported
triangle gap is approximately `-0.0074486303691`; the largest perimeter gap
is approximately `-0.0912370178197`. These are numerical scan results.
The run does not claim exact evaluation of every unretained row.

All 258 core-pair clique rows are evaluated with Python integers at the
exact dyadic coordinates. Every gap is nonpositive. The largest is
approximately `-0.00742643431879`. A separate 4.674-second replay reproduces
all 258 exact gaps and verifies the empty retained-cut record. It does not
repeat or independently certify the numerical maxima.

## Records and continuation

The source is `experiments/workspace/root_prism_free_f0_three_selector_scan.py`,
SHA256 `def73142c54ea432589ba05d9f9f1d1f3378676786c661928986d2eeae05bf50`.
An independent full-source review checks the literal mapping, broadcasting,
candidate caps, exact denominator construction and replay scope.
The preparation includes 240 small array/formula comparisons.

The result is `experiments/logs/root-prism-free/f0-three-selector-scan01.json`,
SHA256 `2a288d6298a2084b4179e1d3976c6808580de2731ade8102edd4c5f26f15fc01`.
The preparation, summary, exact replay and independent review are adjacent
files. All sources and inputs are hash-bound.

Adding only these already satisfied clique rows cannot reject this proposal.
No such optimizer repeat is scheduled. The next targets are the full current
selector and graph-Schur PSD blocks, and stronger local conflict cliques.
The graph-existence problem remains unresolved.
