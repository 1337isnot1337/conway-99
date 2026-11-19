# Fifteen grids through a point

Let (p) belong to fifteen grids. On the seven triangles through (p), join two axes in (F) when their cell fails to form a grid. Then the six edges of (F) must form a complete bipartite graph (K_{2,3}), with the other two axes isolated.

Use the cell vectors (z_e) and four-point sets (B_e) of the [root bound](grid_intersections.md). Their sum at each axis is zero. For (w) in (B_f), the number of its neighbors in (B_e) is (2-z_e(w)) if (e=f), (-z_e(w)) for distinct intersecting pairs, and (1-z_e(w)) for disjoint pairs. Each nongrid cell contains at most two internal edges, and some vertex there has (z_e(w)>0).

## Six possible missing edges

No nonisolated vertex of (F) has degree one. On four nonisolated vertices the only possibility is (K_4). On six vertices the components must be cycles, and an isolated odd cycle forces all its edge vectors to vanish. The six-cycle was excluded in the root bound. On five vertices the degree sequence is (4,2,2,2,2) or (3,3,2,2,2). In the first case two triangles meet at the vertex of degree four. In each triangle the two edges at that vertex have equal vectors, by cancellation at the other two vertices. Two distinct edges meeting at an axis cannot have equal vectors: at a vertex of positive defect in one cell the other cell has nonpositive defect. This excludes the first case.

In the second case suppress the degree-two vertices. A pair of disjoint end cycles joined by a path would need at least six vertices. Hence the graph consists of three paths joining the degree-three vertices. Their lengths are (1,2,3) or (2,2,2). The axis equations at the ends, after alternating along the paths, force the vector on the unique even path of the first case to vanish. The second case is (K_{2,3}).

## Excluding the tetrahedron

Suppose (F=K_4). Its three opposite-edge pairs carry vectors (x,y,z), respectively, with (x+y+z=0). Indeed, adding the equations at two axes and subtracting the other two shows equality of opposite edges.

In a missing cell of type (x), the value of (x) is at most one by comparison with its disjoint opposite edge. Thus all four internal degrees are at least one. The two-edge bound makes the cell a perfect matching, (x=1) throughout, and the other two coordinates are 0 and (-1) in some order. The corresponding statements hold in each missing cell. In a present cell touching the tetrahedron, its vertices have no neighbors in any distinct cell sharing an axis with it: the grid already uses both far-neighbor slots on that axis. Thus at least one edge from each opposite-edge pair has value zero there. The three remaining present cells, on pairs of the three isolated axes, will be called the exterior cells. They contain twelve vertices.

Fix a missing cell (B) of type (x). Each of its four points has precisely one neighbor in each exterior cell, by perfect domination of the corresponding grid and disjointness of the axes. This gives three maps from (B) to four-point sets. Any two points of (B) have at most one shared far neighbor in any one missing cell counted as a potential *vertex* only when some vertex there has at least two neighbors in (B). In fact no such vertex occurs: in the opposite cell the count is zero, in a touching missing cell it is at most one, and within (B) it is also one. All present cells disjoint from (B) that touch the tetrahedron have defect zero, so every vertex there also sees at most one point of (B). Present cells meeting (B)'s axes see none. Consequently every common neighbor of two points of (B) outside the near shell is an agreement of their three maps.

No fiber of a map can contain three points. If the internal matching uses sides of the signed square, any triple contains a matched pair whose unique common neighbor is its near anchor. If it uses diagonals, then *each* pair needs exactly one far common neighbor: a diagonal pair is adjacent and has no near common neighbor, and a side pair is nonadjacent and has one near common neighbor. Four points in one fiber would use every agreement at that coordinate (this case is already impossible since (x+y+z=0) and each exterior coordinate is at most one, giving (x\ge-2)). If exactly three agree at a coordinate, they must be pairwise distinct at both other coordinates. The fourth point can then agree with at most two of the three, a contradiction.

At an exterior vertex the three coordinates are thus at least (-1), since a fiber has size (1-x), and are at most one. Their squared sum is at most two. On the 24 missing-cell vertices the squared sum is two as well. All other coordinates vanish. This gives
[
  \|x\|^2+\|y\|^2+\|z\|^2\le 2(24+12)=72 .
]
But every missing cell has internal degree one at all four vertices. The identity (W^2=7W) gives (\|x\|^2=7\langle h_e,z_e\rangle=28), and likewise for the other two vectors. Their squared norms sum to 84. This rules out the tetrahedron.
