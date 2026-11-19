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

## Excluding a four-cycle of mixed matchings

In fact at least **six** edges must be mixed. Four edges of an even bipartite graph form a rectangle. The two row indices and the two column indices must be disjoint, since no diagonal edge exists. Relabel them as rows 0,1 and columns 2,3. Put zeros on the rectangle and retain the aligned signs on its complement. The aligned signs in each row and column still cancel. There are 38 such arrays and five orbits under simultaneous axis relabeling preserving the rectangle, transposition with relabeling, and global negation.

Number the three sign characters of a square as 0 (distinguished axis), 1 (indexed axis), and 2 (product). Each bijection on four points acts by a signed permutation on these characters. On each mixed row the two distinguished characters pulled back from the right are opposite copies of the same character, either 1 or 2. Likewise on each mixed column for pullbacks from the left. Flipping the indexed-axis sign switches both characters 1 and 2. Because the four indices concerned are distinct, these switches independently fix the first orientation in each of the two rows and columns. The row and column pullbacks specify a mixed bijection uniquely: they specify the images of two independent binary characters, including their signs. There are $2^4$ choices of character types per sign-array orbit. On an aligned edge all four bijections with the specified aligned sign remain available.

Here is the matrix test used on the resulting 80 templates. Work in the near sign differences and the three unit characters on each of the eleven known squares. Use both $4I+A$ and $3I-A$ on this space orthogonal to constants. Eliminate the characters of $B_{cd}$ and then the near sign differences. The internal block on either set of five spokes has the following form, with the characters grouped by type. Write $J_5$ for the five-by-five all-ones matrix.

| Form | Distinguished block | Indexed block | Product block | Indexed contact at equal indices |
| --- | --- | --- | --- | --- |
| $4I+A$ | $4(I-J_5/5)$ | $(10/3)I$ | $2I$ | $-2/3$ |
| $3I-A$ | $3(I-J_5/5)$ | $(5/2)I$ | $5I$ | $-1/2$ |

For example the coupling between a square character and its signed near axis is $\sqrt2$. In $4I+A$, eliminating $B_{cd}$ leaves diagonal $3-2/4=5/2$ at $c,d$ and three at each other near difference. This gives the first row of the table. In $3I-A$ the corresponding diagonals are $4-2/3$ and four, giving the second row. At different indices the contact block is the signed permutation of the matching, with the sign of $A$ in the chosen form.

Eliminate the left spokes on the orthogonal complement of their one distinguished constant direction. The cancellation conditions make all right columns orthogonal to that kernel. The inverse weights on the left are respectively $(1/4,3/10,1/2)$ and $(1/3,2/5,1/5)$. In particular, if $D$ is the right diagonal block in the table and $V$ is the full contact matrix, the remaining form is $D-V^{\mathsf T}D^{+}V$. Here the left and right diagonal blocks coincide, and the superscript denotes the inverse on the kernel complement. Multipliers 20 and 15 make the two remaining forms integral.

The [template generator](../../experiments/workspace/mixed_spoke_templates.py) supplies the matching domains. The [exact search](../../experiments/workspace/mixed_spokes.cpp) checks both forms on the five distinguished characters, which are independent of the remaining choices. It retains four of these characters and adds the other two characters of each right spoke, first processing the two columns with mixed matchings. The fifth distinguished character is redundant by cancellation. Summed over all 80 templates the numbers of retained prefixes are 256, 878, 3,000, 156, and **zero**. Integer fraction-free elimination makes every rejection. A separate numerical implementation using explicit real-valued Schur complements produced the same counts. Since every mixed subgraph has an even number of edges, this excludes all counts below six.

## The six-edge case and the rank test

The restriction strengthens to **at least eight mixed matchings**. A six-edge mixed support is an even subgraph of the bipartite graph obtained from $K_{5,5}$ by deleting its diagonal. Enumeration gives 130 labeled supports in three orbits. The same sign-array and character calculations extend to this case. If an index occurs on both sides of the mixed subgraph, its indexed-axis sign switch normalizes the first mixed edge in its row only. If it occurs only on the right, it normalizes the first mixed edge in its column. This gives 2,304 templates.

Eight complete assignments pass both semidefinite inequalities. Each fails the rank bound. To see the required rank, split the 59 coordinates orthogonally into vectors constant on each near pair and four-cell (also allowing the root), and the signed coordinates used above. The constant space has dimension 19 and the graph preserves both spaces on the 59-point core: the disjoint-cell interfaces are permutations and the counts to near-axis pairs are constant within each cell. On the constant space $27I-9A+J$ has rank seven. Its kernel contains the eleven independent grid indicators and $(A+4I)e_p$. Independence follows from the distinct far-cell supports. On the other hand, the Gram on the seven near-pair indicators has diagonal 40 and off-diagonal 4, hence rank seven.

In the signed space, eliminating the three $B_{cd}$ characters, the seven near differences and the nonkernel left-spoke directions contributes $3+7+14=24$ to the rank. The rank of the full negative projector is 44. Thus the remaining form for $3I-A$ must have rank at most $44-7-24=13$. Each of the eight survivors has rank 14 on the retained characters. Independently, [building the ordinary 59-vertex matrix](../../experiments/workspace/spoke_core_rank.py) for each survivor gives rank 45 for $27I-9A+J$ by elimination over $\mathbb F_{1009}$.

To replay the six-edge test, run the template generator with argument 6. Passing its output to the C++ verifier with option `--survivors` prints the two ranks and the intercell permutations (lexicographic indices among the 24 permutations, in row-major cell order).
