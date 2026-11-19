# Fourteen independent vertices through a neighborhood transversal

Fix any root o. Its neighbors are seven disjoint edges. Choose one endpoint from each edge uniformly and independently, and call the seven chosen endpoints T. The 84 vertices at distance two have distinct labels consisting of two nonmate neighbors of o. Exactly 21 labels avoid T. Let H be the graph they induce. An independent set in H can be adjoined to T.

The full distance-two graph has 504 edges, since every vertex has twelve neighbors there. For each vertex, exactly two of those twelve neighbors have a label meeting its label. In fact, for each of its two anchors, the edge to that anchor lies in a unique triangle and its third vertex is in the distance-two graph. Thus 84 full-shell edges have a shared anchor, and the other 420 have disjoint labels. Each of the former occurs in H with probability at most 1/8, and each of the latter with probability at most 1/16. Opposite ends of a matched near edge prevent occurrence altogether. Hence the expected number m of edges in H is at most 147/4.

Every edge with disjoint labels is contained in exactly one triangle wholly within the distance-two graph. The three labels of such a triangle are pairwise disjoint because an edge with a shared anchor already has that anchor as its unique common neighbor. Consequently there are exactly 140 such triangles. Each occurs in H with probability at most 1/64, so the expected triangle count t in H is at most 35/16.

For a triangle-free graph on n vertices with independence number at most a, Radziszowski and Kreher proved that the number of edges is at least 6n−13a. Source: [Minimum triangle-free graphs](https://repository.rit.edu/article/643/). If H had independence number at most six, successively deleting a vertex of a surviving triangle would yield a triangle-free graph after r ≤ t deletions, with at least 2r original edges lost. Hence m ≥ 6(21−r)−78+2r ≥ 48−4t. But the expectation of m+4t is at most 91/2, strictly less than 48. Thus for every root at least one transversal gives an independent seven-set in H. Together these give a coclique of size fourteen with seven vertices in the root's neighborhood.

This gives a necessary condition and an unrestricted search normalization. It does not establish existence or nonexistence.

## Extending the transversal to a maximal coclique

Extend the fourteen vertices to a maximal coclique I, and write h for its size. The original root b has seven neighbors in I, the maximum possible because its neighborhood consists of seven edges. Each vertex x outside I gives a nonempty block of size d(x) consisting of its neighbors in I. Each point occurs fourteen times and each pair occurs twice. Thus the sums of 1, d and d(d−1) over outside vertices are 99−h, 14h and 2h(h−1). The Hoffman bound gives h ≤ 22. Equivalently the sum of (d−4)² equals 2(h−22)(h−36); for h=22 it would force every d=4.

There is also no h=21 for this choice of I. The sum of (d−3)(d−4) is 2(h−22)(h−27), which at h=21 is 12. All summands are nonnegative integers, and d(b)=7 already contributes 12. Every other block would therefore have size three or four. For any outside vertex x, summing its common-neighbor count with the points in I gives
     
    sum of d(y) over outside neighbors y of x = 2h−d(x).

At b this says the sizes of its seven outside neighbors sum to 35, exceeding 7·4. Consequently every root admits a maximal coclique of size between fourteen and twenty containing seven of its neighbors. This upper bound concerns the stated choice of coclique.

The seven additional independent vertices used before maximal extension have labels consisting of seven different edges on seven points. There are 65 isomorphism classes for this pattern. hemisphere_cases.py exhausts the 116,280 labeled choices and verifies each multiplicity by the orbit-stabilizer formula.
