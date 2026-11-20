# Order-ten prism-zero feasibility probe

## Result

The single bounded interior-point run returned a numerical proposal in
16.925 seconds, using twelve IPM iterations and no crossover iterations.
It does not exclude the prism-free case and is not an exact count witness.

The proposal has prism coordinate exactly zero. Scanning the existing
1,416 moment and projector blocks produced no exact negative
integer-vector certificate. One numerical negative, approximately
`-5.96e-7` in `induced-schur-7.pickle` block 415, did not yield an exact
separator. This scan does not certify PSD.

Rounding the ordinary core coordinates produces integral induced counts,
but two induced counts are negative:

| Catalogue type | Rounded induced count |
| --- | ---: |
| 48301 | -1 |
| 48915 | -1 |

Every other induced count is nonnegative. There are no divisibility
failures, and all fourteen previously certified cuts are strictly positive
at the rounded point. The complete rounded point and exact failures are
preserved. No correction search, second optimization, or dual extraction
formed part of this run.

## Mathematical scope

The target is a hypothetical SRG(99,14,1,2) with no triangular prism.
Coordinate 1 of the ordinary core count vector is the number of prism
copies. The corresponding six-vertex catalogue graph is type 99, with
adjacency bit rows

```text
[28, 56, 49, 35, 7, 14]
```

The preparation saves an explicit isomorphism to the usual two-triangle
prism. It also saves explicit ordinary embeddings of this prism into both
nine-vertex patterns whose coordinates are zeroed: broken rook at
coordinate 56 and rook at coordinate 57. Thus their zero counts are
necessary when the prism count is zero.

In an SRG with lambda one, a prism copy cannot acquire an additional edge
between its two triangles. Such an edge would give an edge of one triangle
two common neighbors. Consequently the ordinary prism count also counts
induced prism copies in the hypothetical graph. The model does not assume
that this count must be positive.

The earlier prism-zero count and theta relaxations are not contradicted by
this numerical run. The current run adds order-ten count constraints and
fourteen proved linear inequalities, but it supplies neither a graph nor
an impossibility proof.

## Model and exact bindings

The model retains the entire frozen free-prefix order-ten count relaxation
and all fourteen certified cuts from
[the bounded moment loop](grid_free_order10_moments_loop.md). The cuts
comprise thirteen exact moment inequalities and one universal order-ten
count inequality. Their coefficient-list SHA-256 is

```text
b133c05d00297e6786d71d348ddaf02342f23ce43e1e77bb41d3376df47f80dd
```

It has 47,634 rows, 547 stored variables, and 5,427,993 nonzeros. The prism
variable is retained as column zero and receives equal lower and upper
bounds of zero. Its scale factor is 3,234. There are therefore 546 free
variables. The effective fixed coordinates are

```text
x[0] = 1; x[1] = 0; x[56] = 0; x[57] = 0.
```

All other upper bounds and positive row scalings are unchanged. No new
zero propagation removes rows or variables. Preparation replays all
fourteen cut certificates and binds the exact reduction audit, which
checks all 180,445 original equations and finds no residual equalities or
congruences.

The canonical CSC matrix, row upper bounds, and variable bounds have
SHA-256

```text
cd09cf494efafa04cd850ffa593d8d55679fb39393118d0d06189ee5a3a0e596
```

The installed HiGHS 1.16.0 accepts `solver=ipm`, `run_crossover=off`,
`presolve=on`, `threads=1`, and `time_limit=120`. The source uses those
settings and a separate cancellation timer. Exactly one solver call ran.
The objective is zero.

## Validation and saved data

The source saves all returned primal and dual arrays, their validity flags,
and solver diagnostics. A numerical status cannot set the exact
infeasibility flag. Every valid finite primal proposal receives the
1,416-block scan and exact rounded-count checks.

The count gate uses Python integer evaluations of all reduced induced
forms. It requires nonnegativity and divisibility before checking every
original extension equation and level total. This proposal fails at the
nonnegativity stage, so the source does not label it a witness. The
rounded prism coordinate is explicitly fixed to zero, and all fourteen
cuts are also evaluated exactly.

The numerical point and the rounded point are distinct saved objects.
The two negative rounded counts do not refute the numerical point or
prove that no nearby exact point exists. Conversely, a numerical solver
status and a scan with no exact separator do not certify a rational
feasible point or PSD.

## Preserved launch correction

The first driver, `grid_free_order10_prism_zero.py`, stopped before any
solver call. Its in-memory metadata used tuples where the reloaded JSON
used lists. The equality guard therefore failed before the HiGHS model
was passed to the solver.

The separate `grid_free_order10_prism_zero_v2.py` changes exactly that
serialization expression to a list of lists. Its entire saved model,
including the numerical matrix and bounds hash, equals the original
preparation. The original source, preparation, failed launch log, and
zero-call failure record remain unchanged.

The v2 source SHA-256 is

```text
ec972814b45828107d9c97f7c94e9760fef7973b360f3af7da8c8a33bc4e1ab3
```

## Files

Sources are in `experiments/workspace/`. Artifacts are in
`experiments/logs/moments-and-counts/`.

The original attempt uses prefix `grid-free-order10-prism-zero`, with
`-preparation.json`, `-preparation.log`, `-run.log`, and
`-launch-failure.json`.

The completed run uses prefix `grid-free-order10-prism-zero-v2`, with
`-preparation.json`, `-preparation.log`, `-result.json`, `-run.log`,
`-solver-data.json`, `-proposal.json`, `-separation.json`, and
`-rounded-counts.json`. The package manifest binds these artifacts and
the two sources.

The run command was:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_prism_zero_v2.py run \
  --preparation experiments/logs/moments-and-counts/grid-free-order10-prism-zero-v2-preparation.json \
  --output experiments/logs/moments-and-counts/grid-free-order10-prism-zero-v2-result.json \
  --prefix experiments/logs/moments-and-counts/grid-free-order10-prism-zero-v2 \
  --seconds 120
```
