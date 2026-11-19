# Complete intrinsic row census for case4

## Result

The complete census over all 1,214 optional attachment columns of indexed
35-core case4 gives 14 elementary target exclusions. Twelve are additional to
the two previously saved explicit unit certificates. Every target passes the
separate GF(2) and GF(3) span tests.

The excluded zero-based columns are

\[
352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167.
\]

The previously saved explicit units are 1080 and 1081. This comparison concerns
the saved unit conclusions; no implication test against the entire earlier
Boolean formula was performed. Case4 and the first local set remain unresolved.

The source is
`experiments/workspace/complement_rook_35core_case0004_intrinsic_rows.py`,
with SHA-256
`24eb86e47e6f5a741721fe9174e7d3762bc74edd290c89d489dd5ddedb900c11`.
The complete compressed certificate has SHA-256
`0d1c096865678958737e34551fb55a203fd65b9dc8b0b5613bd9f1dfd26185e9`.
It occupies 104,269 bytes. A fresh complete replay passed.

## Complete row domain

For each admitted core column h_a, define

\[
t_a=(2\mathbf1-h_a-Bh_a,\ 14-|h_a|),\qquad w_b=(h_b,1).
\]

If a occurs in a graph completion, its exterior neighbors satisfy

\[
t_a=\sum_{b\sim a}w_b.
\tag{1}
\]

The census reconstructs all 1,214 target vectors from the fixed 35-core and
the frozen complete column domain. It tests all 736,291 unordered pairs of
optional columns for the necessary edge conditions: at most one shared core
neighbor and both endpoint zero-quota tests. The result is exactly the saved
275,578 eligible unordered edges, or 551,156 directed neighbor entries.

No incidence point is fixed. No numerical proposal, LP, SAT solver, or graph
automorphism assumption enters this census.

## Support dominance

For a fixed target a and coordinate i, let

\[
S_i(a)=\{b:\ b\text{ is eligible for }a,\ w_b(i)=1\}.
\]

There are 35 incidence coordinates and one degree coordinate. If
S_i(a) is contained in S_j(a), equation (1) requires t_a(i) at most t_a(j).
A strict reverse inequality therefore excludes the target column. The same
conclusion follows from the integer potential e_i minus e_j.

All 1,573,344 ordered coordinate comparisons were covered, including the
vacuous diagonal comparisons. Exactly 14 comparisons give exclusions, one
per excluded target. Every witness compares two mixed coordinates and has
t_a(i)=2 and t_a(j)=1.

Core coordinates 0 through 8 are R0 through R8; coordinates 9 through 17 are
S0 through S8. The exact witnesses are:

| Target columns | Smaller neighbor support | Larger neighbor support | Required counts |
| --- | --- | --- | --- |
| 352, 353, 354, 355 | R6 | S2 | 2 versus 1 |
| 439 | R2 | S6 | 2 versus 1 |
| 552, 553 | R6 | S1 | 2 versus 1 |
| 645 | R1 | S6 | 2 versus 1 |
| 869, 873 | R3 | S2 | 2 versus 1 |
| 957 | R2 | S3 | 2 versus 1 |
| 1080, 1081 | R3 | S1 | 2 versus 1 |
| 1167 | R1 | S3 | 2 versus 1 |

For each witness, every eligible neighbor is checked directly. The conclusion
already holds for nonnegative neighbor weights in (1), so it does not require
an integer or Boolean neighbor search.

## Finite-field tests

Reducing (1) modulo a prime p requires t_a to belong to the linear span of all
eligible w_b over GF(p). The span test is necessary even when an arbitrary
field combination differs from a legal zero-one neighbor selection.

The census performs exact Gaussian elimination over both GF(2) and GF(3).
It carries provenance through elimination. A passing test saves an explicit
combination of eligible neighbor columns whose coordinate sum equals t_a
modulo p. An unsuccessful test would instead save a vector v with

\[
v\cdot w_b=0\quad\text{for every eligible }b,
\qquad v\cdot t_a=1\pmod p.
\]

All 1,214 targets pass in each field. The certificate contains all 2,428
positive combinations. Each is separately checked using ordinary integer
coordinate sums, independent of the packed elimination operations. The largest
combination uses 23 neighbors over GF(2) and 27 over GF(3). There are no parity
dual exclusions.

Both fields give the same rank distribution:

| Rank | Targets |
| ---: | ---: |
| 22 | 4 |
| 23 | 23 |
| 24 | 108 |
| 25 | 178 |
| 26 | 252 |
| 27 | 251 |
| 28 | 292 |
| 29 | 90 |
| 30 | 16 |

Elimination may stop early only when it reaches a proved ambient rank bound.
Every zero mixed target coordinate is zero on every eligible column. In
addition, each column meets each of the three nine-point bases once, giving
three independent relations equating those base sums with the degree
coordinate. Each base has a nonzero allowed coordinate, so the three relations
remain independent after deleting the zero coordinates. Over either field the
rank is therefore at most 36 minus the number of zero mixed coordinates minus
3. The target satisfies the same relations. If elimination does not reach
this bound, it processes the complete neighbor list.

## Arithmetic controls and replay

The GF(2) implementation was checked on all subsets of the seven nonzero
three-dimensional binary vectors and all eight targets: 1,024 span and witness
cases. The GF(3) two-plane arithmetic was checked against all 729 pairs of
three-dimensional ternary vectors. A separate explicit reachable-set
enumeration checked 10,314 ternary span and witness cases, including empty,
dependent, and full-rank generator families.

The complete census took 5.199 seconds with peak RSS 42,684 KiB. These are
execution measurements, not a complexity guarantee. The full cold replay
reconstructs the domain, all ordered comparisons, and every finite-field
certificate; it makes no optimizer or solver call.

From the repository root, replay to a new path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_intrinsic_rows.py \
  --replay experiments/logs/grids-and-triangles/complement-rook-35core-case0004-intrinsic-rows.json.gz \
  --output /tmp/conway99-case4-intrinsic-rows-replay.json \
  --seconds 120
```

The artifact manifest is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-intrinsic-rows-artifacts.json`.
This checkpoint does not alter the earlier Boolean formula or run another
case4 query.
