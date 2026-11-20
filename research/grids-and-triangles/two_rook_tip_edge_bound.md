# A weighted edge bound for the nine tips of an isomorphic pair

Let two disjoint induced rook grids have a rook-isomorphic matching.
Use matching coordinates `0,...,8`, and let `z_i` be the unique common
neighbor of the matched core edge at coordinate `i`. Write `Z` for the
graph on these nine tips, `R` for the fixed rook adjacency relation,
and

\[
e=|E(Z)|,\qquad t=|E(Z)\cap E(R)|.
\]

Then

\[
\boxed{e\le16\quad\text{or}\quad Z=J-I-R,}
\]

and consequently

\[
\boxed{4e+t\le72.}
\]

The complement-rook alternative remains unresolved as a full completion.
This bound does not exclude the isomorphic pair.

## The two high-edge catalogue types

For every nine-vertex graph satisfying the inherited common-neighbor
caps, with degrees `d_i`,

\[
\frac12\sum_i d_i^2
=\sum_{i<j}\big((Z^2)_{ij}+Z_{ij}\big)\le72.
\]

Cauchy-Schwarz gives `e<=18`. A fresh reconstruction of the complete
diamond/K2,3-free catalogue through order nine has 6,535 types, including
5,311 of order nine. Exactly two order-nine types have at least 17
edges:

| Edges | Number of types | Identification |
| ---: | ---: | --- |
| 17 | 1 | Rook graph with one edge deleted |
| 18 | 1 | Rook graph |

The new certificate records their adjacency rows and explicit
isomorphisms to the standard labelled targets. Replay rebuilds the
catalogue rather than reading the previously cached list, and checks
the saved isomorphisms directly.

## Why the seventeen-edge type is impossible

This restates the existing integral obstruction in `STATE.md`, using
the norm-14 structure from
[`shortest_vectors.md`](../eigenlattices/shortest_vectors.md).

Suppose an induced nine-vertex set `H` is the rook graph with one edge
deleted. For the full graph adjacency matrix `A`, put

\[
v=(3I-A+J/9)1_H.
\]

Because `|H|=9`, this vector is integral. It is a -4 eigenvector, has
coordinate sum zero, and satisfies

\[
\|v\|^2=7\left(3\cdot9-2\cdot17+\frac{9^2}{9}\right)=14.
\]

If any coordinate had magnitude at least two, its eigenvector equation
would require opposite-sign mass at least eight. The positive and
negative masses are equal, so the total absolute mass would be at
least sixteen. Integrality gives squared norm at least sixteen, a
contradiction. Hence `v` has seven entries +1 and seven entries -1.

Each negative site has at least four positive neighbors. Counting pairs
of positive sites with a marked negative common neighbor gives at least

\[
7\binom42=42
\]

incidences. The universal two-common-neighbor bound gives at most

\[
2\binom72=42.
\]

Equality forces every common neighbor of two positive sites to be
negative. But the deleted edge's endpoints both have coordinate +1,
while their third vertex on the original rook line is a common
neighbor with coordinate zero. This contradiction excludes the
seventeen-edge type.

The census verifier checks the restricted coordinates, the norm
calculation, and the matching incidence totals exactly. The argument
above supplies the mathematical exclusion; no solver is used for it.

## The eighteen-edge boundary

The complete labelled census and exact incidence reduction in
[`two_rook_tip_rook_boundary.md`](two_rook_tip_rook_boundary.md)
left two orbits at eighteen edges: the complement rook and an orbit
of 18 other labelled rook graphs. The checked joint incidence/edge
certificate in
[`two_rook_tip_boundary_joint_integer.md`](two_rook_tip_boundary_joint_integer.md)
excludes the latter orbit without fixing an incidence witness.

Therefore `e=18` forces the labelled equality `Z=J-I-R`. In particular,
`t=0`. Combining this with the seventeen-edge exclusion proves the
stated alternative.

The new census certificate binds the separate boundary proof manifest's
SHA-256. It does not rerun the large CNF or its DRAT proof; that checked
certificate remains an explicit theorem dependency.

## Deriving the weighted bound

At each tip, the existing Hall inequality is
`d_near<=d_far`, where near and far refer to the fixed rook labels.
Summing over all nine tips gives

\[
2t\le2(e-t),\qquad t\le\frac e2.
\]

If `e<=16`, then

\[
4e+t\le\frac92e\le72.
\]

In the remaining case, `Z=J-I-R`, so `e=18,t=0` and the same bound is
an equality. The only arithmetic possibilities for equality are
`(e,t)=(16,8)` and `(18,0)`. No realization of either pair in an
SRG(99,14,1,2) is asserted.

## Exact replay

Source: `experiments/workspace/two_rook_tip_edge_bound.py`.
Certificate and logs use the stem
`experiments/logs/grids-and-triangles/two-rook-tip-edge-bound-`.

```sh
python experiments/workspace/two_rook_tip_edge_bound.py \
  --boundary-proof experiments/workspace/two-rook-tip-boundary-joint-3679836361-certificate.json \
  --certificate experiments/logs/grids-and-triangles/two-rook-tip-edge-bound-certificate.json
```

Add `--write` to regenerate. This rebuilds the small graph catalogue,
checks the two explicit identifications, and verifies the norm and
edge-inequality arithmetic controls. It launches no completion solver.
