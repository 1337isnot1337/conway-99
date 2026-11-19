# First shared-row continuation: terminal resource limit

The bounded continuation returned five valid component-incidence
selections. Exact exterior-row certificates rejected all five. The
run stopped while encoding further proved cuts; it did not return
UNSAT and does not exclude component zero.

The conditional hypothesis remains a component-zero shell in a
globally prism-free and $F$-free split $18+18$ configuration. All 480
incidence selectors were free. The run fixed neither an incidence
design nor a second component or alignment.

## Recorded outcomes

The prepared limits were 20 incidence queries, ten seconds per SAT
query, 60 seconds per individual-row pass, 60 seconds per shared
LP, and 180 seconds overall. The encoding limits were one million
variables and two million clauses. The run stopped after 37.830083
seconds, with no time overrun.

| Iteration | SAT seconds | Exact individual obstructions | Exact row boxes | New individual cuts | New encoded shared cuts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.291211 | 1 | 59 | 12 | 0 |
| 1 | 0.017493 | 2 | 58 | 24 | 0 |
| 2 | 0.012400 | 4 | 56 | 48 | 0 |
| 3 | 0.019746 | 4 | 56 | 48 | 0 |
| 4 | 0.029260 | 0 | 60 | 0 | 8 |

Each candidate passed the exact original Gram, occupancy, and motif
checks and every cut present when it was generated. The first four
candidates yielded eleven integer row obstructions. Their twelve
verified core transports supplied 132 new individual-row cuts.
The 289 rational row boxes in the complete five passes were also
checked exactly. No numerical status alone supplied a cut.

The fifth selection passed all sixty individual row boxes. It then
reached the shared-edge test. That test has 1,223 eligible undirected
edges, 1,080 mixed equations, and sixty degree equations. Explicit
upper-bound slacks give 2,446 nonnegative variables and 2,363 rows.

The shared test returned an exact integer Farkas certificate with
right-hand side $-1$, 367 nonzero multipliers, and largest absolute
multiplier 28. The replay checks every primary and slack coefficient
and the strict negative right-hand side. Thus the fifth incidence
cannot support the required symmetric exterior graph, although its
sixty individual neighborhood boxes are all feasible.

## Universal cut and encoding stop

The row potentials were extended by zero to all 480 signatures.
The lift checks all 68,394 eligible signature pairs. It found 3,771
positive edge weights: 3,767 cross the saved selection boundary and
four lie inside it. The potential demand at the saved selection is
45, and its internal positive-edge capacity is 42. Dividing by the
coefficient gcd three gives a strict selector-cut gap of one.

The saved selection only chooses the support of the potentials and
the endpoint allocation. It is not a hypothesis of the inequality.
All twelve core transports are necessary for every incidence in this
component case. Their complete exact coefficients are saved in
`iteration04/symmetric-cut.json`, including the four transports that
were not inserted into the terminal CNF.

Each transported inequality has 454 nonzero coefficients. Its
positive-literal threshold is 331. The decision-graph encoder added
eight transports. The ninth exceeded the fixed variable limit and
was refused before any partial cut was added. The formula therefore
ends with 940,264 variables and 1,681,322 clauses. It contains 168
individual weighted cuts and twenty signed shared cuts, in addition
to the twelve earliest direct row cuts.

This stop identifies an encoding cost. It is not a mathematical
restriction, a SAT timeout, or a completed component search. The
complete proved registry contains 168 individual weighted cuts and
24 signed shared cuts. A later compact encoding can include the four
remaining transports without changing any inequality or hypothesis.

## Exact replay and files

The cold replay rebuilt the original component domain and formula,
checked every candidate against its actual cut prefix, replayed all
eleven integer row obstructions and 289 rational row boxes, checked
the shared Farkas certificate and all twelve transported inequalities,
and reconstructed the terminal CNF byte hash. It called no optimizer
or solver. No DRAT proof exists or is needed for this unresolved run.

The terminal CNF has 35,192,804 bytes and SHA256
`ed2ecaf317806b6a6d248d24daf3e7ca8b9b12445bf035af7a7e8300f773a42c`.
It is reproducible from the frozen source and cut transcript; the
publication manifest omits the raw CNF. The result file has SHA256
`03c7cfa9cfde1a23df0e3b3b2ffe6e1650801eaf5daf9e79a0403f45574fd20b`.

The run directory is
`experiments/logs/root-prism-free/f0-symmetric-row-loop-run01/`.
Its result, five candidate files, five row passes, shared certificate,
complete transported cut, and retained registries are all preserved.
The separate cold result is
`f0-symmetric-row-loop-run01-cold-replay.json`.

The source and initial preparation remain those in
`root_prism_free_f0_symmetric_row_loop.md`. This terminal package
does not modify them or any earlier result. No unrestricted graph,
second component completion, or component exclusion was obtained.
