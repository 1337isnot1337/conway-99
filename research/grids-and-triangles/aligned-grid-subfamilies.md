# Eight grids cannot all preserve opposite corners

Fix a vertex of a Conway graph. Each grid through it uses a pair of the seven axes. Its four far points form a square. Between two such cells on disjoint axis pairs there is a perfect matching. Call it aligned when it takes opposite square corners to opposite corners. **In every family of eight grids through the vertex, at least one matching on disjoint axis pairs is not aligned.** The graph and the chosen grids need no symmetry.

In particular, the unique fixed point of an involution lies in **at most seven grids**. Such an involution reverses all seven axes. On each cell it interchanges diagonally opposite corners. Every matching between disjoint grid cells commutes with this action and hence preserves the opposite-corner partition.

## Checkerboard vectors and their parities

Choose on each selected grid cell $e$ a vector $d_e$ with alternating entries $+1,-1,+1,-1$ on the square and zero elsewhere. Write $Y_e=(A+4I)d_e$, where $A$ is the original adjacency matrix. The near vertices see either two opposite signs or no points of the cell; thus $Y_e$ vanishes there and at the root. At a far point of label $f$, its value is $2d_e$ when $f=e$, zero when $f$ meets $e$ in one axis, and $+1$ or $-1$ when they are disjoint. Indeed the [grid domination identity](grid_intersections.md) gives respectively two internal neighbors, zero neighbors in the cell and one neighbor in the cell.

For a fully aligned selected family form the matrix
\[
 K_{ef}=d_e^\top(A+4I)d_f/4 .
\]
It has diagonal two, zero on intersecting labels and a sign on disjoint labels. On the four vertices of any selected cell $f$, the rows of $Y$ are $d_f(t)K_{f,:}$. From $A^2+A=12I+2J$ and $Jd_e=0$ we obtain
\[
 Y^\top Y=28K .
\]

Let $D$ be the 21-by-21 zero-one disjointness matrix on axis pairs. Its column for $e$ gives the parity of $Y_e$ on every far cell. Any primitive integer kernel vector of $K$ therefore has a nonzero binary reduction in the kernel of $D$, extending it by zero on unselected labels. To describe the latter kernel, write $S$ for the total binary weight and $b_i$ for the degree parity at axis $i$ of its support. The equation at label $ij$ is $x_{ij}=S+b_i+b_j$ modulo two. A nonzero support is consequently a cut of the complete graph on seven axes or the complement of a cut. The only possibility of size at most eight is a full six-edge star.

If the family includes this full star and two other edges, take one of the latter as $e$. Four of the star edges are disjoint from $e$. In the $Y/\sqrt{28}$ representation their roots are pairwise orthogonal of squared norm two; their inner products with the root of $e$ are signs. Subtracting their signed sum from twice that root gives squared norm zero. The resulting relation has exactly four odd coefficients, which the disjointness parity excludes. In every remaining eight-edge family the Gram matrix must be positive definite.

## Testing all eight-grid families

The [integer checker](../../experiments/workspace/aligned_grid_subfamilies.py) generates the unlabelled seven-axis graphs by vertex extension. Exactly 97 have eight edges; two contain the full star. In each other graph reverse checkerboard signs individually to fix the positive signs on a spanning forest of the disjointness graph. Enumerating all remaining signs gives 22,216 matrices. Exactly eight are positive definite, by their leading principal minors.

For each far cell $f$, let $P_f$ be a superset of its possible rows of $Y$. If $f$ is selected, take the two signed copies of its Gram row. Otherwise enumerate all independent signs in positions disjoint from $f$, with zeros elsewhere. The projection identity is
\[
 \sum_{t\text{ far}} Y_{t,:}K^{-1}Y_{t,:}^{\top}=28\cdot8.
\]
There are four vertices per cell. In six of the eight cases, the sum over cells of the individual minimum row costs already exceeds $7\cdot8$. In the other two it equals the budget, forcing every row to attain its own minimum.

For each column pair $i,j$, the cellwise average of $Y_{ti}Y_{tj}$ over its four vertices must lie between the minimum and maximum of that product on the remaining rows. The 21 averages must sum to $7K_{ij}$. One matrix misses a required interval outright. For the other, several sums saturate their endpoints and some cell has no row attaining all the required extrema. This exhausts the family. Run `make verify-aligned-grid-subfamilies` with the project Python dependencies to replay the proof, including the integral adjugate calculations.
