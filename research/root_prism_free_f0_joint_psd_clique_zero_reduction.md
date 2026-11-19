# Exact zero substitution in the joint PSD and clique model

This package gives an equivalent real linear model for the frozen joint
PSD and clique relaxation. It removes precisely the 162 edge coordinates
already fixed to zero by explicit equalities. No optimizer was called.

The parent model is
`experiments/logs/root-prism-free/f0-joint-psd-clique-model01.json.gz`,
file SHA256
`43fff7283308cc2ed1be0936fae4b4f7b264c5961f6e6a4c9a81d123836e4f69`.
Its earlier numerical query remains UNKNOWN. This reduction does not change
that result or provide a feasible point or infeasibility certificate.

## Equivalence

Let \(J\) be the set of 162 coordinates fixed to zero by the parent
equalities, and let \(E\) insert zero at those coordinates. The reduced
variables retain their original unit bounds. Every parent feasible vector
has the form \(Eu\), and every retained row is exactly the corresponding
parent row evaluated at \(Eu\). Integer coefficients, right-hand sides and
positive numerical row scales of retained rows are unchanged.

The builder records an old-to-new column map, its inverse, a map for every
retained row, and a witness for each original row. Its general duplicate
logic uses primitive integer row keys only for lookup. Equality references
may have a nonzero signed proportionality factor; inequality references
require a positive factor unless they refer to a retained equality. The
replay checks these relations by literal integer cross multiplication.
No such duplicate or equality-reference removal occurs in this instance.

For a projected row \(a^T u\), its exact range on the unit box is

\[
\sum_j\min(a_j,0)\ \leq\ a^Tu\ \leq\ \sum_j\max(a_j,0).
\]

This proves every omitted row directly. The 162 zero equalities become
\(0=0\). The corresponding 162 rows \(Y_{ab}\leq Z_{ab}\) become
\(-Z_{ab}\leq0\), which follows from the retained variable bounds.
These are the only 324 omitted rows.

Thus deleting the zero coordinates and inserting them back give inverse
maps between the two feasible sets. This is equivalence over the real
unit box, not only over Boolean assignments. The 162 zero premises are
already part of the parent model; this package adds no new premise.

## Exact dimensions

| Quantity | Parent | Reduced |
|---|---:|---:|
| Variables | 15,200 | 15,038 |
| Equalities | 6,135 | 5,973 |
| Inequalities | 21,908 | 21,746 |
| Total rows | 28,043 | 27,719 |
| Nonzero terms | 1,086,559 | 1,079,832 |
| Stored PSD directions | 92 | 92 |

All selector and second-moment coordinates remain. All 92 held PSD
directions are physically retained, including any direction that might
be redundant after substitution. Their family counts are 32 augmented
selector directions, 17 directions conditioned on the 18-core, 22
directions conditioned on the full core, and 21 later joint-scan directions.

The reduction removes 6,727 terms, approximately 0.619 percent. This is a
small storage reduction. No runtime improvement has been measured, and
the counts do not justify an unchanged optimizer retry.

## Verification and files

The builder is
`experiments/workspace/root_prism_free_f0_joint_psd_clique_zero_reduction.py`,
SHA256 `3dfa11d839993206d59cc76d48f77881320ee8fd13e956fd247e17f2fc0ef120`.
Its preparation runs exact small rational-grid controls and saves the
complete row/column witness maps in
`experiments/logs/root-prism-free/f0-joint-psd-clique-zero-model01.json.gz`.

The separate standard-library checker is
`experiments/workspace/root_prism_free_f0_joint_psd_clique_zero_replay.py`,
SHA256 `b8db3a661ed2a31056d30eb7134bbce7f06d33d77ddc354338b28834f73e95e7`.
It imports no subject builder. It reconstructs the 162 zero premises,
checks every original obligation and retained row directly, checks both
column maps, and verifies that all 92 PSD directions and every second
moment coordinate survive. Its standalone replay passed in 28.96 seconds.

The reduced model file SHA256 is
`da9b2062f9102a0487bc5fb88b2e009c1a228cbc2d2c39264135808bb3467ffb`;
its canonical mathematical-model SHA256 is
`7793e51627f1559aa041ababce08f68f2899f3984afa1e92dd039d9e4871a6cf`.
The exact matrix and scale hashes are
`af8df1fdd52c5dc0ec760914bb27c2d10d1f2761c6cc957edfc6ede87f319816`
and `84c35e927e99e96bffdbd5d03bdfe574ddaaeb447e0868a295215518365e71bb`.

The independent source review is
`experiments/logs/root-prism-free/f0-joint-psd-clique-zero-reduction-independent-source-review.json`,
SHA256 `96ee2d196e7f0124f41f77fecc392216376c015e74a9082a94fbb61c228ca5e2`.
It covers both complete sources and the mathematical equivalence. It did
not repeat the model reconstruction, controls or an optimizer call.

The complete preparation and standalone replay records are
`f0-joint-psd-clique-zero-model01-preparation.json` and
`f0-joint-psd-clique-zero-model01-standalone-replay.json` in the same log
directory. This package ends at exact preparation and replay.
