# A common prism pair at the three vertices of a full triangle

Let $T$ be a triangle on six grids in a hypothetical Conway graph. Each grid on $T$ consists of $T$ and a triangular prism, with two sites in each of the three fibers indexed by the vertices of $T$. Different prisms are anticomplete. At a vertex $x$ of $T$, the axes from prisms $i,j$ may span a further grid $G_x(ij)$. **No pair $ij$ spans such a grid at all three vertices of $T$.**

## The 27-point core

Assume a common pair exists. The [cross-grid disjointness lemma](full-triangle-cross-grids.md) gives three disjoint grids, one layer at each vertex of $T$. Label a layer in row-major order $0,\ldots,8$, with its root at $0$, its two $i$ sites at $1,2$ and its two $j$ sites at $3,6$. The four other points are its corners. Between any two layers there is a perfect matching because every grid perfectly dominates its exterior. The edges of $T$ and the two transversal triangles in each prism fix the matching on the five labeled axis sites after choosing their orders. The corner bijections have $24^3$ choices.

For core adjacency $H$, write $R=12I+2J-H-H^2$. The strongly regular graph equation identifies $R$ with the Gram matrix of the core-to-exterior incidence. Keep only entrywise nonnegative $R$ and identify isomorphic cores preserving $T$. The marking recovers the prisms as the two components among the neighbors of $T$. Each corner has two neighbors in these prisms, both in the same root fiber, which recovers its layer. This leaves 93 marked cores.

Every exterior point selects one neighbor in each layer. Its triple also meets each of the two grids on $T$ in one point. A candidate row $v$ must satisfy $Hv+v\le2\mathbf1$ and cannot contain a pair with zero residual quota. A triple can occur at most once since distinct vertices share at most two neighbors. Select distinct rows whose outer products sum to $R$, checking diagonal and pair quotas. A search that forces all remaining choices in a tight quota, rules out all choices in a filled quota and otherwise branches on inclusion of one row gives seven possible cores.

## The forced 24 neighbors of the triangle

An exterior triple selecting a point of $T$ has two corners in the other layers. An exterior triple avoiding $T$ has one $i$ site, one $j$ site and one corner, because it meets both grids on $T$. Consequently the exterior common neighbors of corners $u,v$ in different layers are precisely the points whose triple consists of $u,v$ and the root in the third layer. Their multiplicity is $R_{uv}$. Make a multigraph on the twelve corners with these multiplicities. Its 24 edge copies index all the remaining neighbors of $T$.

Fullness splits these 24 points into four further prisms. Each corner sees one site of each prism, by perfect domination of the corresponding grid on $T$. Hence each prism is a perfect matching of the corner multigraph. Enumerate partitions of its edge copies into four perfect matchings, identifying orders of components and exchanges of copies of the same edge. Each matching contains two edges between each pair of layers since it covers the four sites in each of three layers. Thus its six new points have two in each root fiber. Join the two in each fiber. To form the two transversal triangles there are four orientations, fixing their names at the first fiber. Across the seven cores there are 468 partitions and $468\cdot4^4=119808$ oriented layouts. This specifies every edge on 51 points. Distinct prisms are anticomplete, and the triple specifies all contacts of each new point with the original 27.

## The final 48 exterior rows

Every remaining point has a triple avoiding $T$ on the first core, and one neighbor in each of the four new prisms. Of its six neighbors in the six prisms, exactly two lie in each root fiber, by the common-neighbor count with each vertex of $T$. Enumerate the four remaining fiber labels with exactly these multiplicities and both signs in every prism. This lists every possible seven-point row. Again the rows must be distinct.

Of the 119,808 layouts, 3,000 have nonnegative residual matrices and 753 also have positive semidefinite residual matrices. The latter test uses the integer coefficients of $\det(xI+R)$. A symmetric $R$ is positive semidefinite exactly when these coefficients are all nonnegative. For each of the 753 cases, filter rows using the zero quotas and $Hv+v\le2\mathbf1$, then solve the same binary diagonal and pair quota equations. None admits an exterior incidence. This excludes the common pair.

Run `make verify-full-triangle-common-pair` for the [integer enumeration](../../experiments/workspace/full_triangle_common_pair.py).
