# Four missing pairs opposite a grid

Suppose a grid contains a root, and exactly four of the ten pairs on the other five axes fail to form grids through that root. **The four missing pairs must form a four-cycle with one isolated axis.** The other five shapes on the passive axes all fail the exterior Gram conditions. No automorphism of the Conway graph is assumed.

It follows that **at most ten grids pass through a vertex outside full triangles**. A vertex with exactly eleven grids must have one full axis. Its eleven axis pairs consist of the full six-edge star, plus five of the six edges on four of its leaves.

## Coordinates and signed axes

Use the central four-point cell and ten passive four-point cells from the [three-missing-pair proof](eleven-grid-bound.md). For each of the five shapes in the table, the signless incidence matrix of the four missing edges has trivial kernel. Remove leaves successively, then use the equations around the odd cycle if one remains. Thus each of the ten passive cells has a perfect matching to the central four points. Label each passive vertex by its central neighbor, and write $p_0$ for the opposite-corner involution of the central square.

Each passive point with coordinate $x$ has five passive neighbors with coordinates $0,1,2,3,p_0(x)$ as a multiset. Enumerate the interfaces between passive grids and fill the maps from missing cells to grids exactly as in the three-missing-pair proof. The missing union has four vertices of each coordinate. Within a coordinate group enumerate all simple four-vertex graphs with the required degree sequence. Between two distinct groups enumerate every binary four-by-four matrix with the required row and column sums. This fills all 44 far points. Adding edges cannot repair an exceeded common-neighbor quota or a missing cell with more than two internal edges.

Early signed-axis tests reduce the number of full graphs to inspect. Assign to each passive axis the possible positive and negative halves in its four incident cells. Each half contributes two points per cell. Each central coordinate must occur in exactly two positive halves, by its common-neighbor count with the signed near vertex. For a grid cell the two halves must use a side partition of its square. Exchange the names of the signs on each axis to normalize the first half.

For a given axis, let $U_+,U_-$ be its two sets of eight far points. A passive point on that axis can have at most one far neighbor in each set. Indeed it already spends one unit of the common-neighbor-plus-edge quota at its own signed near vertex through adjacency, and at the opposite signed near vertex through their common near mate. A point away from the axis can have at most two in each set. Two distinct points in the same $U_+$ or $U_-$ have that signed near vertex as a common neighbor. The known far edges must leave one unit available for it. These upper bounds apply to the partial graph as soon as the missing-to-grid maps have been placed, and again after the missing union has been filled.

Finally choose one signing per axis. Two axes have just one common four-point cell, in which all four sign combinations must occur. Equivalently their positive halves meet in exactly one point. This gives all candidate signed incidences with the fourteen near vertices. Add the root to obtain an induced adjacency matrix $H$ of order 59. Its exterior incidence Gram $12I+2J-H-H^2$ must be entrywise nonnegative, positive semidefinite and have rank at most 40.

For the path, star, and disjoint triangle and edge, the checker assigns the near signs before filling the missing union. In that order it adds the ten signed vertices and their five mate edges to the partial graph. The same pair quota then applies directly at every edge insertion. The check on the 59-point Gram uses the ordinary adjacency matrix reconstructed from the emitted rows and five positive sign masks.

| Missing pairs | Grid assignments | Symmetry classes | Simultaneous near labelings | Possible exterior Grams |
|---|---:|---:|---:|---:|
| Triangle with a pendant edge | 29,544 | 4,233 | 206 | 0 |
| Five-vertex tree of degrees $3,2,1,1,1$ | 22,600 | 3,253 | 196 | 0 |
| Five-vertex path | 19,411 | 2,947 | 980 | 0 |
| Triangle and a disjoint edge | 59,100 | 1,596 | 32 | 0 |
| Four-edge star | 97,336 | 1,757 | 1,136 | 0 |

The symmetry reduction permutes the five axes preserving the missing edge set and relabels the coordinates by symmetries of the central square. All 2,550 simultaneous assignments have entrywise nonnegative exterior Grams. None passes exact positive semidefiniteness. In the far-first order the triangle with a pendant edge gives 56,577,990 completed far graphs passing the early tests, of which 1,834 allow each axis separately. The corresponding numbers for the tree of degrees $3,2,1,1,1$ are 148,133,244 and 4,272.

These shapes exhaust the connected trees on five vertices and the four-edge graphs on five vertices containing a triangle. The remaining shape is a four-cycle and an isolate. The signless incidence argument permits nonzero alternating deviations on that cycle.

## Exactly eleven grids at a root

Of the 148 unlabelled ten-edge graphs on seven axes, twenty pass the earlier [four disjoint missing, full-triangle and signless-incidence restrictions](eleven-grid-bound.md#the-twelve-grid-supports). In five, some missing cell has no possible internal degree sequence for four points spanning at most two edges. Fourteen of the remaining fifteen have a central grid opposite a triangle with a pendant edge, the tree of degrees $3,2,1,1,1$, or a five-vertex path. This leaves one missing-axis graph up to isomorphism. Its complement consists of a six-edge star together with a $K_4$ minus one edge on four leaves. The center corresponds to a triangle in six grids. At a point outside such triangles at least $84-4\cdot10=44$ nonneighbors therefore generate the graph with it.

Run `make verify-four-missing-grid-cones` for the [matching and matrix checker](../../experiments/workspace/sparse_grid_cones.py), [far-graph enumerator](../../experiments/workspace/central_grid_fill.cpp), [signed-axis checks](../../experiments/workspace/central_grid_axes.hpp), and [eleven-grid support classification](../../experiments/workspace/eleven_grid_supports.py).
