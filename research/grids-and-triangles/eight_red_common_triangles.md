# Eight all-red grids with a common selected triangle system

Suppose eight all-red grids exist. Let U be the remaining 27 vertices.
The result below is conditional: if all eight base projections select the
same eighteen triangles in U, then U contains three disjoint rook grids.
Together with the eight all-red grids, these partition all 99 vertices
into eleven grids. This does not exclude such a partition.

The condition is automatic if every U vertex lies in exactly two U
triangles. It has not been established for an arbitrary eight-grid case.

## The selected triangle system

Each U vertex has six neighbors in U and one neighbor in each all-red
base grid R_i. Every base vertex has three U neighbors, so the projection
pi_i: U -> R_i has fibers of size three.

The inverse image of each red line consists of nine U vertices. The
unique-grid partition through that line splits this inverse image into
three triangles, each mapped bijectively onto the red line. A grid used
in this partition meets U in one or two parallel lines, just as in the
[nine-grid reduction](nine_red_cover_audit.md).

For each projection, the six red lines therefore select eighteen distinct
triangles in U. Every U vertex lies in two of them, one over a row and
one over a column. Degree six and lambda=1 imply that every U vertex lies
in either two or three U triangles altogether. The edges lying in no U
triangle form disjoint cycles on the vertices having exactly two triangles.

If x vertices lie in three triangles, U has 18+x/3 triangles. In particular
x is divisible by three. Every base omits x/3 triangles; these form a
partition of those x vertices into triples. When x=0, the eighteen selected
triangles are the entire U triangle system, independent of the base.

## A common system gives a three-cover

Now assume that the eighteen selected triangles are identical for every
base projection. Use them as the vertices of K; each U vertex is the edge
joining its two selected triangles. Then K is simple and cubic, with
eighteen vertices and twenty-seven edges. Every projection gives a
three-sheeted covering K -> K3,3.

No two base projections can share a three-edge fiber in K. Such a fiber
is a triple of U vertices with the same neighbor in the corresponding
base. Repeating it would give two vertices in different bases three common
neighbors, contradicting the SRG common-neighbor bound.

If K is connected, the exact finite calculation below shows that at most
four projections can have no common three-edge fiber. Eight projections
are therefore impossible in the connected case.

If K is disconnected, its components cover K3,3 with sheet numbers adding
to three. The component sizes are either 6+12 or 6+6+6. In the first case
the twelve-vertex component is a connected double cover. The
[common edge-pair lemma](nine_red_cover_audit.md#a-common-edge-pair-gives-the-stronger-auxiliary-bound-two)
says that every one of its possible deck involutions swaps the same two
edges somewhere. The corresponding two U vertices would share a neighbor
in all eight bases, again impossible.

Thus K consists of three copies of K3,3. Their line graphs are three
disjoint rook grids in U. They are induced: adding an edge to a nonedge
inside one of these rook graphs would make its two existing common
neighbors violate lambda=1. The remaining edges among these three grids
are perfect matchings, by perfect domination of every rook grid.

Because the common selected system contains the row and column triangles
of these three grids, their interfaces with each all-red base are rook
isomorphisms. The interfaces among the three new grids are not determined
by this argument. No assertion that a general U grid has such an
isomorphic interface is used.

## Exact audit of connected three-covers

The script
[`grid_eight_red_covers.py`](../../experiments/workspace/grid_eight_red_covers.py)
uses only the Python standard library. Assigning a permutation of three
sheets to each edge of K3,3 describes every three-cover. Switching labels
along a spanning tree normalizes five permutations to the identity, leaving
6^4=1,296 assignments. Of these, 1,250 are connected, 45 have component
sizes 6+12, and one has sizes 6+6+6.

For a connected K its bipartition into two nine-vertex sides is unique
up to exchange. Every new covering projection partitions each side into
three triples with pairwise disjoint neighborhoods. Conversely, any pair
of such partitions defines a covering: the edges between any left triple
and right triple form a perfect matching of size three.

There are 280 partitions of nine labeled vertices into three unlabeled
triples. The script tests every one on each side. Every connected cover
has between one and four valid partitions per side. Two pairs of partitions
share an edge fiber exactly when their left partitions share a triple and
their right partitions also share a triple.

The script computes the largest compatible family and independently
checks that no larger subset is compatible. The resulting histogram is:

| Maximum compatible projections | Normalized connected covers |
|---:|---:|
| 1 | 1,022 |
| 2 | 120 |
| 4 | 108 |

There is also a shorter certificate for each cover. The script records an
edge belonging to at most four possible three-edge fibers across all
covering projections. Distinct base projections need distinct fibers at
that edge, giving the same bound directly.

```sh
.venv/bin/python experiments/workspace/grid_eight_red_covers.py
```

The complete normalized-cover table and per-cover edge certificates are in
[`grid-eight-red-covers.json`](../../experiments/logs/grids-and-triangles/grid-eight-red-covers.json).
The audit proves only the connected/common-system statement described
above. It does not classify arbitrary U graphs or varying selected
triangle systems.
