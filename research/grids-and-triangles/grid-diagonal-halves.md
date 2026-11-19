# The twenty points at two diagonally opposite grid corners

Suppose the tips of both pairs of opposite sides of a square are adjacent. Choose a pair of opposite corners. Their two ten-point fibers induce a connected cubic graph $H$, the union of a matching in each fiber and a bipartite 2-factor between them. The [connectedness argument](incomplete-corner-fibers.md) applies with or without the ninth grid point. Up to isomorphism preserving the unordered pair of fibers, there are at most **3,978** possible marked graphs $H$. In a complete nine-point rook grid, a constraint from its seven other fibers cuts this to **3,937**. Of these, only **three** have an edge cut of size at most two.

## Enumerating the diagonal

The bipartite cycles have lengths at least six. Their half-lengths form one of $(10),(3,7),(4,6),(5,5),(3,3,4)$. Fix a labeled copy of each 2-factor and enumerate its two internal matchings. Two endpoints of a matching edge already share their grid corner, so they cannot have a common neighbor on the other side. Discard such matching edges. The orbits of the remaining matching pairs under the color-preserving automorphism group of the 2-factor give 7,511 types with ordered fibers. Allowing a global exchange of the fibers gives 3,985 types. Seven are disconnected.

## Counting squared intersections

Now assume the grid is complete. Every exterior point has exactly one neighbor among the nine grid points. Partition the 90 exterior points into fibers of ten by that neighbor. A point in one fiber has one neighbor in the fiber of an adjacent grid point and two in the fiber of a nonadjacent grid point. This follows by counting its two common neighbors with the second grid point.

Take any subset $S$ of $H$ with indicator $z$, containing $a,b$ points in the two respective fibers. For each exterior point $y$ outside $H$, write $q_y=|N(y)\cap S|$. The identity $A^2+A=12I+2J$ of the full graph gives the sum of $q_y^2$ on the seven remaining fibers:
\[
L=z^\top(12I+2J-H-H^2)z-a^2-b^2.
\]
The final two terms remove the two grid corners seeing $S$. The sums of $q_y$ within the seven fibers are $a+b$ twice, $a+2b$ twice, $2a+b$ twice, and $2a+2b$ once. For ten integer values with total $t=10u+r$, $0\le r<10$, the minimum sum of squares is $f(t)=10u^2+(2u+1)r$. Hence
\[
L\ \ge\ 2f(a+b)+2f(a+2b)+2f(2a+b)+f(2a+2b).
\]
Complementing $S$ replaces $q_y$ by $d-q_y$ for a constant $d$ in each fiber, so the excess above the bound is unchanged. Checking all $2^{19}$ representatives excludes 41 marked types. A second calculation evaluates the displayed quadratic form directly on a witness for every exclusion.

For example, an eight-point subset with four points in each fiber and just two edges to its complement cannot occur. Let $v=1_S-(8/20)1_H$, extended by zero outside $H$. Then $\|(3I-A)v\|^2=7 v^\top(3I-A)v=14$. The squared contributions on $H$ sum to at least four, from the incidences of the cut edges. The grid corners contribute zero. The centered counts in the seven other fibers must therefore have total squared norm at most ten. Their means are $0.8$ twice, $1.2$ four times, and $1.6$ once. Rounding within each fiber requires at least $2(1.6)+4(1.6)+2.4=12$.

The [census](../../experiments/workspace/grid_diagonal_halves.py) uses the generators of each bipartite factor and a canonical certificate with an auxiliary vertex for each layer. The [subset checker](../../experiments/workspace/grid_diagonal_cuts.cpp) uses integer arithmetic for the inequality and counts cut edges independently. Run `make verify-grid-diagonals` with Python, NumPy, pynauty and a C++20 compiler.
