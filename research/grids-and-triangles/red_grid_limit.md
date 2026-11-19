# At most eight grids whose six lines have multiplicity six

Call a triangle red when it belongs to six induced rook grids. Call a grid
all-red when all six of its lines are red. A hypothetical srg(99,14,1,2)
contains at most eight all-red grids. This restricts a particular kind of
grid; it does not replace the bound of 120 on all grids.

The argument uses the grid intersection and crossing-square facts proved in
[`grid_intersections.md`](grid_intersections.md). The proof below is
combinatorial and spectral; the small covering enumeration is an independent
check, not a premise.

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

Every vertex outside a grid has exactly one neighbor in it. It has at most
one because each pair of grid vertices has already used its full
common-neighbor quota inside the grid. The grid sends 9(14-4)=90 edges to
its ninety exterior vertices, so equality holds for every exterior vertex.

The six grids through a red triangle T partition its 36 exterior neighbors
into six-vertex sets. Two such grids meet exactly in T, and each has six
vertices outside T, all adjacent to a vertex of T. Consequently, for every
exterior neighbor q of T there is a unique grid containing both T and q.

The perfect matching between two disjoint all-red grids is a rook-graph
isomorphism. For a line T in the first grid and a matched vertex q of the
second, the unique grid through T and q meets the second grid in a triangle,
not just q. That triangle is precisely the image of T under the matching.
Thus all lines are preserved.

## Nine all-red grids leave a graph on eighteen vertices

Suppose nine all-red grids R_1,...,R_9 exist. Let U be the eighteen remaining
vertices. Each vertex of U has one neighbor in every R_i and therefore five
neighbors in U. Each vertex in an R_i has four neighbors in its own grid,
one in each of the other eight grids, and two in U.

Fix R_i. The map pi_i from U to R_i sending a vertex to its unique neighbor
has fibers of size two. For every line T of R_i, its six-point inverse image
splits into two disjoint triangles of U.

To prove the last assertion, take q in that inverse image and let G be the
unique grid containing T and q. Its intersection with each R_j, j != i,
is either empty or a triangle: a singleton is forbidden by the all-red
property. These intersections are disjoint lines of G, hence parallel to T.
Therefore G meets U either in a single parallel line or in the two parallel
lines outside T. As q varies, the exterior-neighbor partition for T shows
that these lines partition its six-point inverse image. There are exactly
two triangles, each mapped bijectively onto T.

For q in U, the row and column of R_i through pi_i(q) give two distinct
triangles of U through q. They cannot be the same triangle: all three
vertices of a common triangle would have to map to the intersection of
that row and column, whose fiber has only two vertices. Distinct triangles
cannot share an edge because lambda=1. Since q has degree five in U, it
lies in exactly two triangles, using four of those neighbors. Its remaining
edge lies in no triangle. The remaining edges form a perfect matching M.

There are exactly twelve triangles in U. Make a graph K whose vertices are
these triangles and whose edges are the eighteen vertices of U: a point
joins the two triangles containing it. Two triangles share at most one
point, so K is simple. Each triangle has three points, so K is cubic. The
edges of U lying in triangles form the line graph L(K), and

    U = L(K) + M.

## Every base grid gives a double covering of K3,3

For each i, the two triangles over every row of R_i form one side of a
six-plus-six bipartition of K, and the triangles over columns form the
other. Every triangle of U is one of the row or column triangles for this
projection: each point already lies in exactly those two triangles.

A row triangle has its three points mapped to the three different columns.
Thus its three neighbors in K map to three different column vertices.
The same holds with rows and columns exchanged. The projection is therefore
a two-sheeted covering K -> K3,3, with two vertices over each base vertex
and two edges over each base edge.

Swapping the two points of every fiber gives a fixed-point-free graph
automorphism tau_i of K. It also swaps the two edges above each edge of
K3,3. On the eighteen vertices of U, tau_i pairs exactly the points with
the same neighbor in R_i.

No involution tau can occur for three of the nine grids. If it did, any
point q and its distinct partner tau(q) in U would have a common neighbor
in each of those three disjoint grids, exceeding the maximum of two.

## A connected covering has at most four such involutions

Suppose K is connected. Its bipartition into two six-point sets is unique
up to exchange, so every tau_i preserves this same bipartition. For a
vertex v, its three neighbors contain one point of each opposite fiber;
the neighbors of tau_i(v) contain the other points. Hence

    N(tau_i(v)) = opposite bipartition class minus N(v).

No three vertices on one side of a connected K have the same neighborhood.
If they did, those three vertices and their three common neighbors would
form a cubic K3,3 component, using all degrees of its six vertices and
disconnecting the twelve-vertex graph.

Group the six vertices on one side by equal neighborhoods. Each class has
size at most two, and the existence of any tau_i pairs each class with the
class having its complementary neighborhood. Paired classes have equal
sizes. There are only two possible size patterns:

    (1+1) + (1+1) + (1+1),
    (2+2) + (1+1).

The first permits one pairing of vertices; the second permits two. Thus
there are at most two possible restrictions of tau_i to each side, and at
most four possible involutions on all of K. Some pairs of restrictions may
fail to preserve edges; this only reduces the count.

Each involution can occur at most twice, so these four possibilities can
account for at most eight all-red grids. The assumed nine are impossible
when K is connected.

## The disconnected covering is also impossible

Every connected component of a covering maps onto the connected base K3,3.
Since there are only two sheets, a disconnected K is exactly two copies of
K3,3. Its line graph consists of two disjoint rook grids X and Y. The
matching M joins them: an added edge inside either rook grid would turn a
pair with two common neighbors into an adjacent pair, contradicting
lambda=1. Thus the nine R_i together with X and Y partition all 99 vertices
into eleven grids.

Every interface from an R_i to X or Y is a rook-graph isomorphism. The
covering restricted to either component K3,3 is a bijection preserving its
rows, columns, and edges, and the resulting map on U is the matching to
R_i. The interfaces between the R_i are already isomorphisms. Only M, the
interface between X and Y, has not yet been shown to preserve the rook
graph.

Identify the adjacency matrix inside each grid with the same rook matrix B.
Let F be the matching matrix from R_1 to X. In the (R_1,Y) block of the
full identity

    A^2 + A = 12 I + 2 J,

every term except FM preserves the eigenspaces of B: the terms through any
other R_i are products of rook isomorphisms, and the terms staying in R_1
or Y include B and a rook isomorphism. The right side preserves those
eigenspaces as well. Thus FM preserves them. Since F is an invertible rook
isomorphism, M also preserves them. Equivalently, BM=MB, so the permutation
M is itself a rook-graph isomorphism.

For each of the eleven grids take its four-dimensional B-eigenspace of
eigenvalue one. Their direct sum is invariant under A, has dimension 44
and trace 44, and is orthogonal to the constants. Its eigenvalues must be
three and minus four. If r is the multiplicity of three, its trace is
7r-176. Equality with 44 would require

    7r = 220,

which is impossible for an integer r. This excludes the disconnected case.
Both cases contradict nine all-red grids, proving the bound of eight.

## Independent finite check

`experiments/workspace/grid_nine_red_covers.py` exhausts the sixteen
spanning-tree-normalized double coverings of K3,3 and the 225 products of
fixed-point-free involutions on their two six-point parts. It checks the
covering condition and complementary-neighborhood property directly.
Among the fifteen connected normalized covers, nine have four possible
deck involutions and six have one. The disconnected cover has thirty-six.
These are labeled, normalized counts; isomorphic covers can occur more
than once.

The checker uses only Python's standard library:

```sh
python experiments/workspace/grid_nine_red_covers.py
```

Its counts independently check the connected-case bound. The proof uses
the elementary neighborhood-class argument, so its validity does not depend
on the enumeration or an isomorphism package.
