# Independent audit of the nine-red-grid cover reduction

The proof in [`red_grid_limit.md`](red_grid_limit.md) reduces nine disjoint
all-red grids to a cubic graph K on twelve vertices. Its eighteen edges
are the remaining vertices U. Each all-red grid gives a two-sheeted
covering K -> K3,3. This note checks the connected-cover obstruction
independently. The general proof below does not require enumeration.

## The common triangle system

Each vertex of U has five neighbors in U. For a red triangle T in one of
the nine base grids, its six neighbors in U are partitioned by the unique
grids containing T and one of those vertices. An intersection with U has
size three or six: every base intersection has size zero or three, and
T already occupies three of the grid's nine vertices. The U intersection
is respectively one or two parallel lines of that grid. Thus these six
vertices split into two triangles in U.

For q in U, the row and column lines through its image in a base grid give
two distinct U triangles through q. Their images are different rook
lines. Because lambda=1, distinct triangles through q use disjoint pairs
of its neighbors. Degree five therefore permits exactly those two
triangles. This proves that the triangle system is independent of the
chosen base. It has twelve triangles.

Use the twelve triangles as the vertices of K; each q in U is the edge
joining its two triangles. Two triangles cannot share two vertices,
because their shared edge would have two common neighbors. Thus K is
simple and cubic. Relative to any base grid, each triangle maps onto a
row or column, with two triangles over each line. This gives the stated
two-cover of K3,3.

## At most four decks in the connected case

Suppose K is connected. Its unique bipartition has six vertices on each
side. The deck involution tau of any two-cover preserves these sides and
has no fixed vertices. Every vertex v has one neighbor in each of the
three fibers on the opposite side. Consequently

    N(tau(v)) = opposite_side \ N(v).

Group vertices on either side by their neighborhoods. No neighborhood can
occur three times: those three vertices and their three common neighbors
would form a whole K3,3 component, contrary to connectedness. Complementary
neighborhood classes have equal sizes, because a deck involution exists.

Each side therefore consists either of three complementary class pairs of
sizes 1+1, or of one pair of sizes 2+2 and one pair of sizes 1+1. Pairing
the complementary classes gives at most two possible involutions on each
side. There are at most four possible deck involutions on K.

Each of the nine base grids supplies such an involution. An involution
can appear at most twice: for any edge q of K, its paired edge tau(q) is
distinct, and each occurrence makes q and tau(q) share a neighbor in that
base grid. Three occurrences would give three distinct common neighbors,
violating mu=2. Thus connected K permits at most eight base projections.

The disconnected case is handled separately in `red_grid_limit.md`; it
consists of two K3,3 components and is excluded by the rook eigenspace
trace argument.

## Exact finite control

The script
[`grid_nine_red_covers.py`](../../experiments/workspace/grid_nine_red_covers.py)
uses only the Python standard library. A two-cover is encoded by nine
binary edge signs of K3,3. Switching fiber labels at the six base vertices
sets the signs on a spanning tree to zero. The remaining four signs give
sixteen normalized covers, so no cover is omitted.

For every normalized cover the script checks all 15*15 free involutions
preserving the two six-vertex parts. It tests the automorphism condition,
local bijectivity onto the three opposite fibers, and the complementary
neighborhood identity. Fifteen normalized covers are connected. Nine have
four deck involutions; six have one. The disconnected cover has 36.

```sh
.venv/bin/python experiments/workspace/grid_nine_red_covers.py
```

The saved exact output is
[`grid-nine-red-covers.json`](../../experiments/logs/grids-and-triangles/grid-nine-red-covers.json).
These counts agree with the general upper bound four and provide an
independent control of its hypotheses. No SAT or numerical result enters
the connected-cover contradiction.
