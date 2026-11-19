# A Fano-plane pairing cannot occur at a one-fixed-point involution

Suppose an involution fixes a unique point $o$ in a Conway graph. Its 14 neighbors form seven swapped pairs, called axes. The other 84 points form 42 swapped pairs, called far orbits. A far orbit has a label consisting of the two axes its points see. Each of the 21 two-axis labels appears twice. Every far orbit has a unique complete bipartite interface with another far orbit. Together the two orbits induce a square. These facts and the even quotient equations follow from the [one-fixed-point reduction](../../STATE.md).

Consider a Fano plane on the seven axes. On each line $\{a,b,c\}$, pair far orbits of labels $ab,ac$ in one square, $ba,bc$ in another, and $ca,cb$ in a third. This uses both copies of each label. **This pairing is impossible**, even if the rest of the graph breaks every symmetry of the Fano plane. The proof derives the inter-square edge counts from a small Gram matrix and excludes all 104 resulting cases.

## The Gram matrix for any pairing

Let $U$ be the $7\times42$ matrix of far-orbit labels, with two ones per column. In each square $s$ choose an order for its two far orbits. Write $m_s$ for the sum of their label columns and $\delta_s$ for their difference. Form $M$ and $\Delta$ from these 21 columns. Write $N_{st}$ for the number of single matching interfaces between far orbits in different squares, with $N_{ss}=0$. Each vertex outside a square sees at most one point from each diagonal, since the two diagonal points already have two common neighbors in the square. Three single interfaces would produce an L-shape in the two-by-two array of orbit pairs. At its middle edge the other two single interfaces each give a different common neighbor via one of the two complete diagonal-orbit interfaces. This violates the adjacent-pair quota. Thus $N_{st}\in\{0,1,2\}$.

Use the negative Gram matrix $G=27I-9A+J$. On the seven axis indicators it has Gram matrix $36I+4J$. Their inner products with a square indicator form the column $8\mathbf1-18m_s$. The square indicators have squared norm 52 and mutual inner products $16-18N_{st}$. Subtract the projections onto the axis indicators and divide the resulting Gram matrix by nine. The result is
\[
K=4I+4J-2N-M^\top M .
\]
In particular $K_{ss}=4-2k_s$, where $k_s$ is the number of axes shared by the two labels of the square. Indeed $\|m_s\|^2=4+2k_s$. This construction applies to any pairing.

For the parity of the vectors, let $x_s$ be the indicator of the square plus $e_o$ plus half the sum of the axis indicators weighted by $m_s$. Its $G$ coordinates are the projection residual just used: $4e_o$ plus the sum of the axis indicators lies in the kernel of $G$. Since $x_s$ has coordinate sum nine,
\[
z_s=(3I-A)x_s+\mathbf1,\qquad z_s^\top z_t=7K_{st}.
\]
This follows from $3I-A+J/9$ being seven times the orthogonal projector onto the $-4$ eigenspace. At any point in a far orbit labeled $ij$, the parity of $2z_s$ is $m_s(i)+m_s(j)$ modulo two.

## Determining the interfaces in the Fano case

Index a square by its Fano line and its center $c$, the common axis of its labels. Call the other two axes its endpoints. Every pair of axes occurs exactly once as endpoints. Each vector $r_s=z_s/\sqrt7$ has squared norm two. No two different $r_s$ coincide up to sign: the parity masks of $2z_s$ on the far labels distinguish their endpoints. Indeed two indicator vectors agreeing in their parity sums on every pair differ by a constant modulo two, and two different two-element sets among seven axes cannot be complements. Thus distinct inner products are $0,1,-1$. Their parity from $K$ is the parity of the number of shared endpoints. If two endpoint pairs are disjoint the inner product vanishes, and if they meet it is a sign.

For each axis $p$ take the six endpoint pairs through it. The product of the three inner-product signs on any triple of these vectors is positive. Otherwise one could change their signs to give all three inner products $-1$ and hence a zero sum. Reducing the corresponding three vectors $2z_s$ modulo two contradicts this: the symmetric difference of their endpoint sets has four elements, and so has nonconstant membership on the axes. Consequently the signs for a star factor as $\sigma_{p,s}\sigma_{p,t}$, by comparing each pair with a reference member of the star. The whole matrix $K$ is the Gram matrix of seven-coordinate columns with these signs at the two endpoints.

Within one Fano line two distinct columns $m_s,m_t$ have dot product five. Thus $K_{st}=-1-2N_{st}=-1$, so the two endpoint signs at their shared axis are opposite. At each of the seven axes there remain three binary choices, one for each incident Fano line. Simultaneously reversing all three signs at an axis leaves the Gram matrix unchanged. There are $2^{14}$ sign choices after this normalization. In each one, $N=(4I+4J-M^\top M-K)/2$ is determined. Permuting the seven nonzero vectors of $\mathbb F_2^3$ by its 168 invertible linear maps leaves 104 interface classes. This relabeling uses no presumed automorphism of the graph.

## The remaining exact obstruction

Let $B$ be the $42\times42$ even far-orbit matrix with its internal double edges. The quotient equations are
\[
UB=4J-2U,\qquad B^2+B=12I+4J-U^\top U.
\]
Change to the normalized sums and differences of the two orbit coordinates in each square. The sum-sum block of $B$ is $2I+N/2$. Write $L/2$ for its sum-difference block. Thus $L_{st}$ is the difference of the two column sums of the binary interface from $s$ to $t$. For $N_{st}=0,1,2$ its possible entries are, respectively, $0$, $\pm1$, or $0,\pm2$. The diagonal is zero.

The two quotient identities give the complete Gram matrix of the vertically stacked array $Y=(\Delta;L)$:
\[
\Delta L^\top=16J-8M-MN,\qquad
LL^\top=24I+32J-2M^\top M-10N-N^2 .
\]
The top block $\Delta\Delta^\top$ is already known. Every column of $Y$ must be perpendicular to the exact rational kernel of that Gram matrix. There are twelve entries restricted to $\pm1$ and four restricted to $0,\pm2$ in the lower part of each column. Split them in half and match their residues on a primitive integer kernel basis modulo 1009. Every match is then tested over the integers.

All 104 classes admit individual columns at all 21 positions. Two required Gram matrices have rank 12, and the other 102 have rank 13. To test joint existence, select one outer product per column. For every matrix entry bound the remaining sum by adding the minimum and maximum contributions at each position. Eliminate choices that violate these bounds and branch on the smallest surviving domain. **None of the 104 classes has the required sum.** The [exact checker](../../experiments/workspace/involution_fano_squares.py) recreates the sign enumeration, rational kernels, individual column sets and integer refutations. Run `python experiments/workspace/involution_fano_squares.py` with NumPy and python-flint.
