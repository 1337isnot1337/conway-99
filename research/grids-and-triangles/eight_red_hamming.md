# An induced ternary three-cube is impossible

A hypothetical strongly regular graph with parameters `(99,14,1,2)`
contains no induced Hamming graph `H(3,3)`. This excludes the Hamming
case of the 27-vertex remainder left by eight all-red grids. The argument
does not require any red grids or any classification of projections.

The Hamming graph has vertex set `{0,1,2}³`; two vertices are adjacent
exactly when they differ in one coordinate. It has 27 vertices and degree
six. Two vertices at Hamming distance one, two, or three have respectively
one, two, or zero common neighbors inside this graph.

## Every outside neighborhood is a three-point code

Suppose `U` induces this Hamming graph in the hypothetical strongly regular
graph. Pairs at distance one or two already have their full required
common-neighbor count inside `U`. An outside vertex can therefore have
only pairwise distance-three neighbors in `U`.

Such a set has size at most three, because its points have distinct values
in every coordinate. On the other hand, `U` sends

\[
27(14-6)=216
\]

edges to its 72 outside vertices. This equals three times 72. Thus every
outside vertex has exactly three neighbors in `U`.

## The unique third point gives a contradiction

Choose points `u,v` at Hamming distance three. They have no common
neighbors inside `U`, so they have two distinct common neighbors `x,y`
outside `U`.

There is exactly one point `w` at distance three from both `u` and `v`:
in each coordinate, take the third symbol not used by that coordinate
of `u` or `v`. Since every outside vertex has three pairwise
distance-three neighbors in `U`, both `x` and `y` have the same
neighborhood `{u,v,w}` in `U`.

The pair `x,y` has at least three common neighbors. Every pair in an
`srg(99,14,1,2)` has at most two. This is a contradiction.

An equivalent count is that there are only `3!·3!=36` possible
three-point codes: order their points by the first coordinate, then
permute the symbols in each of the other two coordinates. No code can
be the neighborhood of two different outside vertices, since those
vertices would share three common neighbors. There are 72 outside
vertices that require such a code, exceeding the 36 available codes.

## Relation to eight all-red grids

Eight all-red grids leave 27 vertices of degree six. If that induced graph
were `H(3,3)`, each red-base projection would partition it into nine of the
three-point codes above. Common-neighbor requirements on pairs of
distance three would require each code twice across the eight
projections. Those two uses would themselves create a pair of red-base
vertices with three common neighbors.

This explains why even a proposed collection of nonlinear projections
cannot work. The obstruction occurs before the red-line condition or the
matching conditions between base grids need to be imposed. It does not
exclude all possible 27-vertex remainders, or the possibility of eight
all-red grids in general.

## Exact finite control

`experiments/workspace/eight_red_hamming.py` uses only Python's standard
library. It checks the induced degrees and all 351 pair-codegrees,
enumerates all 36 compatible triples by two different methods, verifies
that every distance-three pair has exactly one compatible third point,
and checks that no compatible four-point set exists. It then checks the
integer boundary count and the `72 > 36` contradiction.

The pair counts are:

| Hamming distance | Common neighbors in `U` | Unordered pairs |
| ---: | ---: | ---: |
| 1 | 1 | 81 |
| 2 | 2 | 162 |
| 3 | 0 | 108 |

Run from the repository root:

```bash
python experiments/workspace/eight_red_hamming.py \
  --output experiments/logs/grids-and-triangles/eight-red-hamming.json
```

The finite check audits the small graph used in the proof. The exclusion
itself follows from the counting argument above and does not depend on
search or solver output.
