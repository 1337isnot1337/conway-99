# At most nine grids whose six lines have multiplicity six

Call a triangle red when it belongs to six induced rook grids. Call a grid
all-red when all six of its lines are red. A hypothetical srg(99,14,1,2)
contains at most nine all-red grids. This restricts a particular kind of
grid; it does not replace the bound of 120 on all grids.

The argument uses the grid intersection and crossing-square facts proved in
[`grid_intersections.md`](grid_intersections.md).

## All-red grids are disjoint

Every graph edge lies on twelve induced squares. A red triangle belongs to
six grids, each contributing two squares through any of its edges. These
squares are distinct: different grids cannot share a nonadjacent pair.
Therefore every square containing a red edge belongs to a grid.

Two grids meeting only at a point have a perfect matching between their
opposite four-cycles. At least two edges are preserved by that matching,
and each gives a crossing square outside every grid. Thus an all-red grid
cannot meet any other grid in just one point.

At a point p of an all-red grid R, its two lines have degree six in the
seven-axis graph D_p. There can be no edge of D_p disjoint from these two
axes: it would give a grid meeting R only at p. Hence D_p consists exactly
of the eleven edges incident to either of those two axes. Its other five
vertices have degree two. In particular p belongs to precisely two red
triangles and to only one all-red grid. Distinct all-red grids are disjoint.

## Ten disjoint grids force an eleventh

Suppose ten all-red grids exist, and let U be the remaining nine vertices.
Every exterior vertex has exactly one neighbor in any grid. Each vertex in
U therefore has ten neighbors outside U and four inside U.

A vertex in one of the ten grids has four neighbors in its own grid and
one in each of the other nine. Its remaining neighbor lies in U. Thus no
vertex outside U is a common neighbor of two vertices in U. The full
common-neighbor equations hold inside U, so U is an srg(9,4,1,2), namely
the three-by-three rook graph. The eleven grids partition the vertices.

## Every matching preserves the rook graph

Let R be one of the ten all-red grids, let T be any line of R, and let S
be another grid in the partition. The cross-edges between R and S are a
perfect matching. The six grids through T partition the 36 neighbors of T
outside T into six-vertex groups: their intersections are precisely T, and
each contributes six such neighbors.

Choose q in S matched to a vertex of T. There is a unique grid G through
T and q. If S is all-red, G cannot meet S in just one point, so their
intersection is a triangle. If S=U, each intersection of G with one of
the ten all-red grids has size zero or three. It follows that |G∩U| is a
multiple of three. It is nonzero, and the distinct grids G,U cannot
intersect in more than a triangle, so it is three.

In either case the triangle G∩S consists exactly of the three vertices
matched to T. Every line of R is therefore mapped to a line of S. All
matchings between the eleven partition grids are rook-graph isomorphisms.

For each partition grid take its four-dimensional adjacency eigenspace of
eigenvalue one. Their direct sum is invariant under the full adjacency
matrix, has dimension 44 and trace 44, and is orthogonal to the constants.
Its eigenvalues must consequently be three and minus four. If r denotes
the multiplicity of three, its trace is 7r−176. The equation 7r−176=44
requires 7r=220, which has no integer solution.

Ten all-red grids are impossible. The earlier proof excludes the special
all-red partition arising at equality in the 121-grid bound. The argument
here applies whenever ten all-red grids exist, without a total-grid-count
assumption.
