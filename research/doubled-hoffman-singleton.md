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

The [graph6 file](../experiments/workspace/hoffman-singleton-double.g6) contains the full labeled graph. The [verifier](../experiments/workspace/hoffman_singleton_double.py) checks the base graph identity, reconstructs the graph, decodes the file and counts every pair by intersections of neighbor sets. A separate integer matrix calculation verifies the complete residual distribution. Run `python experiments/workspace/hoffman_singleton_double.py` with NumPy, or `make verify`.
