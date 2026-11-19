# The eight vertices of a rook grid with one vertex missing

Fix an induced square, and call the third vertex on each of its four sides a tip. The tips are distinct, with no edges between tips of consecutive sides. Suppose both pairs of opposite tips are adjacent. These eight vertices then induce a 3-by-3 rook graph with one missing vertex. Call their set U.

A vertex outside U adjacent to a corner cannot have another neighbor in U. Indeed the common-neighbor quota for each pair in U involving a corner is already attained in U, as can be checked in the nine-vertex rook graph. Thus there are 40 vertices with a single corner neighbor, and 51 with no corner neighbor. Each of the six pairs of tips lacks exactly one common neighbor. The possibilities are a common neighbor of all four tips, a vertex adjacent to three tips, or six distinct vertices indexed by unordered pairs of tips. The middle possibility induces the rook graph minus one edge on U and that vertex and is impossible by the integral norm argument in STATE.md.

In the last possibility, let P be the six vertices seeing a pair of tips. Each tip has 11 neighbors outside U. Of the 51 vertices, six belong to P, 32 see exactly one tip, and 13 see none. Call the latter set X and write N for X together with the four tips.

Let A be the graph adjacency matrix. The integer vector

    z = -(3I-A) 1_U - 1

has value +1 on P, -1 on N, and zero elsewhere. Since A²+A=12I+2J, it satisfies Az=-4z-2·1. Write p and n for the numbers of internal edges of P and N. A vertex in P has six more neighbors in N than in P, and a vertex in N has two more neighbors in P than in N. Counting edges between the classes gives n=p+1. The number of common neighbors in N counted over pairs in P is

    Σ_{a in N} binom(2+deg_N(a),2) ≥ 17 + 4n.

The total number of common neighbors over the same pairs is 30-p. Hence p≤1. The two opposite-tip edges already give n≥2. Therefore p=1, n=2, X is independent, and each vertex of X has precisely two neighbors in P. The P-neighborhoods of vertices of X form a multigraph on the six elements of P. Its degrees are four except for the two endpoints of the sole edge of P, whose degrees are five. Its pair multiplicities are bounded by the remaining common-neighbor quotas.

The code in broken_grid.py enumerates the possible multigraphs using these exact degrees, multiplicity bounds, and exclusion of excess common neighbors in the resulting 27 vertices. Quotienting by the eight dihedral relabelings of the square yields exactly eight cores. Every incomplete eight-vertex grid in a solution would extend to one of these cores. This assertion makes no automorphism assumption on the solution. Every core passes the tested numerical spectral bounds and has a feasible linear relaxation for its 72 exterior attachment patterns. Their extension to a full graph remains unresolved. The other four-cycle types, with zero or one opposite-tip edge, remain possible.
