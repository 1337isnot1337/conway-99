# Center 355: exact local Boolean witness

The single proof-enabled pilot returned SAT. It used 0.023861208 seconds
for solver initialization, search and exact verification, and 2.203710908
seconds including the fresh model reconstruction. There was one production
solver call and no timeout.

The exact eight-neighbor set is:

| Signature ID | Component sites |
|---:|---|
| 69 | 0, 14, 17 |
| 73 | 1, 2, 8 |
| 174 | 2, 7, 17 |
| 201 | 3, 4, 7 |
| 212 | 3, 5, 12 |
| 284 | 4, 10, 12 |
| 435 | 9, 10, 15 |
| 475 | 11, 14, 15 |

Its eighteen mixed counts are

\[
(1,1,2,2,2,1,0,2,1,1,2,1,2,0,2,2,0,2).
\]

Every one of the 16,105 CNF clauses passes. The native check verifies the
eighteen exact demands, population eight, all 5,495 conflicts and all
435 common-neighbor caps in the explicit thirty-vertex partial graph.
The primitive neighbor bits remain distinct.

A separate cold replay rebuilt the exact native model and CNF, then
rechecked the stored assignment and native witness without another solve.
It passed in 1.864205150 seconds.

The run record is
`experiments/logs/root-prism-free/f0-local-center355-pilot01/result.json`,
SHA256
`691770408d6af35c86cd06004344b51159dbd6ba8ceafd2b185b5764ee37cd0e`.
The stored solver assignment has SHA256
`d7ca2777d38f90365f9583d043ee183da3c0878779615a9a02329695e56e5fff`.
The cold replay is
`experiments/logs/root-prism-free/f0-local-center355-pilot01-replay/result.json`,
SHA256
`d7f61ccc7b2916d545fab07443104fe8d01a9b71368248ed063fb1361730b217`.

This result shows that the tested local projection cannot exclude
signature 355. It supplies neither a complete sixty-vertex incidence
design nor an SRG completion. In particular, the matching required inside
the center's full fourteen-neighbor set was not imposed in this pilot.
No other center was queried.
