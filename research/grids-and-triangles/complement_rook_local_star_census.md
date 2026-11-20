# Complete local choices at one complementary-rook core point

At a fixed point of either rook base, there are exactly 864 possible
sets of eight exterior neighbors at the local incidence level. They
form 118 orbits under the eight-element point stabilizer. Every set
has an eligible perfect matching. Every resulting 35-point core passes
the visible common-neighbor caps and both principal-projector tests.

This census does not assert that any local choice extends to a full
72-column incidence design or an exterior graph. It gives a complete,
small domain for a later conditional search and shows that these local
projector tests remove no choice.

## The 864 local signature sets

Use the complementary-rook core and signature convention of
`complement_rook_positive_pattern.md`. Fix the core vertex `R0`.
Its 28 possible exterior signatures have the form `(0,q,t)`, where

\[
q\in\{4,5,7,8\},\qquad t\in\{1,\ldots,8\}\setminus\{q\}.
\]

The exact Gram equation at `R0` requires eight selected signatures.
The four pairs `(R0,Sq)` each have quota two. The eight pairs
`(R0,Tt)`, for `t != 0`, each have quota one. Therefore the eight tip
labels must be partitioned into four labeled pairs, with label `q`
excluded from the pair assigned to `q`.

Without the four exclusions there are `8!/(2!)^4=2520` assignments.
Inclusion-exclusion gives

\[
2520-2520+1080-240+24=864.
\]

The recursive enumeration independently obtains all 864 distinct sets
and checks every required local quota. The core's 144 verified
relabelings have an eight-element stabilizer of `R0`. Applying that
stabilizer gives the following complete orbit census.

| Orbit size | Number of orbits | Labeled sets |
| ---: | ---: | ---: |
| 8 | 101 | 808 |
| 4 | 11 | 44 |
| 2 | 6 | 12 |
| Total | 118 | 864 |

The certificate exports all sets, their orbit indices, and the 118
representatives. These are relabelings of the fixed core; no symmetry
of the hypothetical full graph is assumed.

## The matching on eight exterior neighbors

The six known core neighbors of `R0` already induce three disjoint
edges. None of the 28 candidate signatures sees one of those six
points. Since the neighborhood of `R0` must be seven disjoint edges,
its eight selected exterior neighbors must induce a perfect matching.

The eligible-edge domain retains only pairs permitted by the core
common-neighbor quotas and conditional mixed equations. The census
enumerates every perfect matching using those eligible edges.
Depending on the local signature set, there are between 13 and 43
matchings. No local set is excluded.

There are 2,521 matching choices on the 118 set representatives. Their
transports cover 18,386 choices over all 864 labeled sets. These are
counts of matching choices on set representatives, not an isomorphism
count of the completed 35-point cores.

For every representative choice, the checker appends the eight
signature vertices and four matching edges to the 27-point core. It
then directly checks all visible pair caps

\[
(B^2+B)_{uv}\le2\qquad(u\ne v)
\]

on the resulting 35-point graph. Every choice passes.

## Exact projector calculation

The two necessary principal-projector matrices are

\[
Q_-=27I-9B+J,\qquad Q_+=44I+11B-2J.
\]

The already checked 27-point core has ranks 24 and 27 respectively.
Its three `Q_-` kernel vectors are compatible with every signature.
The saved exact inverse construction therefore reduces the two tests
to eight-by-eight Schur matrices on the added vertices.

For all 2,521 representative matching choices, both Schur matrices
annihilate the all-ones vector. Delete their last row and column to
obtain a seven-by-seven matrix `K`. The checker constructs an exact
`LDL^T` factorization of `K`, verifies its product entry by entry, and
checks that all seven pivots are positive. With

\[
S=\begin{pmatrix}K&-K\mathbf1\\-\mathbf1^TK&\mathbf1^TK\mathbf1\end{pmatrix},
\]

this proves that `S` is positive semidefinite of rank seven. Thus both
principal-projector tests pass for every choice, with full 35-point
ranks 31 and 34. There are 5,042 exact positive quotient checks.
No numerical eigensystem is used in this certificate.

## Reproduction

```sh
.venv/bin/python experiments/workspace/complement_rook_local_star_census.py
```

The source checks the hash of the earlier exact projector construction,
regenerates every local set and orbit, and repeats every integer and
rational calculation. The deterministic certificate is
`experiments/logs/grids-and-triangles/complement-rook-local-star-census.json`.
It records the local sets, orbit representatives, counts, exact pivot
bounds, and a hash of every Schur matrix and factorization.

The census gives no whole-core exclusion. The smaller star oracle
retains more constraints by leaving the remaining incidence design
and all edges touching the chosen star in its model.
