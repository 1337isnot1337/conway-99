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

## Walk-regularity characterizes the full triangles

A graph is walk-regular if for each length all vertices start the same number of closed walks. **The exterior $E$ is walk-regular if and only if $T$ lies on six grids.** In fact equality of the rooted counts through length eight suffices.

The necessity argument for $s=0$ and $d\in\{1,6\}$ above uses only closed walks of lengths three and four: in a regular graph their counts at a root determine its numbers of triangles and squares. When $s=0$, contract each triangle of $D$ to a vertex and keep its three matching half-edges. The resulting cubic multigraph $H$ on twelve vertices is properly three-edge-colored by the fibers. Parallel edges occur in bundles of three, one bundle per grid on $T$. The graph $D$ is the line graph of the subdivision of $H$. Its characteristic polynomial is
$$
 \chi_D(z)=z^6(z+2)^6\chi_H(z^2-z-3).
$$
Indeed the subdivision has 30 vertices and 36 edges. If $N$ is its unsigned vertex-edge incidence matrix, $D=N^tN-2I$. In $NN^t$ the diagonal blocks are $3I,2I$ and the off-diagonal block is the incidence matrix $C$ of $H$, with $CC^t=3I+H$. Taking a Schur complement gives the displayed formula. In particular
$$
 \chi_E(x)=(x-8)(x-3)^{18}(x+4)^7(x+1)^4(x-1)^6\chi_H(x^2+3x-1).
$$

Suppose $d=1$. Then $H$ consists of one triple edge and a simple cubic graph $L$ on ten vertices. Compare this with the six-grid polynomial, where the ten vertices instead form five triple edges, denoted $L_0$. Each eigenvalue $h$ of $L$ contributes two eigenvalues of $E$ whose power sum $p_j(h)$ satisfies $p_0=2$, $p_1=-3$, $p_j=-3p_{j-1}+(1+h)p_{j-2}$. In particular $p_6,p_8$ are integral polynomials with leading terms $2h^3,2h^4$. The six-grid spectrum is $8^1,3^{18},1^{12},(-1)^{10},(-2)^6,(-4)^{13}$; its sixth and eighth power sums are both divisible by 60.

Write $a,b$ for the counts of triangles and squares in $L$. The traces of $L^2,L^3,L^4$ are $30,6a,150+8b$, while the traces for $L_0$ are $90,0,810$. Walk-regularity requires both $\operatorname{tr}E^6$ and $\operatorname{tr}E^8$ to be divisible by 60. Subtracting the six-grid trace at length six gives $12a\equiv0\pmod{60}$. The only possible multiple of five is zero. In a cubic graph triangles outside $K_4$ components are isolated triangles or pairs sharing an edge, using respectively three points per triangle or four points per two. Ten points without a $K_4$ support at most four triangles. With a $K_4$ the other six vertices form a cubic graph; its complement is a six-cycle or two triangles, yielding respectively two or zero more triangles. Now $a=0$, and subtraction at length eight gives $16b\equiv0\pmod{60}$. Thus $15\mid b$. Each vertex lies on at most six squares, so $b\le15$. Equality would require every two neighbors of every point to have identical three-point neighborhoods. The components would all be $K_{3,3}$, impossible on ten vertices. Hence $b=0$.

A simple cubic graph of girth at least five on ten vertices cannot have a proper three-edge-coloring. Two colors would form an even cycle cover, necessarily a single ten-cycle. Label it cyclically from 0 to 9. The five remaining matching edges are chords of cyclic distance four or five. Distance four preserves parity, so an odd number of chords have distance five. Two such diameters whose indices are consecutive modulo five make a square, so at most two diameters are possible. The only diameter must then be $0$ to $5$ up to rotation. On the remaining points the distance-four matching is forced: its edges are $2$ to $6$, $4$ to $8$, $1$ to $7$ and $3$ to $9$. But $1,2,6,7$ form a square. This excludes $d=1$.

Conversely if $d=6$, $D$ consists of six triangular prisms. Every exterior point marks exactly one point of each prism, since the associated nine-point grid is a perfect dominating set. For every polynomial $f$, the diagonal of $Bf(D)B^t$ is constant: there is one contributing diagonal entry per prism, and the prism is vertex-transitive. The relation $EB=2J-B-BD$ implies that $E^jB$ is a linear combination of $J$ and $Bf_j(D)$ for every $j$. Thus $E^jBB^t$ has constant diagonal, using the constant row sum of $B$. Multiplying $E^2+E=12I+2J-BB^t$ by successive powers of $E$ proves inductively that all powers of $E$ have constant diagonal.

Consequently at most twenty of the 231 triangles have walk-regular exteriors, by the [bound on full triangles](double-partner-witness.md). All other triangles have two exterior points with different numbers of closed walks of length at most eight.

## Fixed points of exterior automorphisms

For every triangle, each nonidentity automorphism of $E$ moves at least 36 points. Its prime divisors belong to $\{2,3,5\}$, and every element of order five acts freely. These conclusions do not require saturation.

For a moved set of size $m$, its mean internal degree is at most $3+5m/60$. This follows by applying the upper bound 3 on the nonconstant spectrum to its centered indicator. Every moved point has at most two fixed neighbors: each is also a neighbor of its image. The mean internal degree is therefore at least six, giving $m\ge36$. For an automorphism of odd prime order, two fixed neighbors of a moved orbit would have at least three common neighbors. Thus every moved point has at most one fixed neighbor, giving $m\ge48$.

Primes larger than eight cannot join a fixed point to a moving orbit. Connectedness would force a free action, and no such prime divides 60. At a fixed point there are between one and four exterior triangles, by the six-mark count above. An element of order five or seven must fix all those triangles pointwise. At order seven, a fixed point touching a moving orbit has just one neighbor left in the fixed set, which cannot contain its triangle. So an order-seven action would have to be free, again impossible.

At order five the fixed set has size $0,5$ or $10$. Its internal vertex degrees are three and eight. Size five would require a cubic graph of odd order. At size ten at most one vertex has degree eight, since two would have at least six common neighbors. Parity of the degree sum then implies that every degree is three. Each fixed point belongs to a triangle inside this cubic graph. In a cubic graph with at most one common neighbor per edge, these triangles are disjoint, and three does not divide ten. This proves freeness. In particular the order of a Sylow five-subgroup is at most five, since it acts freely on sixty points.

An order-five exterior symmetry also requires $s\in\{0,5,10\}$ by the triangle count. Its free orbits give the polynomial constraint
$$
 \chi_D(z)\equiv z^2(z-1)(z-3)^3 F(z)^5\pmod 5
$$
for a monic polynomial $F$ of degree six. Indeed, over characteristic five, a five-cycle acts as a single unipotent Jordan block. Order the vertices in twelve orbits; $E$ is a matrix of circulant five-by-five blocks. The filtration by the powers of the cyclic shift minus the identity has five layers, all acted on by the same twelve-by-twelve quotient. Hence $\chi_E$ is a fifth power modulo five. Substitute the exterior characteristic identity and compare the multiplicities of the roots $0,1,3$ of the indicated factors.

## Faithful action on twenty blocks

Let $G=\operatorname{Aut}(E)$ and assume it acts transitively on the 60 vertices. The twenty exterior triangles are its canonical blocks. The edges between any two form a matching. If two triangles have one or two cross-edges, this distinguishes a vertex of the first triangle by its matching status. The kernel of the action on the blocks fixes this vertex. Its fixed points form a $G$-invariant set by normality, so transitivity forces the kernel to fix all 60 vertices.

It remains to rule out the case in which every two blocks are anticomplete or joined by a full matching. Each block then has six neighboring blocks, giving a simple 6-regular graph $H$ on twenty points. The block partition is equitable with quotient $2I+H$. The connectedness of $E$ gives connectedness of $H$; interlacing gives $\lambda_2(H)\le1$. Take $f(z)=(z-1)(z+3)^2$. Its sum over the eigenvalues of $H$ is at most $f(6)=405$, since all others are at most 1. Yet it is $\operatorname{tr}H^3+5\cdot120-9\cdot20\ge420$. This proves faithfulness.

In fact the action on the twenty blocks is faithful whenever $s=0$, even if $G$ is intransitive. A block-fixing permutation cycling any one block can meet another block by a nonempty matching only if it is a full matching and the other block also cycles. Connectedness and the quotient contradiction above exclude this possibility. Any remaining nonidentity element of the kernel swaps pairs inside triangle blocks. Each moved vertex has just one fixed neighbor: its triangle's third point. An additional fixed neighbor would be a second common neighbor of the adjacent swapped pair. The moved set then has mean internal degree seven, requiring at least 48 vertices. Swapping at most two vertices in each of twenty triangles moves at most 40.

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
