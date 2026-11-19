# Fifteen grids through a point

Let $p$ belong to fifteen grids. On the seven triangles through $p$, join two axes in $F$ when their cell fails to form a grid. Then the six edges of $F$ must form a complete bipartite graph $K_{2,3}$, with the other two axes isolated.

Use the cell vectors $z_e$ and four-point sets $B_e$ of the [root bound](grid_intersections.md). The vectors on the edges incident to each axis sum to zero. For $w$ in $B_f$, the number of its neighbors in $B_e$ is $2-z_e(w)$ if $e=f$, $-z_e(w)$ for distinct intersecting pairs, and $1-z_e(w)$ for disjoint pairs. Each nongrid cell contains at most two internal edges, and some vertex there has $z_e(w)>0$.

## Six possible missing edges

No nonisolated vertex of $F$ has degree one. On four nonisolated vertices the only possibility is $K_4$. On six vertices the components must be cycles, and an isolated odd cycle forces all its edge vectors to vanish. The six-cycle was excluded in the root bound. On five vertices the degree sequence is $4,2,2,2,2$ or $3,3,2,2,2$. In the first case two triangles meet at the vertex of degree four. In each triangle the two edges at that vertex have equal vectors, by cancellation at the other two vertices. Two distinct edges meeting at an axis cannot have equal vectors: at a vertex of positive defect in one cell the other cell has nonpositive defect. This excludes the first case.

In the second case suppress the degree-two vertices. A pair of disjoint end cycles joined by a path would need at least six vertices. Hence the graph consists of three paths joining the degree-three vertices. Their lengths are $1,2,3$ or $2,2,2$. The axis equations at the ends, after alternating along the paths, force the vector on the unique even path of the first case to vanish. The second case is $K_{2,3}$.

## Excluding the tetrahedron

Suppose $F=K_4$. Its three opposite-edge pairs carry vectors $x,y,z$, respectively, with $x+y+z=0$. Indeed, adding the equations at two axes and subtracting the other two shows equality of opposite edges.

In a missing cell of type $x$, the value of $x$ is at most one by comparison with its disjoint opposite edge. Thus all four internal degrees are at least one. The two-edge bound makes the cell a perfect matching, $x=1$ throughout, and the other two coordinates are 0 and $-1$ in some order. The corresponding statements hold in each missing cell. In a present cell touching the tetrahedron, its vertices have no neighbors in any distinct cell sharing an axis with it: the grid already uses both far-neighbor slots on that axis. Thus at least one edge from each opposite-edge pair has value zero there. The three remaining present cells, on pairs of the three isolated axes, will be called the exterior cells. They contain twelve vertices.

Fix a missing cell $B$ of type $x$. Each of its four points has precisely one neighbor in each exterior cell, by perfect domination of the corresponding grid and disjointness of the axes. This gives three maps from $B$ to four-point sets. No vertex of a missing cell sees two points of $B$: in the opposite cell the count is zero, in a touching missing cell it is at most one, and within $B$ it is also one. All present cells disjoint from $B$ that touch the tetrahedron have defect zero, so every vertex there also sees at most one point of $B$. Present cells meeting $B$'s axes see none. Consequently every common neighbor of two points of $B$ outside the near shell is an agreement of their three maps.

Every fiber of each map has size at most two. If the internal matching uses sides of the signed square, any triple contains a matched pair whose unique common neighbor is its near anchor. If it uses diagonals, then *each* pair needs exactly one far common neighbor: a diagonal pair is adjacent and has no near common neighbor, and a side pair is nonadjacent and has one near common neighbor. A four-point fiber is impossible since $x+y+z=0$ and each exterior coordinate is at most one, giving $x\ge-2$. If exactly three agree at a coordinate, they must be pairwise distinct at both other coordinates. The fourth point can then agree with at most two of the three, a contradiction.

At an exterior vertex the three coordinates are thus at least $-1$, since a fiber has size $1-x$, and are at most one. Their squared sum is at most two. On the 24 missing-cell vertices the squared sum is two as well. All other coordinates vanish. This gives
$$
  \|x\|^2+\|y\|^2+\|z\|^2\le 2$24+12$=72 .
$$
But every missing cell has internal degree one at all four vertices. The identity $W^2=7W$ gives $\|x\|^2=7\langle h_e,z_e\rangle=28$, and likewise for the other two vectors. Their squared norms sum to 84. This rules out the tetrahedron.

## The surviving 24 vertices

Write the two hubs as $u,v$, the three vertices of degree two as $i,j,k$, and the two isolated axes as $c,d$. On the two edges at $i$ the vectors have opposite signs. Write $x_i=z_{ui}=-z_{vi}$, so $x_i+x_j+x_k=0$. Combine the missing cells at $i$ into the eight-point set $U_i=B_{ui}\cup B_{vi}$.

Every point of $U_i$ has two neighbors within $U_i$. For instance, in $B_{ui}$ its internal degree is $2-x_i$ and its degree into $B_{vi}$ is $x_i$. For any other leaf $j$, its degrees into $B_{uj}$ and $B_{vj}$ sum to one, by the same coordinate formulas. Thus the three eight-point sets carry a 4-regular graph with perfect matchings between sets. Inside each set the edges alternate between a perfect matching within the two leaf-sign classes and a perfect matching between them. Indeed a far point bearing one signed leaf anchor has one far neighbor bearing that sign and one bearing its mate. No present cell sharing the leaf axis can supply either neighbor. In particular the internal graph is an eight-cycle or two four-cycles.

Fix $U_i$. A point in a present cell on two of the four axes $j,k,c,d$ sees precisely two vertices in $U_i$, since its counts into the two missing cells sum to $(1-x_i)+(1+x_i)$. Every point of $U_i$ has one neighbor in that present cell. Its four points therefore define a perfect matching on $U_i$ by pairing the two points with the same image. The other present cells see at most one point of $U_i$ each. Neither of the other missing eight-point sets can supply a shared neighbor, by the inter-set matchings. For each pair in $U_i$, subtract its near common neighbors and its common neighbors within $U_i$ from the required common-neighbor number. The residual pair multiplicities must decompose into **six perfect matchings**, one for each pair of axes in $\{j,k,c,d\}$. The matching for the pair $jk$ must join opposite hubs throughout. Indeed its points have $x_j=x_k=0$ because the cell is present and touches both leaves, so $x_i=0$ there as well.

The [eight-point enumeration](../../experiments/workspace/grid_leaf.py) generates the two four-point matchings within sign classes and the bijection between classes. The pair quotas, the two-edge bound in each missing cell, and the signed-hub bounds leave 114 of 216 labeled choices and 23 orbits under swapping hubs and flipping signs. All 23 orbits admit the six-matchings decomposition above. Compatibility of the three eight-point sets is still required.
