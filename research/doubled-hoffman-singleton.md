# A 14-regular graph scoring 4,313 out of 4,950

Replacing the vertices of the Hoffman–Singleton graph by pairs gives an explicit 99-vertex, 14-regular graph with CAISc score **4,313/4,950 (87.13%)**. Thakkar and Severini report a 14-regular construction scoring 3,795 in version 3. The new example has 637 failing pairs and large errors concentrated on 49 pairs of vertices. [Published benchmark and scoring convention, §§2.1 and 3.3](https://arxiv.org/html/2608.11211v3)

| Constraint | Satisfied | Total |
| --- | ---: | ---: |
| Degree 14 | 99 | 99 |
| One common neighbor for an adjacent pair | 182 | 693 |
| Two common neighbors for a nonadjacent pair | 4,032 | 4,158 |

## Construction and count

Start with the Hoffman–Singleton graph, which has parameters $(50,7,0,1)$. Fix a vertex $o$. Replace every vertex other than $o$ by two vertices with the same external neighbors. Retain $o$ as a singleton. Over each base edge join every vertex at one end to every vertex at the other. Add the edge within each of the seven pairs over a neighbor of $o$. The 14 vertices in these pairs originally had degree 13 and now have degree 14. Every other degree was already 14. The generator uses the five-pentagon, five-pentagram coordinatization. [Hoffman–Singleton graph](https://aeb.win.tue.nl/drg/graphs/Hoffman-Singleton.html)

The neighbors of $o$ are independent in the base. Every lifted edge between different base vertices has one common neighbor precisely when an endpoint belongs to one of the seven internally joined pairs. There are $7\cdot2\cdot13=182$ such edges. The seven internal edges have thirteen common neighbors each. The remaining 504 edges have zero.

For two vertices over different nonadjacent base points, their common neighbors are exactly the fiber over the unique common base neighbor. Only a singleton at $o$ gives the wrong count. There are $4\binom{7}{2}=84$ such pairs. The 42 nonadjacent pairs within fibers have fourteen common neighbors each. This leaves $4158-84-42=4032$ correct nonedges.

For $R=A^2+A-12I-2J$, the off-diagonal upper triangle has 49 entries equal to $12$, 588 equal to $-1$ and 4,214 equal to zero. The sum of squared errors over unordered pairs is $7,644$. The row at $o$ satisfies the required graph equation, while each other vertex has a partner accounting for its large positive residual.

## Sharpness among graphs with 49 disjoint twin pairs

Here a pair is called twins if each vertex has the same neighbors outside the pair. Among **all** 14-regular 99-point graphs with 49 disjoint pairs of twins, the largest possible score is 4,313. The doubled Hoffman–Singleton example is the unique maximizer up to isomorphism.

For any such graph let $o$ be the remaining singleton. Between two twin pairs the interface is complete or empty. For a pair let $b$ indicate adjacency to $o$, let $c$ indicate its internal edge, and let $d$ count the other pairs it sees. The degree equation $14=2d+b+c$ gives $b=c$. Exactly seven pairs see $o$, and these are exactly the internally joined pairs. Call them special. Contract every pair, retaining $o$. The resulting 50-point graph is 7-regular.

Let $t$ count the edges between special vertices in this quotient. An edge with both ends in ordinary fibers has an even number of common neighbors. Each special internal edge has thirteen. Thus every successful adjacent pair must use one of the $7\cdot 2\cdot 13=182$ incidences from a special point to another fiber. Every edge between two special fibers fails, since it has $o$ and the two partners as common neighbors. Each of the $t$ quotient edges of that kind uses eight of the counted incidences. There are at most $182-8t$ successful edges.

The 42 ordinary twin pairs fail the nonedge test. Between two distinct nonadjacent special fibers, the common-neighbor count is odd: the singleton contributes one and every other contribution comes in pairs. This forces another $4(21-t)$ failing nonedges. The total score is at most
\[
99+(182-8t)+4158-42-4(21-t)=4313-4t.
\]

Equality requires $t=0$ and success on every nonedge outside the forced failures. In the quotient every nonadjacent pair of special vertices has the common neighbor $o$. Every other quotient nonedge has a common neighbor because its lifted points satisfy the nonedge test. Thus the 7-regular quotient of order 50 has diameter two. From each vertex the seven neighbors have only 42 remaining slots for walks of length two, and all 42 nonneighbors must be reached. This forces parameters $(50,7,0,1)$. Uniqueness of the Hoffman–Singleton graph and its vertex-transitivity give the stated equality case. [Hoffman–Singleton uniqueness](https://people.math.harvard.edu/~elkies/Misc/hsgraph.pdf) · [Vertex-transitivity](https://aeb.win.tue.nl/drg/graphs/Hoffman-Singleton.html)

The [graph6 file](../experiments/workspace/hoffman-singleton-double.g6) contains the full labeled graph. The [verifier](../experiments/workspace/hoffman_singleton_double.py) checks the base graph identity, reconstructs the graph, decodes the file and counts every pair by intersections of neighbor sets. A separate integer matrix calculation verifies the complete residual distribution. Run `python experiments/workspace/hoffman_singleton_double.py` with NumPy, or `make verify`.

## Rewiring the graph

Allowing the two copies of the base graph to have different labelings, then switching edges and whole symmetry orbits, produced a [twin-free 14-regular graph](../experiments/workspace/hoffman-rewired-4272.g6) scoring **4,272/4,950 (86.30%)**. It satisfies 554 edge and 3,619 nonedge constraints. Its largest positive residual is five and its sum of squared errors is 2,442. Both quantities are smaller than in the 4,313-point example.

A single degree-preserving switch gives a graph with **trivial automorphism group** scoring **4,238/4,950 (85.62%)**. In the zero-based graph6 labeling, delete edges $48$–$49$ and $97$–$98$, and add $48$–$98$ and $49$–$97$. It satisfies 556 edge and 3,583 nonedge constraints, with maximum positive residual five and sum of squared errors 2,494.

For a direct asymmetry certificate, color each vertex by the sorted entries in its row of $R$. This gives 20 colors invariant under every automorphism. Refine each color by the multiset of colors of its neighbors. The next two rounds give 81 and 99 colors, forcing every vertex to be fixed. The verifier replays the switch, the color counts and the residual histograms for both graphs.
