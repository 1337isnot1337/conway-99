# Translation obstruction for three compatible rook grids

Three disjoint induced rook grids with pairwise rook-isomorphic matching
interfaces cannot have translation holonomy in an `srg(99,14,1,2)`.
The exact outside-incidence equations give `0=54`.

This statement does not require the three grids to be all-red. Once the
three matching interfaces have the form below, their induced 27-vertex
core is sufficient for the contradiction.

## The core and its outside signatures

Label the three grids `0,1,2`, with points `(x,y)` in `F_3^2` and vertex
number `9b+3x+y`. Gauge the interfaces `0 -> 1` and `0 -> 2` to the
identity. Set the remaining interface to

\[
p(x,y)=(x+1,y+1).
\]

Its permutation in row order is `(4,5,3,7,8,6,1,2,0)`, label four in
the sorted eleven-map convention. All four translations with both
coordinates nonzero are conjugate to this one by coordinate reversals.

Let `B` be the adjacency matrix of these 27 vertices. It has degree six.
Every outside vertex has exactly one neighbor in each induced rook
grid: any two grid vertices already have their full common-neighbor
quota inside the grid, and the grid's 90 outgoing edges meet its 90
outside vertices. Thus an outside neighborhood is a three-element
signature, with one point in each grid.

Let `h` denote its indicator vector. Two necessary conditions are

\[
G_{ij}>0\quad\text{whenever }h_i=h_j=1,\ i\ne j,
\qquad (B+I)h\le2\mathbf1,
\]

where

\[
G=12I+2J-B^2-B.
\]

The first condition preserves the remaining common-neighbor quota of
each core pair. The second bounds the common neighbors of an outside
vertex and a core vertex that already lie in the core. Both follow
directly from `A^2+A=12I+2J`.

Exact enumeration of the `9^3=729` signatures gives 135 satisfying the
first condition and 108 satisfying both. Every core vertex occurs in
12 of the 108 surviving signatures.

## An exact linear contradiction

Let `z_s` be the number of outside vertices with signature `s`. If `X`
is the outside-incidence matrix, then `XX^T=G`. For each core pair with
positive residual quota, this gives

\[
\sum_{s\supseteq\{i,j\}}z_s=G_{ij}.
\]

Classify the off-diagonal equations by their right side `q=G_ij` and
the number `a` of admissible signatures containing the pair. There are
four classes:

| Class `(q,a)` | Number of equations | Sum of right sides |
| --- | ---: | ---: |
| `(1,1)` | 27 | 27 |
| `(1,4)` | 27 | 27 |
| `(2,2)` | 54 | 108 |
| `(2,3)` | 27 | 54 |

Sum the equations within each class. In the class order displayed above,
the coefficient vector of every signature has one of these three forms:

| Signature coefficient vector | Number of signatures |
| --- | ---: |
| `(1,0,0,2)` | 27 |
| `(0,1,2,0)` | 54 |
| `(0,2,0,1)` | 27 |

Each vector has zero dot product with `(-8,-2,1,4)`. That weighted sum
of the four aggregate equations therefore has zero left side, but its
right side is

\[
-8(27)-2(27)+108+4(54)=54.
\]

This is impossible. The certificate excludes even real solutions of
the incidence equations. It does not use integer programming, a
numerical rank test, or nonnegativity of the `z_s`.

## A separate forcing contradiction

A signature cannot occur twice: its two outside vertices would share
three common neighbors. Consequently `z_s` is zero or one. Every
equation in classes `(1,1)` and `(2,2)` forces all its available
signatures to occur. Their union contains exactly 81 signatures,
although the graph has only 72 outside vertices.

Each core vertex belongs to nine forced signatures. Its core degree
six leaves room for only eight outside neighbors. The saved certificate
also records nine explicit signatures through core vertex zero and a
forcing pair for each. This gives a local replay of the same obstruction.

## Replay and scope

`experiments/workspace/three_red_translation_incidence.py` uses only
Python's standard library. It builds the core directly, enumerates all
signatures, and checks the mixed bounds a second way. It then verifies
the coefficient of each of the 108 signature variables in the integer
certificate and checks that the resulting right side is 54.

The saved artifact contains the core adjacency rows, Gram matrix, full
signature list, all 162 positive Gram equations, and both certificates.

```bash
python experiments/workspace/three_red_translation_incidence.py \
  --verify experiments/logs/grids-and-triangles/three-red-translation-incidence.json
```

The explicit core and all conjugate full-support translations are
excluded. The separate three-grid interface classification and boundary
checks handle the identity and reflection holonomies. No adjacency
among the 72 outside vertices was chosen or assumed in this proof.
