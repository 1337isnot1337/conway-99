# An upper bound of 120 induced grids

Let a grid mean an induced 3-by-3 rook graph in a hypothetical strongly regular graph with parameters (99,14,1,2). Write g for the number of grids. There are at most 120 grids, and at least 1,998 unordered pairs of nonadjacent vertices generate all 99 vertices under two-neighbor bootstrap percolation.

## Grids and common neighbors

Within a grid, all pairs already have their required number of common neighbors. An exterior vertex therefore has at most one neighbor in the grid. Counting the 9·10 edges leaving the grid shows that each of the 90 exterior vertices has exactly one. Two nonadjacent vertices in a grid generate the grid by repeatedly adding common neighbors. Consequently two distinct grids meet in either zero vertices, one vertex, or one full triangle. The same closure criterion says a nonadjacent pair outside any common grid generates the entire graph. See [Ibrahim, LaFayette and McCall, Lemma 4.9 and Theorem 4.19](https://ajc.maths.uq.edu.au/pdf/93/ajc_v93_p060.pdf). The qualitative implication that two-vertex percolation occurs was also derived from Makhnev's result in [earlier work](https://raw.githubusercontent.com/YesterdaysLemon/conway-99-research/main/STRUCTURE.md).

The 4,158 nonedges are the diagonals of 2,079 induced squares. Each grid contains nine squares, all belonging uniquely to that grid. Write b = 2,079 − 9g for the count of squares in no grid.

## Counting pairs of grids meeting in a point

At a vertex p, form a seven-vertex graph D_p whose vertices are the triangles through p. Two triangles form an edge in D_p when they lie in a common grid. The grid is unique because the two triangles together contain a nonadjacent pair. Write e_p for its edge count and m_p for its number of unordered pairs of disjoint edges. Then Σe_p = 9g, and Σm_p counts exactly the unordered pairs of grids meeting in a single vertex.

Let two such grids intersect at p. In each grid the four vertices nonadjacent to p induce a four-cycle. A vertex of either four-cycle cannot see p or a neighbor of p in the other grid, since its two common neighbors with p are already in its own grid. Its unique neighbor in the other grid therefore belongs to the opposite four-cycle. This gives a perfect matching between the two four-cycles. Under any bijection of four points, at least two of the four edges of one cycle map to edges of the other, as there are only two nonedges. Each overlapping edge gives a square crossing the grids. The triangle tips on its opposite internal sides are neighbors of p on distinct triangles through p. They are nonadjacent. In a rook grid the tips of opposite sides of any square are adjacent, so the crossing square belongs to no grid.

Conversely, such a square can account for at most four witnesses. Choose one of its two pairs of opposite sides. Their triangle tips must be nonadjacent, and hence have only two choices of a common neighbor p. For each choice, p and either endpoint of the corresponding side form a nonadjacent pair determining at most one grid. Thus

    Σ m_p ≤ 2b.

All simple graphs on seven vertices with e edges and m pairs of disjoint edges satisfy m ≥ 5e − 35 and 4m ≥ 25e − 195. The minimum values of m, in increasing order e = 0 to 21, are

    0 0 0 0 0 0 0 4 8 12 15 20 27 33 39 45 55 65 75 85 95 105.

The integer enumeration in grid_intersections.py checks every one of the 2^21 subsets of the edges of K7. The first inequality gives 45g − 3,465 ≤ 4,158 − 18g and hence g ≤ 121.

## Excluding equality

If g = 121, both local inequalities have equality after summing over p. Both therefore have equality at each p. Their joint equality graphs consist of the 11 edges incident to either of two special vertices in K7. The same enumeration verifies this classification. The number of grids containing a given triangle is its degree in D_p at each of its three points. Color triangles that lie in six grids red. The other triangles lie in two grids and are blue. Color each graph edge by its unique triangle. Every point lies on exactly two red triangles and the grid-eligible pairs there are exactly those involving at least one red triangle. Also, equality in the crossing-square count forces each square outside a grid to have all four possible witnesses. In particular each of its two opposite-side tip pairs is nonadjacent. Every square containing a red edge lies in a grid, since the six grids through that edge cover its twelve squares (two per grid).

In any grid at least one parallel class consists entirely of red triangles. Otherwise two blue triangles of different directions would meet and define a grid. Suppose there is both a red and a blue triangle in the other parallel class. Take a point p on one of the blue triangles. The grid under consideration is a red-blue edge in D_p, which has a disjoint edge obtained by pairing the other red triangle with a different blue triangle. The resulting two grids intersect only in p. At least two edges of the first grid's four-cycle far from p then belong to crossing squares outside all grids, so both must be blue. Yet the two far edges perpendicular to the blue triangle are red, and at least one of the two parallel far edges is red by the mixed-color assumption. This contradiction leaves two types of grid. All six lines are red, or exactly one whole parallel class is red and the other whole class is blue.

The unique grid through the two red triangles at any point is therefore all-red. Conversely each point of any all-red grid lies on its unique pair of red triangles there. Thus eleven disjoint all-red grids partition the 99 points. The remaining 110 grids each contain three parallel red triangles, in three different all-red grids. Indeed two parallel triangles from the same all-red grid would give a nonadjacent pair common to two distinct grids.

For each pair of all-red grids the cross-edges are a perfect matching. It can map at most six triangles of one grid onto triangles of the other. Each of the 110 remaining grids gives three such transported triangle pairs. Different remaining grids cannot use the same pair because their intersection would contain two full disjoint triangles. The total is 330 = 6·55, so every matching transports every triangle. In particular it is an isomorphism of rook graphs.

In each of the eleven all-red grids take the four-dimensional eigenspace of its internal adjacency with eigenvalue 1. The direct sum is invariant for the full adjacency matrix A since all the matchings are rook isomorphisms. Its dimension and the trace of A on it are both 44. It is orthogonal to the constants, so A has eigenvalues drawn from 3 and −4 on it. If r is the multiplicity of 3, then 7r − 176 = 44, which is impossible. This rules out 121 grids.

Finally, each grid accounts for 18 distinct nonpercolating nonedges. The bound gives at least 4,158 − 18·120 = 1,998 percolating nonedges. This count applies under the existence assumption and leaves that assumption undecided.

## Counting pairs of triangles with two cross-edges

Write n for the number of unordered pairs of disjoint triangles joined by exactly two edges. Those edges form a matching. Equivalently n counts square and opposite-side choices for which the two triangle tips are nonadjacent. In the witness argument above each such opposite-side choice has at most two common centers. Consequently Σm_p ≤ n.

At a root p, fix two of its seven triangles, with signed neighbors a,a′ and b,b′. The four remaining square corners opposite p have labels (a,b), (a,b′), (a′,b), (a′,b′). Among them there are four potential edges changing just one sign. If three are present, neither diagonal can be present, as each diagonal would produce a second triangle on a present edge. The nine vertices then induce the rook graph with one edge deleted, excluded by the integral eigenvector argument in STATE.md. If all four edges are present there is a grid. Otherwise at most two are present.

In the four squares at p specified by these labels, each present sign-changing edge accounts for a link between opposite tips in exactly two squares. For example, (a,b) and (a′,b) are adjacent precisely when a′ is adjacent to the triangle tip on the side from b to (a,b). This equivalence follows from the uniqueness of the outer vertex with near neighbors a′ and b. Thus a two-triangle choice at p outside a common grid gives at least four missing opposite-tip links across its four squares. Summing over the roots counts each square-side choice four times. This proves n ≥ 2,079 − 9g.

The seven-axis table also gives 4m_p ≥ 15e_p − 90. For g ≤ 100 the first lower bound on n is at least 1,179. For g ≥ 101 the crossing witnesses give 4n ≥ 135g − 8,910 ≥ 4,725. Hence n ≥ 1,179 in every case. The external research ledger linked above gives an earlier lower bound of 708.

## Strengthening the count to 1,188

Fix a root p. For each axis pair e = ij, let h_e be the indicator of the nine vertices comprising p, its four neighbors on the two axes, and its four far vertices on these axes. Put W = 3I − A + J/9 and z_e = Wh_e. The matrix identity for A gives W² = 7W. Also W(A+4I) = −2J + (14+4)J/9 = 0.

The sum of h_ij over j distinct from i equals (A+4I) times the indicator of the triangle containing p and its two neighbors on axis i. This follows by counting coordinates at p, near vertices and far vertices. Hence at each axis the sum of the six incident vectors z_e is zero. Further, ||z_e||²/7 = 36 − 2|E(H_e)|. If z_e vanishes, every patch vertex has internal degree four and every vertex outside has exactly one neighbor in the patch. All common neighbors of pairs in the patch are therefore inside, so the patch is the unique strongly regular graph with parameters (9,4,1,2), the rook grid. Conversely a grid has z_e = 0 by its internal degrees and perfect domination.

Let F be the complement of D_p, and let C be the unoriented vertex-edge incidence matrix of F over the rationals. The support of each coordinate across the vectors z_e belongs to ker C, and every edge of F occurs in the support of at least one such vector. Consequently deleting any edge preserves the rank of C. The rank is seven minus the number of bipartite connected components, counting isolated vertices. Indeed, a left-kernel vector alternates sign across each edge, giving one free scalar for a bipartite component and none for an odd-cycle component.

Restrict the seven-axis enumeration to graphs satisfying this edge-deletion criterion. grid_support.cpp checks all 2^21 labeled graphs. An independent check on the 1,044 seven-vertex graphs of the NetworkX graph atlas gives the same minima. With a dash indicating an impossible support, the resulting minimum m_p for e_p = 0 to 21 is

    0 0 0 0 0 2 0 4 8 12 17 20 27 34 42 48 – 67 – – – 105.

In particular m_p ≥ 4e_p − 24. If g ≤ 99, n ≥ 2,079 − 9g ≥ 1,188. If g ≥ 100, n ≥ Σm_p ≥ 36g − 2,376 ≥ 1,224. This proves n ≥ 1,188.

## The bound at each root

The incidence-support argument and the full four-cell transport enumeration together give a pointwise restriction. Every vertex belongs to at most 15 grids. In particular every vertex has at least 24 distinct nonneighbors with which it generates the entire graph.

For the additional argument write B_e for the four far vertices of cell e. The vectors z_e vanish at the root and its 14 neighbors. At w in B_f their coordinates equal 2 minus its internal degree in B_f if e=f, minus its number of neighbors in B_e if e and f share exactly one axis, and 1 minus its number of neighbors in B_e if e and f are disjoint. For a nongrid cell there are at most two internal edges. To check this last assertion directly, a diagonal between opposite sign pairs cannot coexist with an edge changing one sign: its two endpoints and the third point would give three common neighbors for a pair consisting of a near and a far point, or duplicate a triangle. Alternatively check the six possible far edges against all 36 codegree bounds. In the remaining case of only sign-changing edges, three edges give the excluded grid minus one edge.

Suppose the support F has just four edges. Each nonisolated axis has degree at least two since its incident vectors sum to zero. A simple graph with four edges of minimum nonisolated degree two must be a four-cycle. Write z for one of its vectors: on opposite edges the vectors are equal, while consecutive edges have opposite vectors. At any point of a missing cell, comparison with the disjoint opposite cell gives internal degree at least one. Since there are at most two internal edges, each missing cell induces a perfect matching. The vector z is identically +1 on two missing cells and −1 on the other two. Its squared norm is 28 by the norm formula above.

At every point of a present cell the neighbors in the two directions of its internal square exhaust its far-neighbor quotas on either of its near axes. Thus a point in a present cell touching a missing axis pair has no neighbors in that missing cell, and z vanishes there. The remaining three present cells are the three pairs among the three axes outside the four-cycle. Each of their twelve vertices has z between −1 and 1, by applying the disjoint-cell formula to both signs of z. Their contributions together must bring the norm from 16 to 28, so all twelve are nonzero. In each of those three cells the sum of z is zero. Indeed each vertex of a missing cell has one neighbor in that present grid by perfect domination, which must be in its four-cell since the two axis pairs are disjoint. Consequently each four-cell has two positive and two negative vertices.

Fix a vertex w in one of the three present cells. By the disjoint-cell formula it has four neighbors in the missing cells, all of sign opposite its own. No other one of the three present cells has a neighbor of w since their axes intersect. Since Az=−4z, the two internal neighbors of w have opposite signs to one another. It follows that the sign pattern on that square is precisely one of its two signed coordinates, up to negation. At either near vertex of each of the three remaining axes, the equation Az=0 there requires that patterns selecting that axis occur equally often in each orientation. A cell whose pattern selects the other coordinate contributes zero. Thus each axis is selected an even number of times. There are three cells and each selects exactly one axis, a contradiction.

The support table excludes 16 and 18 through 20 grids. The 21-grid case was independently eliminated by the two computational reductions described in STATE.md and root_cover_audit.py. The latter reproduces all four sign orbits (sizes 1, 105, 120, 30), all three ternary transports in each, and zero feasible character assignments in all twelve cases. This proves the stated upper bound of 15. Each grid accounts for four nonneighbors at the root, giving 84−4·15=24.

The same argument excludes a support F that is just a six-cycle. The missing cells again alternate ±z, and each missing vertex has internal degree one by comparison with a disjoint same-sign cell. Every present cell meets at least one missing edge since only one axis lies outside the cycle. Hence the norm is 24 instead of the required 28.
