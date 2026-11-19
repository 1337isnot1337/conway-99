# Two exterior-row inequalities for case 4

The bounded pilot visited all 32 planned rows in 1.178 seconds. Every
numerical LP returned an optimal status. Two integer potentials gave
necessary inequalities, and both passed an optimizer-free exact replay.
The other 30 queries supplied no retained separator. No global LP or SAT
formula was rerun.

The inequalities apply to actual completions of indexed 35-core case 4.
They do not exclude that core. The saved proposal is still a numerical
point whose exact Gram feasibility has not been established.

## Exact inequalities

Use zero-based column and core indices from the frozen domain. For target
column \(a\), let \(N_a\) be its complete eligible neighbor domain and put

\[
c_{ab}=\max\left(v_{a,35}+\sum_{i\in h_b}v_{a,i},0\right)
\quad(b\in N_a),
\qquad c_{ab}=0\quad(b\notin N_a).
\]

The exact results are

\[
\sum_b c_{85,b}x_b\ge15x_{85},\qquad
\sum_b c_{628,b}x_b\ge2x_{628}.
\]

| Target column | Core-neighbor sites | Exterior degree | Positive coefficients | Largest absolute potential entry |
|---|---|---:|---:|---:|
| 85 | 1, 17, 20, 31 | 10 | 129 | 12 |
| 628 | 5, 15, 20, 27, 32 | 9 | 96 | 2 |

The 36 entries of each potential are its 35 core-row multipliers followed
by the exterior-degree multiplier:

```text
v85 = [-12,-3,-12,12,0,12,-12,-8,-12,
       -3,-9,-12,9,12,3,-9,-12,-12,
       3,12,4,6,4,3,-6,-6,-4,
       -9,0,9,4,6,0,-3,-4,-3]

v628 = [-2,1,-2,1,1,1,-1,2,1,
        -1,0,0,-2,2,-1,0,-2,-2,
        0,1,2,0,0,0,-2,0,0,
        2,0,0,0,0,1,0,0,-1]
```

The terminal JSON contains every eligible-neighbor product, including
the zero and negative products, and the complete positive coefficient
lists. Replay reconstructs the original attachment domain and checks
each integer product and each right-hand side. The proof is the exact
mixed/degree row identity and endpoint activation described in
`complement_rook_35core_case0004_exterior_rows.md`.

For binary selectors, any positive coefficient can also be capped at the
right-hand threshold without changing that inequality's Boolean meaning.
In the second inequality, the positive coefficients are 53 ones,
38 twos, and 5 threes. After capping at two, its meaning is: if column 628
is selected, at least one of 43 weight-two columns or at least two of the
53 weight-one columns must be selected. This is a consequence for future
encoding; no such encoding was added in this pilot.

## Numerical diagnostic and limits

At the sanitized saved numerical proposal, the right side minus the left
side is approximately 4.061463 for the first integer inequality and
0.114155 for the second. These are numerical proposal gaps. They are not
an exact certificate that the prior real relaxation is infeasible.

The integer inequalities themselves do not depend on numerical accuracy:
their necessity follows from the complete exact row domain. The pilot
does not establish that the other 30 rows are exactly feasible, nor that
all 1,214 possible target rows have been tested. It does not constrain
another matching core or another local eight-set.

## Reproduction

The result is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-separation-run01.json`.
The source and all inputs are hash-bound in that result and the terminal
artifact manifest. The source preserves the requested two-second row
and 60-second total limits, one thread, and per-row durable checkpoints.

The following command does not call an optimizer:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_row_separation.py replay \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-separation-run01.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-separation-replay-new.json
```

Use a fresh output filename. The existing replay files are frozen.
