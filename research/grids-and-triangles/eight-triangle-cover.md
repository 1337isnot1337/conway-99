# Components of full triangles are pencils

Every connected component of full triangles consists of grids on a common full triangle. In particular, there are at most **21 full triangles** in a Conway 99-graph.

The previous [component census](full-triangle-components.md#after-the-nine-triangle-cover-exclusion) left two other possibilities, a four-cycle and $K_{2,3}$. Take an induced four-cycle of full triangles in either. Put them in the top-left two-by-two cells of a three-by-three array. Each cycle edge supplies the third parallel triangle in its grid. This completes the first two rows and first two columns. The eight triangles are disjoint. Their graph of three-edge matchings is the rook graph on these eight cells: in particular the two remaining row-end cells are matched to each other, and likewise the two column-end cells. This follows directly from the products of the forced vectors: each is minus the sum of its two generators. All other pairs are anticomplete.

## The 75 exterior points

Each point outside the 24 sees one vertex in each of the four complete grids. The cells it sees in the central two-by-two square are a partial permutation. Two marked central cells give a two-point signature. One central cell forces two peripheral cells, making a three-point signature. No central cell forces all four peripheral cells.

In each incomplete row or column the two triangles are matched. Their three matched edges have no common neighbor in the 24-point core. Each has one common neighbor outside. For an unmatched pair across these same triangles the two common neighbors are already in them. A point seeing both cells must therefore see the endpoints of a matched edge. It has a four-point signature, and the same reasoning applies to the other pair of peripheral triangles. Exactly three such points occur, joining the two sets of three matching edges by a bijection.

Temporarily complete these three special points to a triangle for labeling only. The six row and column matchings are now flat, giving the same 1,296 normalizations as for the [nine-cell configuration](nine-triangle-cover.md). The checker drops all three temporary edges before calculating quotas or testing adjacency. It identifies 59 marked cores under isomorphisms preserving the 24-point set. The central four triangles are intrinsic: they are the only triangles consisting entirely of degree-six vertices in that induced 24-point graph.

Subtract the known contributions of the three special points from $12I+2J-A-A^2$, where $A$ is the 24-point adjacency matrix. Each remaining signature lies on one of six partial permutations. For the two that used the missing cell, all multiplicities are fixed by their two-point margins. For the other four use the binary three-coordinate tables of the nine-cell proof. Any pair of cells in a partial permutation determines its permutation uniquely. Combining the tables gives 649 assignments on 21 marked cores, with 268 distinct marked attachments. At every leaf the checker verifies the full matrix of common-neighbor counts directly.

## Four neighborhoods of full triangles

Start with the exterior adjacency constraints from the nine-cell proof, using the actual $75\times24$ incidence matrix. Each central triangle $T$ already lies in two of its six grids. The other four grids each consist of $T$ and six exterior vertices. Two of the six see each vertex of $T$. The six outside $T$ form a triangular prism, with one edge inside each fiber and two parallel triangles across the three fibers.

Enumerate two points per fiber. At every core point outside $T$, the number of its neighbors among the six must be zero if it already sees $T$, and one otherwise. At each point of $T$ it must be two. For every surviving choice, enumerate the two orderings in each of the last two fibers to give every possible labeled prism. Discard a choice if an ordinary adjacent or nonadjacent pair in the enlarged core already exceeds its common-neighbor bound.

A Boolean variable for a chosen prism implies its nine edges. Every exterior point outside the fibers sees no point of $T$, so this variable also implies the presence of at least one edge from that point to the six. Each exterior point in the fibers must belong to some selected prism. These necessary conditions already contradict all 268 incidence cases. The three special points have unrestricted mutual adjacency in this test. CaDiCaL generated separate UNSAT proofs and DRAT-trim independently verified all 268. The page constraints also accept the actual graph for each of the six choices of marked line in the ordinary nine-point rook graph. Replay with `make verify-eight-triangle-cover`.

## Counting the remaining pencils

Let $k$ denote the number of components among the $t$ full triangles. In a pencil of $m$ full triangles, the number of grids with exactly two full triangles plus twice the number with three is $m-1$. Thus $g\ge 6t-(t-k)=5t+k$.

If $t=22$, the upper bound $g\le112$ allows at most two components. One then has $m\ge11$. A pencil has at most six grids on its center; if it has more than seven vertices, at least one grid has three full triangles. Every full triangle outside the component sends exactly one edge to each member: its relation is constant across the component, and it must send three edges to this three-full grid. It is disjoint from the grid.

For the center of the pencil, its 36 neighbors outside the center include all $3(m-1)$ points of the other members. Each of the $t-m$ outside full triangles must use a distinct remaining neighbor. Hence $t-m\le36-3(m-1)$, or $t\le39-2m$. This excludes $t=22$ at $m\ge11$. The earlier bound $t\le22$ now gives the result.

## At least 1,215 disjoint triangle pairs with two cross-edges

Let $n$ count these pairs. The [weighted crossing inequality](triangle-witness-bound.md) gives $8n\ge\sum_p w_p$, where $w_p$ is the integer root weight defined there. For the two grid degrees $d,e$ of a corner, assign a correction $a(d,e)$ as follows. In a corner on a full triangle give $-3/2$ if the other degree is one and $1/2$ otherwise. At a corner on no full triangle give one if either degree is one and zero otherwise. Two full triangles cannot meet.

The [seven-axis enumeration](../../experiments/workspace/grid_support.cpp) verifies $2w_p-2\sum a(d,e)\ge196$ at every eligible root, summing once per grid through the root. It checks even the larger set of all signless-support graphs with at most thirteen grids and at most one full axis.

Now sum the corrections at the nine corners of one grid. If it has $m>0$ full triangles choose them as rows, and let $j$ of its columns have degree one. Each full row contributes $3/2-2j$. Each other row contributes at least $j$. For $m=1,2,3$ the resulting lower bounds are respectively $3/2,-6,-27/2$. With $m=0$ the correction is nonnegative. Equivalently it is at least $\tfrac32(m-6\max(0,m-1))$ for each grid.

The sum of $m$ over all grids is $6t$ and the sum of $\max(0,m-1)$ is $t-k$ by the pencil classification. Hence $8n\ge 98\cdot99+9k$. Even allowing $k=0$, divisibility of $n$ by three gives **$n\ge1215$**.
