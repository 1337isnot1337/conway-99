# Coordinate-cover case4 query: UNKNOWN

## Terminal result

The single authorized query returned UNKNOWN. It loaded the complete
134,852-variable, 439,604-clause formula and reached the 60-second limit
without a SAT point or an UNSAT proof. Indexed 35-core case4 remains open.
There was no retry.

| Measurement | Value |
| --- | ---: |
| Clauses loaded | 439,604 |
| Loading time | 5.049 seconds |
| Solver return from start of loading | 60.022 seconds |
| Total query-wrapper time | 60.066 seconds |
| Peak process RSS | 142,060 KiB |
| Conflicts | 29,702 |
| Decisions | 94,099 |
| Propagations | 89,224,516 |

Loading counted inside the 60-second limit. The solver was fresh, with no
assumptions, phase preferences, extra clauses or retries. Its formula had
the exact prepared SHA-256
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.

The result is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-run01/result.json`.
The adjacent cold replay reconstructs the full attachment domain, original
formula, thirty Gram conflicts, sixty integer row cuts, complete coordinate
ledger and streamed CNF before checking the result binding. No proof checker
is called for UNKNOWN, because no UNSAT proof was obtained.

The preparation and exact cover theorem remain valid. In particular, the
fourteen target exclusions remain proved, and all 178,533 retained cover
clauses remain necessary. This query supplies no further exclusion. It also
does not supply a feasible incidence point.

## What this query leaves untested

The coordinate covers test one positive coordinate difference at a time and
weaken demands above one. Even the sixty earlier general row cuts test only
the saved potentials. Neither family proves that any remaining target has a
feasible entire exterior neighborhood.

A concrete next test is therefore the intrinsic neighborhood problem for
one optional target a, before another whole case4 query. All candidate
neighbor columns remain available. The variables y_b would satisfy

\[
\sum_b w_b y_b=t_a,\qquad 0\le y_b\le1.
\tag{1}
\]

Two further necessary capacities can be imposed without a full exterior
graph. Columns with the same original 27-core signature form an
at-most-one family. Also, for each pair of core vertices i,j, the chosen
neighbors containing both i and j form an at-most-one family. Two such
neighbors would otherwise have common neighbors i,j and a, contrary to the
global common-neighbor bound of two.

These are feasibility constraints on one target row. A feasible point is
only a local relaxation; it does not extend the incidence to a graph.
An exact infeasibility certificate could exclude the target independently
of any numerical incidence proposal. No such test is executed in this
checkpoint.

## Exact form of a possible row certificate

Let F range over any of the valid at-most-one families above. In an actual
completion, with source indicator x_a and neighbor indicators y_ab,

\[
\sum_{b\in F}y_{ab}\le x_a.
\]

Choose a rational potential v on the 36 mixed/degree coordinates and
nonnegative rational multipliers gamma_F. Define

\[
\delta=v\mathbin{\cdot}t_a-\sum_F\gamma_F,
\qquad
c_b=\max\!\left(v\mathbin{\cdot}w_b-
              \sum_{F\ni b}\gamma_F,\ 0\right).
\]

Then every completion satisfies

\[
\delta x_a\le\sum_b c_bx_b.
\tag{2}
\]

Indeed, write v dot t_a x_a as the sum of v dot w_b times y_ab,
subtract the family multipliers from each coefficient, discard negative
residual coefficients, use y_ab at most x_b, and use each family capacity.
After clearing a positive common denominator, all entries can be checked by
integer arithmetic on the complete frozen row domain.

If delta exceeds the sum of the c_b over every available candidate, (2)
forces x_a=0. Known absent candidates can be removed when their unit proofs
are explicitly bound. A numerical LP may propose v and gamma, but only the
complete exact coefficient and sign check would establish a new condition.
This proposal adds no cut to the frozen formula and makes no claim that a
new exclusion exists.
