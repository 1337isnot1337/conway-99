# Independent audit of the rooted matching normalization

Fix anchor 0 and its mate 1. The other twelve neighbor labels form six
fixed mate pairs `(2,3),...,(12,13)`. The anchor's twelve exterior
neighbors must be paired by a perfect matching. Relabeling the six
remaining axes and independently swapping their two endpoints acts
as the signed permutation group of order `2^6*6!=46080`.

There are exactly 11 orbits of the 10,395 possible matchings. The audit
below uses a closed counting formula, independently of the recursive
matching census and generator-orbit search in the model's other audit.

## Classification and orbit sizes

Superimpose the fixed mate matching and a candidate matching. Each
component is an alternating cycle with `2l` vertices; a repeated edge
is the `l=1` case. The component sizes in fixed axes form a partition
of six.

Two matchings with the same partition are equivalent: pair their
same-size alternating components, then use a color-preserving cycle
isomorphism. It maps fixed mate edges to fixed mate edges, so it is
exactly an axis permutation with independent endpoint swaps. Different
partitions cannot be equivalent.

For a partition with `m_l` parts of size `l` and `k` total parts, the
orbit size is

\[
\frac{2^{6-k}6!}{\prod_l l^{m_l}m_l!}.
\]

To derive it, partition the six labelled axes into component blocks.
A block of `l` axes has `2^{l-1}(l-1)!` matchings producing one alternating
component, including the cases `l=1,2`. Multiplying these counts gives
the displayed expression.

| Partition | Orbit size |
| --- | ---: |
| 1+1+1+1+1+1 | 1 |
| 1+1+1+1+2 | 30 |
| 1+1+1+3 | 160 |
| 1+1+2+2 | 180 |
| 1+1+4 | 720 |
| 1+2+3 | 960 |
| 1+5 | 2,304 |
| 2+2+2 | 120 |
| 2+4 | 1,440 |
| 3+3 | 640 |
| 6 | 3,840 |

The sizes sum to `11!!=10395`. The certificate includes a canonical
matching on the actual labels `2,...,13` for each partition, verifies
its alternating components, and checks the corresponding stabilizer
order. It also checks the formula for one through five remaining axes.

Choosing one representative in the rooted search fixes labels only.
It does not require an automorphism of a completed graph.

## Scope of the 84 broken-rook implications

For two root mate-pairs, the root, four near vertices, and four forced
far vertices form a mandatory nine-vertex cell. The four far vertices
have four sign-changing side positions and two diagonal positions.

A diagonal together with any side exceeds the common-neighbor cap of
an appropriate near/far pair. Therefore, when three sides are present,
both diagonals are absent. If the fourth side were absent, the cell
would be the induced rook graph minus one edge. The unconditional
norm-14 obstruction in
[`two_rook_tip_edge_bound.md`](two_rook_tip_edge_bound.md) excludes it.

Thus each of the four sets of three sides forces the fourth. There are
21 pairs of axes, giving 84 valid clauses. This proof uses no grid-count
bound or full-axis hypothesis.

The conclusion is conditional on a side being present. Diagonals with
no side edges must not be forbidden by this argument. The separate
64-assignment local control finds 19 cap-compatible far-edge patterns,
including all four zero-side diagonal patterns. Exactly four compatible
patterns have three sides; these are precisely the broken-rook patterns
removed by the extra implications. The four-side pattern is the
nine-point rook graph and passes as the degree-four positive control.

## Replay

Source: `experiments/workspace/root_full_caps_matching_orbit_audit.py`.
Certificate: `experiments/logs/grids-and-triangles/root-full-caps-matching-orbit-audit.json`.

```sh
python experiments/workspace/root_full_caps_matching_orbit_audit.py \
  --certificate experiments/logs/grids-and-triangles/root-full-caps-matching-orbit-audit.json
```

This audit uses only the standard library and launches no completion
solver or duplicate matching census.
