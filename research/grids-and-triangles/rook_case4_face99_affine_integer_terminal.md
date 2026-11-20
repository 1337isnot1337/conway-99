# Exact signed-integer feasibility of the case4 equalities

The complete native equality system on the proved 99-zero face has a signed
integer solution. The saved 1,214-coordinate vector passes every one of the
632 original equalities and all 99 zero equations. Both the constructor's
cold replay and the separate standard-library checker passed.

This closes the signed-integer lattice question for these equalities. It
does not settle binary incidence feasibility: the vector has 92 negative
coordinates and 67 coordinates greater than one.

## Construction and exact acceptance

The single authorized child used only the first prepared 286-square minor,
selected modulo 19. Its exact Dixon solve took 0.526 seconds and already
returned denominator one. The two later solves, associated with 601 and
145463, were skipped. In the saved Bézout stage the old rational point has
coefficient zero and this new integer point has coefficient one.

The full child took 10.872 seconds, with 13.110 seconds measured by the
supervising process. No optimizer, HNF, SNF, or automatic retry was used.
The cold replay took 38.762 seconds and did not solve a linear system.
The separate direct checker took 0.211 seconds.

The point has the following exact statistics:

| Property | Value |
|---|---:|
| Original coordinates | 1,214 |
| Original equality rows checked | 632 |
| Distinct nonempty equations after substitution | 396 |
| Previously proved zero coordinates | 99 |
| Negative coordinates | 92 |
| Positive coordinates | 161 |
| Coordinates equal to zero | 961 |
| Nonzero coordinates | 253 |
| Minimum coordinate | −10 |
| Maximum coordinate | 19 |
| Maximum integer bit length | 5 |
| Common denominator | 1 |

The 862 zero coordinates beyond the already proved 99 belong to this
chosen point. They are not new universal zero conclusions.

## Meaning of the certificate

Let A x=b denote precisely the native equalities after the 99 established
zeros. The final vector proves that b lies in the integer column lattice
of A. Consequently, no congruence or integer-linear obstruction using only
these equality rows can exclude the case. Reducing the vector modulo any
positive modulus gives a solution of the corresponding congruences.

The nonnegative and binary problems remain separate. This signed point is
not checked against the signature capacities, triple capacities, conflict
clauses, nonempty exterior-row inequalities, or coordinate covers. Its
negative coordinates already prevent it from being an incidence design.
The earlier strictly positive rational point and this signed integer point
must not be combined into a claim of nonnegative integer feasibility.

## Authoritative artifacts

The vector is
`experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01/integer-point.json`,
with SHA256
`9aad22d8896ac071a946dc16c4775a401882b41bd31e8981f269d16e9f1371f9`.

The final result is bound by
`rook-case4-face99-affine-integer-run01/result.json`, SHA256
`75916828aab10ac828791acbe972506dd0abc4cee8f3ddb972e2807c53d555f6`.

The cold trace replay is
`rook-case4-face99-affine-integer-run01-replay.json`.
The independent direct-vector report is
`rook-case4-face99-affine-integer-run01-direct.json`.
All paths above are under `experiments/logs/grids-and-triangles`.

The direct checker imports no constructor, modular elimination, linear
solver, or optimizer. It rebuilds all 630 Gram supports from the diagonal
supports of the bound native input, checks each original Gram equation,
checks the two empty-support row equations directly, and verifies the 99
known zero coordinates. The vector itself is sufficient for this affine
feasibility conclusion; the construction trace is retained for provenance.

## Replays

```sh
python experiments/workspace/rook_case4_face99_affine_integer.py replay \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-preparation01 \
  --directory experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01 \
  --output /tmp/rook-case4-affine-integer-cold.json
```

```sh
python experiments/workspace/rook_case4_face99_affine_integer_direct_check.py \
  --point experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01/integer-point.json \
  --output /tmp/rook-case4-affine-integer-direct.json
```

Both commands are optimizer-free. Each output path must be new.
