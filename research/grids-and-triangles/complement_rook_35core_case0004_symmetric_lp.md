# A shared exterior-edge LP for case 4

The preparation has 276,792 nonnegative variables, 590,165 rows, and
4,121,379 matrix entries. It has not been optimized. It retains every
original incidence constraint, the 30 checked binary Gram no-goods, and
all 60 checked exterior-row inequalities.

## Variables and exact equations

There are 1,214 real selector variables \(x_a\), one for each complete
attachment column \(h_a\). There is one variable \(y_{ab}\) for each of
the 275,578 eligible unordered exterior pairs. This same variable occurs
in the rows of both endpoints. The model imposes

\[
0\le y_{ab}\le x_a,\qquad y_{ab}\le x_b.
\]

For each column \(a\), all mixed and degree equations are

\[
\sum_{b:\{a,b\}\in E}h_b(i)y_{ab}=q_a(i)x_a
\quad(0\le i<35),
\]

\[
\sum_{b:\{a,b\}\in E}y_{ab}=d_ax_a,
\qquad q_a=2\mathbf1-h_a-Bh_a,
\qquad d_a=14-|h_a|.
\]

Every actual completion supplies a binary solution. The LP relaxes these
variables to real values. Sharing \(y_{ab}\) adds consistency between the
two endpoint rows; it imposes no equality between unrelated edges and
uses no graph automorphism assumption.

The row identity has 42,490 mixed positions and 1,214 degree positions.
Exactly 6,594 mixed positions are identities \(0=0\): their quota is
zero and the complete eligible domain has no contributing neighbor.
Only these identities are omitted. Every positive mixed quota has at
least one possible neighbor. No column is removed during preparation.

## Complete inventory

| Row family | Rows | Nonzero entries |
|---|---:|---:|
| Original Gram equalities | 397 | 14,986 |
| Original-signature capacities | 186 | 1,198 |
| Additional triple capacities | 12 | 208 |
| Selector upper bounds | 1,214 | 1,214 |
| Checked binary Gram no-goods | 30 | 60 |
| Checked exterior-row inequalities | 60 | 4,324 |
| Mixed exterior equations | 35,896 | 2,444,707 |
| Exterior degree equations | 1,214 | 552,370 |
| First-endpoint activation | 275,578 | 551,156 |
| Second-endpoint activation | 275,578 | 551,156 |
| **Total** | **590,165** | **4,121,379** |

The totals split into 37,507 equalities and 552,658 upper inequalities.
All variables are nonnegative. The retained selector bounds and endpoint
activation imply upper bound one for every edge variable, so no separate
edge upper-bound rows are needed.

The largest absolute integer coefficient is 1,217. All coefficients and
bounds are exactly representable as float64 values; this says nothing
about the accuracy of a future numerical solution.

If every upper inequality is converted to an equality using a distinct
nonnegative slack, the standard form has 829,450 variables and 4,674,037
nonzero entries. There is no reason to materialize those slacks merely
to pass the general-row LP to a solver.

## Sparse storage

The exact array inventory is:

| Arrays | Bytes |
|---|---:|
| Float64/int32 CSC matrix | 50,563,720 |
| Float64/int64 CSC matrix | 68,156,408 |
| Costs and column/row bounds | 16,085,648 |
| Optional float64/int32 COO construction arrays | 65,942,064 |
| Int32 CSC plus costs/bounds | 66,649,368 |
| COO plus int32 CSC plus costs/bounds | 132,591,432 |

These are array-storage counts. They exclude Python objects, solver
copies, presolve data, and factorization memory. They are not a memory
bound for solving the LP.

Preparation streamed the complete exact row sequence in 16.35 seconds.
Its observed peak RSS was 123,296 KiB. It did not allocate a solver
matrix or call an optimizer. The compressed preparation contains every
eligible unordered pair, with its deterministic variable index.

## Controls and exact binding

A known rook graph supplies a positive control for all mixed equations,
degree equations, and both endpoint inequalities. Each shared edge is
checked to contribute once to each endpoint degree.

A separate three-vertex path control shows why sharing variables can add
information. Independent unit-degree row boxes are feasible at all three
vertices. Shared variables would require both path edges to be one from
the endpoint equations, while the middle equation requires their sum to
be one. This is only an algebraic control, not a claimed Conway core.

The entire physical row stream is hashed using little-endian signed
64-bit records of the form
`sense, rhs, nnz, (column, coefficient)*`. Sense zero means equality and
sense one means an upper inequality. Its SHA256 is

```text
233c802009571ad234596e4eb3bd78f3cda55dda6808102d314fa487b8fa049a
```

The source is
`experiments/workspace/complement_rook_35core_case0004_symmetric_lp.py`.
The complete preparation is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-preparation.json.gz`.

An optimizer-free complete reconstruction can be requested with:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_symmetric_lp.py \
  --replay experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-preparation.json.gz \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-replay-new.json
```

No exterior common-neighbor pair caps are added at this stage. A feasible
LP point would remain only a fractional relaxation. An exclusion would
require an exact infeasibility certificate. The 60-cut SAT option remains
available from the frozen integer inequalities, but this package neither
encodes nor queries it.
