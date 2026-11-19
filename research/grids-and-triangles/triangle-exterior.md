# No triangle has a vertex-transitive exterior

Fix any triangle $T$ of a hypothetical Conway 99-graph. The graph on the 60 points with no neighbor in $T$ cannot be vertex-transitive. Its automorphisms need only preserve this induced graph. The argument determines the exterior spectrum from the 36 neighbors of $T$ and uses a finite group enumeration in the last step.

## Spectrum of the exterior

Write $U$ for the 36 neighbors of $T$ outside $T$ and $W$ for the remaining 60 vertices. Each of the three points of $T$ sees one fiber of twelve points in $U$. The graph $D$ on $U$ is cubic: every vertex sees one point in each fiber, including its own. The graph $E$ on $W$ is 8-regular. Each vertex of $W$ sees two points of each fiber, while each vertex of $U$ sees ten in $W$. Below we use $D,E$ also for their adjacency matrices, $B$ for the $W$-by-$U$ incidence matrix and $P$ for the three fiber indicators as rows. The corresponding blocks of $A^2+A=12I+2J$ give
$$
 B^tB=12I+2J-D-D^2-P^tP,\qquad EB=2J-B-BD,\qquad E^2+E=12I+2J-BB^t .
$$
The constant column on $U$ maps to a constant. The two independent contrasts between the fiber indicators lie in $\ker D\cap\ker B$. On the orthogonal complement of all three fiber indicators, $B^t B=(3I-D)(4I+D)$. Since $D$ is cubic, the only remaining null vectors have eigenvalue 3. If $D$ has $h$ components, there are $h-1$ of these: one linear combination of the component constants is the global constant, and each component has equal numbers of points in the three fibers. This last fact follows from the perfect matchings between fibers.

The other $34-h$ eigenvalues $\theta$ of $D$ transfer to $-1-\theta$ in $E$. The constant contributes eigenvalue 8, and the orthogonal complement of the image of $B$ has eigenvalues 3 and $-4$. Its dimension is $25+h$. Using $\operatorname{tr}E=\operatorname{tr}D=0$ gives multiplicities 18 and $7+h$ respectively. The transferred values lie in $(-4,2]$. In particular $E$ is connected and its second eigenvalue is 3. In polynomial form, with $\chi_M(x)=\det(xI-M)$,
$$
 (x+1)^2\chi_E(x)=(x-8)(x-3)^{18}(x+4)^7\chi_D(-1-x).
$$

## Triangles and squares

Let $c$ be the number of disjoint triangles joined to $T$ by three edges, and set $s=12-c$. These are exactly the triangles of $D$: the matchings within fibers already complete their edges through $T$, and a triangle of $D$ uses all three fibers. A vertex $w\in W$ has six neighbors in $U$. Let $e_w$ count edges among those six. The 14 neighbors of $w$ form a matching. Of the eight neighbors in $W$, precisely $6-2e_w$ are paired to a neighbor in $U$. Thus $w$ lies in $1+e_w$ triangles of $E$. The $36-3c$ cross-fiber edges outside the triangles of $D$ must each complete a triangle in $W$ with their two endpoints in $U$. Hence $\sum e_w=3s$ and $E$ has $20+s$ triangles.

If $E$ is vertex-transitive, all $e_w$ are equal, so $s$ is a multiple of 20. Since $0\le s\le12$, we have $s=0$. In particular the triangles of $E$ partition $W$ into twenty triples.

Writing $q_D,q_E$ for the respective numbers of unoriented 4-cycles, the spectral identity gives
$$
 \operatorname{tr}E^4=8568+24c+8q_D,\qquad q_E=171+3c+q_D .
$$
Indeed $\operatorname{tr}D^2=108$, $\operatorname{tr}D^3=6c$ and $\operatorname{tr}D^4=540+8q_D$. Subtract $60\cdot8\cdot15$ from $\operatorname{tr}E^4$ to count the eight walks per exterior 4-cycle.

When $s=0$, $D$ consists of twelve triangles and a matching of their vertices within fibers. Any square alternates two matching edges with two triangle edges. Two matching edges between a pair of triangles force the third. Otherwise these two triangles and $T$ would induce the [rook grid minus one edge](../../STATE.md), which is impossible. Three matching edges give one grid on $T$, contributing three squares. If $d$ denotes the number of grids on $T$, then $q_E=207+3d$. Under transitivity the number of squares through each exterior vertex is $(69+d)/5$. Since $0\le d\le6$, this requires $d=1$ or $6$, giving 14 or 15 rooted squares.

## Faithful action on twenty blocks

Let $G=\operatorname{Aut}(E)$ and assume it acts transitively on the 60 vertices. The twenty exterior triangles are its canonical blocks. The edges between any two form a matching. If two triangles have one or two cross-edges, this distinguishes a vertex of the first triangle by its matching status. The kernel of the action on the blocks fixes this vertex. Its fixed points form a $G$-invariant set by normality, so transitivity forces the kernel to fix all 60 vertices.

It remains to rule out the case in which every two blocks are anticomplete or joined by a full matching. Each block then has six neighboring blocks, giving a simple 6-regular graph $H$ on twenty points. The block partition is equitable with quotient $2I+H$. The connectedness of $E$ gives connectedness of $H$; interlacing gives $\lambda_2(H)\le1$. Take $f(z)=(z-1)(z+3)^2$. Its sum over the eigenvalues of $H$ is at most $f(6)=405$, since all others are at most 1. Yet it is $\operatorname{tr}H^3+5\cdot120-9\cdot20\ge420$. This proves faithfulness.

## Exhausting the faithful actions

A faithful transitive action on twenty blocks is conjugate to one of the 1,117 groups in the [GAP TransGrp catalog](https://gap-packages.github.io/transgrp/). Let $K$ be such a group and $H$ a block stabilizer. Its possible transitive actions on sixty vertices with these blocks are the coset actions $K/J$ where $J$ has index three in $H$. To find them, enumerate epimorphisms from $H$ onto $C_3$ and $S_3$ and take the inverse image of a point stabilizer in their natural three-point actions. Every transitive degree-three group appears. [GQuotients](https://docs.gap-system.org/doc/ref/chap40_mj.html) returns epimorphisms up to target automorphisms, which preserve the conjugacy class of this point stabilizer for both targets.

For each action, a simple invariant graph is a union of orbits on unordered pairs of points. The orbit of an in-block pair gives the twenty triangles and has valency two. Enumerate all subsets of the remaining orbits with total valency six. At a root, apply the common-neighbor bounds for both edges and nonedges and demand exactly one triangle. Count one rooted square for each other vertex with two common neighbors. Transitivity makes these tests independent of the root. Finally $E-3I$ must have rank 42 over the rationals and rank at most 42 over every prime field.

| Stage | Count |
| --- | ---: |
| Marked transitive actions | 912 |
| Degree-eight orbital unions containing the block triangles | 66,327 |
| Common-neighbor and triangle tests pass | 2,302 |
| Rooted square count is 14 or 15 | 362 |
| Rank at most 42 modulo 101 | 0 |
| Rank at most 42 modulo 1009 | 0 |

Run `make verify-triangle-exterior` with GAP, its TransGrp library, Python and NumPy. The [GAP action enumerator](../../experiments/workspace/triangle_exterior_actions.g) and [orbital and modular rank checker](../../experiments/workspace/triangle_exterior_transitive.py) recreate the table from the catalog. Counts refer to marked actions and orbital unions, so a graph can appear more than once. The [ProofAtlas research record](https://www.proofatlas.ai/collaboration/conways-99-graph-conjecture/) already discusses the triangle spread and the six-prism construction. The present exclusion leaves exterior graphs with more than one vertex orbit open.
