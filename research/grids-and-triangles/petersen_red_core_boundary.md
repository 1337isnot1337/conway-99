# The Petersen five-grid core cannot occur

The 45-vertex Petersen interface core cannot be an induced subgraph of an
`srg(99,14,1,2)`. Its five constituent rook grids would force each of the
other 54 vertices to have one neighbor in each grid. There are only
eighteen possible neighbor sets after the local common-neighbor bounds,
and no two outside vertices can use the same set. An independent short
integer eigenvector argument excludes every possible set individually.

This is a statement about the specified core. Its use in a bound on all-red
grids also requires the separate complete interface census and exclusions
of the other interface types.

## Construction

Let `P` be the Petersen graph whose ten vertices are the two-element subsets
of `{0,1,2,3,4}`. Two vertices are adjacent when their subsets are disjoint.
Color an edge by the unique element absent from its two endpoints. Each of
the five colors occurs on three pairwise disjoint edges. In the line graph
`L(P)`, the edges of any two different colors are joined by a perfect
matching.

The core points are pairs `(e,v)`, where `e` is one of the fifteen edges of
`P` and `v` belongs to `{0,1,2}`. Adjacency is defined by:

- Within one edge color, `(e,v)` and `(f,w)` are adjacent when `e != f`
  and `v != w`.
- Between different edge colors, they are adjacent when `e` and `f`
  share a Petersen endpoint and `v=w`.

Each color gives a nine-vertex rook grid. The first adjacency rule is the
usual rook graph after the invertible coordinate change
`u=x+y, v=x-y` over `F_3`. Each point has four neighbors in its grid and
one in each other grid, so the core adjacency matrix `B` has degree eight.

Every exterior vertex of a rook grid in the target strongly regular graph
has exactly one neighbor in that grid, as proved in
[`red_grid_limit.md`](red_grid_limit.md). Thus an exterior vertex of this
core must select a point from each color. Write this five-point neighbor
set as its signature.

## The pair quotas force one coordinate and a perfect matching

Put

    C = 12 I + 2 J - B^2 - B.

If the core extends to the full graph and `X` is its incidence matrix to
the exterior vertices, the strongly regular graph identity gives

    C = X X^T.

In particular, two core points with `C_(a,b)=0` cannot occur together in a
signature.

Consider two selected points `(e,v),(f,w)` of different colors. The
following pair rules are immediate from the core adjacency:

- If `v=w`, the Petersen edges `e,f` must be disjoint. If they share an
  endpoint, their core points are adjacent and already have their unique
  common neighbor in the third edge at that endpoint.
- If `v!=w`, the Petersen edges `e,f` must share an endpoint. If they are
  disjoint, the two core points already have two common neighbors, one
  in each endpoint grid. If they share an endpoint, these two paths are
  absent.

Equivalently, the five selected Petersen edges induce a complete
multipartite graph in `L(P)`, whose parts are the equal-coordinate classes.
There are at most three parts.

The line graph is claw-free: three pairwise disjoint edges cannot all meet
one edge, which has only two endpoints. Therefore, if more than one part
is nonempty, every part has size at most two. Five selected edges in at
most three such parts must have sizes `2,2,1`. The two parts of size two
would give an induced four-cycle in `L(P)`.

That induced four-cycle cannot exist. Its four Petersen edges would form
a four-cycle in `P`. The two-subset definition shows that `P` has no
four-cycle: two distinct opposite vertices have at most one common
neighbor, because the complement of the union of their subsets has at
most two elements.

Hence all five selected points have the same coordinate `v`. Their five
Petersen edges are pairwise disjoint and therefore form a perfect matching
`M` of `P`. Since one point was selected in each grid, the five matching
edges have different colors.

## Eighteen signatures are too few

The Petersen graph has six perfect matchings. The exact check below
enumerates all `binomial(15,5)=3003` edge subsets and checks this count.
Each matching contains one edge of each color. Consequently there are
exactly `3*6=18` signatures, one for each matching and each common
coordinate.

Two different outside vertices cannot have the same signature: they would
have five common neighbors in the core, exceeding the common-neighbor
bound two. Therefore at most eighteen exterior vertices could attach to
this core. The target graph requires 54, a contradiction.

## An integer certificate excludes each signature

There is a second obstruction that does not need the count of perfect
matchings. Fix any candidate matching `M` and define an integer vector on
the core by

    z(e,w) = 2  if e belongs to M,
             -1 otherwise.

It is independent of `w`. Each grid contains one matching edge, so the
sum of `z` on its three edge positions is zero. Its internal rook
adjacency contributes `-2z`.

In `L(P)`, a matching edge meets no other matching edge. A nonmatching
edge meets exactly two matching edges, one at each Petersen endpoint.
The four cross-grid neighbors therefore also contribute `-2z`. It follows
that

    B z = -4 z,        1^T z = 0,        C z = 0.

For a candidate signature column `h`, all its five chosen points lie on
matching edges, so

    h^T z = 10.

But `C=XX^T` and `Cz=0` imply

    0 = z^T C z = ||X^T z||^2,

so every column of `X` must be orthogonal to `z`. The nonzero inner product
is a contradiction. Thus no exterior vertex with a required one-per-grid
signature can be added at all.

## Exact finite replay

`experiments/workspace/petersen_red_core_boundary.py` uses only the Python
standard library. It independently constructs the 45-point adjacency,
checks every cross-grid matching and all common-neighbor deficits, and
enumerates all `9^5=59049` possible signatures. Exactly eighteen survive
the pair quotas. They are precisely the six perfect matchings at each of
the three coordinates.

For each matching the program records its 45-entry integer vector. It
checks `Bz=-4z`, `Cz=0`, and inner product ten against all three associated
signatures. All quantities are integers. The saved certificate is
`experiments/logs/grids-and-triangles/petersen-red-core-boundary.json`.

```sh
python experiments/workspace/petersen_red_core_boundary.py \
  --output experiments/logs/grids-and-triangles/petersen-red-core-boundary.json
```

An earlier independent NumPy/SymPy implementation,
`experiments/workspace/petersen_red_core.py`, uses root-gauged rook
coordinates. It obtains the same eighteen candidates and eliminates all
of them by the exact nineteen-dimensional nullspace of `C`. The final
standard-library check needs neither a nullspace algorithm nor a solver.
