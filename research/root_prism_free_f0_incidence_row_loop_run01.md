# Terminal result of the first incidence and row loop

The loop stopped after its first SAT incidence. Every one of the 60
selected exterior rows has an exact rational box witness. There was
no retained row obstruction and no further incidence query. Cold
replay reproduced the formula and checked the incidence, all current
cuts, and all 60 rational witnesses.

This selection satisfies the entire family of single-row potential
inequalities. It does not specify a symmetric exterior graph or a
Conway99 graph.

## Recorded outcome

| Item | Outcome |
| --- | --- |
| Incidence queries | 1 |
| SAT call | 0.008376 seconds |
| Initial loading, checks and bootstrap | 1.149400 seconds |
| Total loop duration | 2.660569 seconds |
| Selected signatures | 60 distinct triples |
| Exact row boxes | 60 |
| Exact row obstructions | 0 |
| New weighted cuts | 0 |
| Stop reason | Complete row pass with no retained obstruction |
| Cold formula and witness replay | Passed |

The initial and final formulas are identical: 40,932 variables and
78,222 clauses, with SHA256
`14a4d6774f1691c1000405c2e30b50f9c83463eb7ae559510415d94a38cc849e`.
The formula contains all original incidence constraints, the 12 earlier
row cuts, and the 36 full weighted inequalities used to seed the loop.

The result is
`experiments/logs/root-prism-free/f0-incidence-row-loop-run01/result.json`,
SHA256
`4af22d0933e676079ca376c87c498add890c406d3f1b1751e473951d01f24098`.
The full selected incidence is in `iteration00/candidate.json`, SHA256
`9e38e41273ad247021854236a56a4e9dd0cdc74b7156867904b7d19fe2d64e46`.

## What the row certificates prove

For each selected target $a$, the saved rational numbers satisfy

$$
\sum_{b\in N(a)\cap S}h_b y_{ab}=q_a,
\qquad 0\leq y_{ab}\leq1,
\qquad\sum_b y_{ab}=8.
$$

All 18 equations and every bound hold exactly. Therefore, for every
integer or real potential $v$,

$$
v^Tq_a
=\sum_b(v^Th_b)y_{ab}
\leq\sum_{b\in N(a)\cap S}\max(v^Th_b,0).
$$

No potential can produce a strict single-row capacity gap against this
selection. For an unselected target, every guarded inequality with
positive demand holds because its left side is nonnegative. Thus the
complete potential-cut family is satisfied by this particular
480-selector point, including all core transports. This closes the
single-row separation approach at this point; it does not settle the
remaining graph constraints.

Eleven saved row witnesses are binary; seven of those also obey the
pairwise triple-intersection packing test. The other 49 witnesses are
fractional. Their denominator distribution is:

| Denominator | Rows |
| --- | ---: |
| 1 | 11 |
| 2 | 13 |
| 3 | 10 |
| 4 | 8 |
| 5 | 7 |
| 6 | 4 |
| 7 | 1 |
| 8 | 2 |
| 9 | 1 |
| 12 | 2 |
| 17 | 1 |

The saved rows are independent witnesses. They disagree under
transposition at 588 unordered exterior pairs. This does not show
that symmetric witnesses are impossible; it shows that these saved
rows themselves do not define one. The selected design has 1,220
eligible undirected exterior edges, which form the domain of a
separate symmetric completion test.

## Verification and scope

The terminal cold replay is
`experiments/logs/root-prism-free/f0-incidence-row-loop-run01-cold-replay.json`,
SHA256
`8640b7b338277389966a0097d4496f04dcbf4da286fccc8f3f8917d7f245453a`.
It reconstructed the complete component domain and both formula
hashes, inspected the selected incidence against the correct cut
prefix, and checked every exact row box. It called no optimizer or
SAT solver.

The search stayed within all declared limits and did not invoke the
fresh UNSAT proof wrapper. The final CNF is also saved as a
deterministic gzip artifact whose decompressed bytes have the formula
hash above.

The hypothesis remains component zero in the globally prism-free and
$F$-free split $18+18$ shell. The second component and its incidence
are unspecified. No component, incidence selection, or graph is
excluded by this terminal result. A symmetric exterior model is
separate work and is not included here.
