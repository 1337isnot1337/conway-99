# No endpoint component can contain six axes

Consider any involution of a Conway graph with just one fixed point. Draw an edge between the two endpoints of each far square whose labels share exactly one axis. **Every component of this graph on the seven axes has at most five vertices.** This holds for arbitrary numbers and placements of squares with disjoint or identical labels. In fact, the even far quotient cannot support the five virtual eigenvectors associated with a tree on six axes.

## A tree supplies the virtual differences

Write $B$ for the symmetric even far quotient and $U$ for its seven-by-42 axis incidence matrix. Each two-axis label occurs twice. The diagonal of $B$ is zero, and each row has ten ones and a single two. The [quotient equations](fano-square-pairing.md) give
\[
 UB=4J-2U,\qquad B^2+B=12I+4J-U^\top U.
\]
Let $S_a$ be the twelve orbits labeled by axis $a$. The weight of a row into $S_a$ is two inside the set and four outside.

If a component has at least six axes, take five squares whose endpoint pairs form a tree on six of them. The associated norm-two roots $r_s$ have lifts $Z_s$ which are integral, have eigenvalue $-4$, and vanish under $U$. Their scalar products scale by 14 on lifting. Their lifted parities are the cuts defined by their two endpoints. The [star-sign argument](distinct-endpoint-squares.md) uses only the chosen squares. Distinct tree edges are orthogonal if disjoint and have inner product $\pm1$ if incident. The product on any three edges at a star is positive, since a negative product would give a signed zero sum with a nonzero parity cut. Thus the roots have the Gram matrix of a signed incidence representation on the six coordinates. On a tree the coordinate signs can always be switched, starting at a leaf, to turn every edge into a signed coordinate difference.

For every two active axes $a,b$, adding signed tree-edge lifts along the path gives an integer vector $f_{ab}$, the image of $e_a-e_b$. These vectors have squared norm 28, eigenvalue $-4$, $Uf_{ab}=0$, and parity one precisely on the 20 orbits whose labels contain exactly one of $a,b$. There are integer row potentials $h_t$ on the six active axes with $f_{ab}(t)=h_t(a)-h_t(b)$. For example one can use the differences from a fixed base coordinate.

## The two entries of magnitude two

Fix $f=f_{ab}$. Its 20 odd entries consume at least 20 of the norm budget of 28. An entry of magnitude three would consume the other eight. Its row would then have to receive weight twelve from other odd entries to attain $|(Bf)_t|=12$. It belongs to exactly one of $S_a,S_b$, so its weight into their union is at most six. It follows that the odd entries are all $\pm1$ and precisely two even entries are $\pm2$.

Both entries of magnitude two lie outside $S_a\cup S_b$, with opposite signs. To see this, suppose one lies in $S_a\cap S_b$. Its row has weight at most four into odd entries. To reach $|(Bf)_t|=8$, the other large entry must have the opposite sign and receive the unique weight two. If it were also in the intersection, it would exhaust that row's weight into each of $S_a,S_b$, leaving no odd contribution. If it is outside the union, the two large entries must instead have the same sign. Indeed $Uf=0$ gives zero sum on each of $S_a,S_b$ and on the whole quotient (every label has size two), so the sum on the intersection equals the sum outside the union. This proves the assertion.

In a row labeled by two active axes their potentials therefore agree. Every label contains at least one active axis. Normalize its row potential by a translation to make the active label coordinates one. Each of the other active coordinates is then zero or two, since its difference from a label coordinate is odd. Let $T_t$ be the subset where the potential is two and let $O_t$ consist of the active axes outside the label. This row realizes $f_{ab}(t)=2$ exactly on the directed cut $T_t\times(O_t\setminus T_t)$. Each ordered pair of distinct active axes is realized exactly once. Thus the nonempty cuts partition the 30 ordered pairs, with at most two rows of a given label.

## Completing the rows

For a chosen collection of nonempty cuts let $c_{ai}$ count rows with label containing $a$ and raised subset containing $i$. Write $x_{ab}$ for the number of remaining rows of label $ab$ raised on all outside coordinates. All other remaining rows raise none. Write $d_a=\sum_{b\ne a} x_{ab}$ and denote the inactive axis by $*$. On the twelve rows in $S_a$ for active $a$, the column for $a$ sums to twelve. The column for any other active $i$ must have the same sum because $Uf_{ai}=0$. Two rows of label $ai$ contribute one each, giving
\[
 d_a-x_{ai}+c_{ai}=5.
\]
Summing over the five other active axes gives $4d_a=25-\sum_i c_{ai}-x_{a*}$. Here $0\le x_{a*}\le2$, so its residue modulo four determines it uniquely if it exists. This recovers all $x_{ai}$. Enforce symmetry and the two-row multiplicities. On the inactive axis the column sums must also agree, which says that $c_{*i}-x_{i*}$ is constant in $i$.

The [checker](../../experiments/workspace/involution_axis_frame.py) enumerates directed covers by choosing an uncovered ordered pair with the fewest admissible cuts. Permuting the six axes lets it fix one initial event for each cut type. Across those branches there are 8,028 terminal covers and 800 completions satisfying the axis equations, counting repetitions across normalized branches. Relabeling active axes, swapping the two rows of a label, and reversing every virtual vector leaves 26 classes. For the reversal the normalized potentials become $2-h_t$.

## One or two quotient rows give a contradiction

For each class choose a row $i$ where some difference has magnitude two. Test for eleven positive positions off its diagonal, ten with weight one and one with weight two. Impose its seven equations from $UB$ and its five independent eigenvector equations from $Bf=-4f$. In 23 classes one such row is already impossible.

For each remaining class choose the two rows $i,j$ where a common difference has magnitude two. Impose those same row constraints, symmetry at their intersection, and the common-neighbor identity
\[
 \sum_k B_{ik}B_{jk}+ B_{ij}=4-|u_i\cap u_j|.
\]
Each product is at most two because a quotient column has only one entry of weight two. Each of the three classes has a pair for which this is infeasible. The search permits any positions for the double weights and imposes no conditions on the other squares. Reproduce with `make verify-involution-axis-frame` in a Python environment with OR-Tools.

For an independent certificate of each row obstruction run `make certify-involution-axis-frame` with python-sat, CaDiCaL, and drat-trim. The second encoding represents a weight by two Boolean variables, counts repeated literals with a sequential counter, and expands the common-neighbor product into Boolean conjunctions. The checker independently verifies all 26 generated DRAT proofs.
