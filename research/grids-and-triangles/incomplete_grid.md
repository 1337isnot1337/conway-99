# The eight vertices of a rook grid with one vertex missing

Fix an induced square, and call the third vertex on each of its four sides a tip. The tips are distinct, with no edges between tips of consecutive sides. Suppose both pairs of opposite tips are adjacent. These eight vertices then induce a 3-by-3 rook graph with one missing vertex. Call their set U.

A vertex outside U adjacent to a corner cannot have another neighbor in U. Indeed the common-neighbor quota for each pair in U involving a corner is already attained in U, as can be checked in the nine-vertex rook graph. Thus there are 40 vertices with a single corner neighbor, and 51 with no corner neighbor. Each of the six pairs of tips lacks exactly one common neighbor. The possibilities are a common neighbor of all four tips, a vertex adjacent to three tips, or six distinct vertices indexed by unordered pairs of tips. The middle possibility induces the rook graph minus one edge on U and that vertex and is impossible by the integral norm argument in [`STATE.md`](../../STATE.md).

In the last possibility, let P be the six vertices seeing a pair of tips. Each tip has 11 neighbors outside U. Of the 51 vertices, six belong to P, 32 see exactly one tip, and 13 see none. Call the latter set X and write N for X together with the four tips.

Let A be the graph adjacency matrix. The integer vector

    z = -(3I-A) 1_U - 1

has value +1 on P, -1 on N, and zero elsewhere. Since A²+A=12I+2J, it satisfies Az=-4z-2·1. Write p and n for the numbers of internal edges of P and N. A vertex in P has six more neighbors in N than in P, and a vertex in N has two more neighbors in P than in N. Counting edges between the classes gives n=p+1. The number of common neighbors in N counted over pairs in P is

    Σ_{a in N} binom(2+deg_N(a),2) ≥ 17 + 4n.

The total number of common neighbors over the same pairs is 30-p. Hence p≤1. The two opposite-tip edges already give n≥2. Therefore p=1, n=2, X is independent, and each vertex of X has precisely two neighbors in P. The P-neighborhoods of vertices of X form a multigraph on the six elements of P. Its degrees are four except for the two endpoints of the sole edge of P, whose degrees are five. Its pair multiplicities are bounded by the remaining common-neighbor quotas.

The code in [`broken_grid.py`](../../experiments/workspace/broken_grid.py) enumerates the possible multigraphs using these exact degrees, multiplicity bounds, and exclusion of excess common neighbors in the resulting 27 vertices. Quotienting by the eight dihedral relabelings of the square yields exactly eight cores. Every incomplete eight-vertex grid in a solution would extend to one of these cores. This assertion makes no automorphism assumption on the solution. Every core passes the tested numerical spectral bounds and has a feasible linear relaxation for its 72 exterior attachment patterns. Their extension to a full graph remains unresolved. The other four-cycle types, with zero or one opposite-tip edge, remain possible.

## The 661 marked incidence profiles

The eight cores also determine all incidences between the first fourteen points (the eight grid points and the six members of $P$) and the other 85, up to 661 choices. No symmetry of the full graph is imposed.

Let $A$ be a 27-point core from the preceding construction and $R=12I+2J-A-A^2$. Each of the 72 exterior vertices marks exactly one of the original eight points. Its marks in $P$ must form a clique in the support of $R$ restricted to pairs in $P$. In every core that support is either a four-cycle with all four multiplicities one or two disjoint pairs of multiplicity two. Hence no vertex marks three points of $P$, and exactly four vertices mark two. Assign the four pair occurrences their marked points among the original eight. The entries of $R$ between those eight and $P$ now determine how many vertices at each anchor have each single mark. The diagonal entries at the anchors give the counts with no mark in $P$. The thirteen points of $X$ already have their two marks in $P$.

For each assignment the verifier checks the complete exterior Gram identity on the fourteen points and the pointwise common-neighbor upper bounds. It then canonicalizes the partial graph with the corners, tips, $P$, $X$ and the remaining vertices as five color classes. The following counts distinguish the eight original 27-point cores.

| Core ID | Anchor assignments after feasibility checks | Marked profiles up to isomorphism |
| ---: | ---: | ---: |
| 0 | 157 | 157 |
| 1 | 224 | 120 |
| 2 | 90 | 27 |
| 3 | 219 | 116 |
| 4 | 256 | 76 |
| 5 | 225 | 36 |
| 6 | 340 | 90 |
| 7 | 256 | 39 |
| Total | 1,767 | 661 |

All eight 27-point cores admit integral exterior incidence allocations. The eight explicit 72-by-27 binary matrices certify this directly. Each gives the exact residual common-neighbor matrix on the entire core and each pair of exterior rows overlaps in at most two positions. Each of these specific assignments already fails a local adjacency quota. For exterior point $w$ the required number of exterior neighbors attached to core point $i$ is $(2-B-BA)_{wi}$. A candidate exterior neighbor $v$ must meet $w$ in at most one core point and its marks must fit the remaining quotas of $w$, with the same test in the reverse direction. Counting the eligible candidates for the indicated pair gives fewer than required in each example. Other assignments at these cores remain possible.

Run the [profile and certificate checker](../../experiments/workspace/incomplete_grid_profiles.py) to regenerate the table and inspect the [integer examples](../../experiments/workspace/incomplete-grid-incidences.json).
