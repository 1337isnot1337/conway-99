# Two full axes force mixed matchings

Call a triangle full if it belongs to six grids. Suppose two full triangles meet at a root. Write $c,d$ for their axes and number the remaining axes from 0 to 4. Let $X_i=B_{ci}$ and $Y_i=B_{di}$ denote the four far vertices on each indicated pair of axes. All ten cells are squares. Between $X_i$ and $Y_j$ for $i\ne j$ there is a perfect matching. Each point sees exactly one point of the opposite grid, and the axes are disjoint. There are no edges between the cells when $i=j$, or between different cells on the same side.

A matching is **aligned** if it takes the two sign classes of $c$ onto the two sign classes of $d$, allowing a reversal. It is **mixed** otherwise. At least four of the twenty matchings must be mixed. This applies even if the remaining five axes have arbitrary grid relations. It applies in particular to the [fifteen-grid case](fifteen-grid-root.md).

## The two spectral tests

Suppose all matchings are aligned. Put their sign reversals in a $5\times5$ matrix $P$ with zero diagonal and off-diagonal entries $\pm1$. For a point of $X_i$, the two common neighbors with each signed near point on $d$ are all in the four cells $Y_j$, $j\ne i$. Thus each row sums to zero. The same reasoning gives column sums zero. There are 216 possibilities and four orbits under simultaneous relabeling of the five axes, transposition, and reversal of one full-axis sign convention.

On each square take the unit vector proportional to the distinguished sign ($c$ or $d$). All these vectors are orthogonal to constants. The compression of adjacency to their span has zero diagonal blocks and off-diagonal block $P$. The positive nonprincipal eigenvalue bound of three requires $9I-PP^\mathsf{T}$ to be positive semidefinite. Two of the four orbits survive.

For each signed half of $X_i$ and $Y_i$, take the unit difference of its two points, oriented by the sign of axis $i$. Also take the unit difference of the two near points on each axis $i$. These 25 vectors have disjoint supports. On their span the compression of $4I+A$ has the form $3I+B$. Each diagonal entry is three because the two points of a difference are adjacent. For each $i$, its near difference is joined with coefficient one to the four half-square differences, and the halves of each one square are joined with coefficient one. Between different indices $i,j$ the two edges from $X_i$ to $Y_j$ connect the halves as specified by $P_{ij}$. Their coefficients are independently chosen signs, accounting for both bijections of each pair of two points. All other entries vanish.

Eliminate the five near differences and the ten $X$ differences. Their block consists of five copies of $2I_3+J_3$, whose inverse is $I_3/2-J_3/10$. Each remaining $Y$ half meets one coordinate in each block. In its own block this is the near coordinate with coefficient one. In the other blocks it is the matched $X$ half with a free sign. Multiplying the Schur complement by ten gives diagonal ten. For any two columns start with ten if they are the two halves of one $Y$ square and zero otherwise. For each block subtract the product of the two contact signs times four if they hit the same coordinate, or times $-1$ if they hit different coordinates. This integer matrix must be positive semidefinite.

The [exact verifier](../../experiments/workspace/aligned_spokes.cpp) chooses the eight signs for one $Y$ square at a time. Switching all five coordinates belonging to an index preserves its fixed coefficients. Four such switches normalize the four signs on the first half of $Y_0$. After each pair of columns the numbers of surviving prefixes are respectively

| Orbit | 1 | 2 | 3 | 4 | 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| First | 16 | 870 | 2,566 | 130 | 0 |
| Second | 16 | 870 | 2,566 | 27 | 0 |

Fraction-free elimination tests exact positive semidefiniteness, including the zero-pivot case. A separate calculation formed the signed 25-coordinate matrix, eliminated its fixed block directly, and reproduced each prefix count by numerical diagonalization. The integer check establishes the exclusion.

Finally, fix an $X_i$ square and pull the four neighboring $d$ signs back along the matchings. Each pullback is a balanced sign function on four points, hence one of the three nonconstant binary characters up to sign. Their sum is zero pointwise because of the two-neighbor quotas on $d$. Orthogonality of the three characters forces an even number of each type. In particular the number aligned is even. The same holds at every $Y_j$. The mixed edges therefore form an even subgraph of a simple bipartite graph. It is nonempty by the exclusion above, so it contains a cycle of length at least four.
