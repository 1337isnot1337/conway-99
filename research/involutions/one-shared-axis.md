# The 21 squares cannot all have one shared axis

At a one-fixed-point involution, the 42 far orbits pair into 21 squares. **At least one square must pair two disjoint axis labels or two identical axis labels.** In the identical case the square lies in a complete grid through the fixed point. This result imposes no additional automorphism on the quotient or the graph.

Suppose instead every square has exactly one shared axis. The [connected-component and tip arguments](connected-endpoint-squares.md) leave six axes in one connected endpoint component, with a seventh isolated axis. Each far orbit labeled by the isolated axis belongs to a square centered there. There are six such squares and fifteen squares centered on active axes. Write $U$ for the axis labels and use the integer columns $Z_s$ from the [norm proof](distinct-endpoint-squares.md).

## The six-axis representation is balanced

The proof for seven connected axes applies to the six active axes after modifying its obstruction to integral unit vectors. In either the full-rank signed-incidence case or the case of orthogonal roots on a repeated endpoint pair, that proof provides six integral $-4$ eigenvectors of $B$ of squared norm 14. The line-graph theorem also applies to a connected graph on six axes. In each of the 42 rows, the six column parities are the active part of the row label or its complement. Let $h$ rows be complemented, of which $h_i$ have labels containing active axis $i$. The original labels give 72 odd entries. Each flip adds at least two: the original row has one or two active axes. Total squared norm 84 implies $h\le6$.

In the column $f$ for $i$, at least $12-h_i$ units of absolute mass lie on the 12 orbits $S_i$ labeled by $i$. Outside there are $h-h_i$ odd entries. The whole column has $12+h-2h_i$ odd entries; every further unit of absolute mass costs at least two units of squared norm. Thus its absolute mass outside $S_i$ is at most $h-h_i+(2-h+2h_i)/2=1+h/2$. Summing $|Bf|=4|f|$ on $S_i$ and using the column weights two inside and four outside gives $12-h_i\le 2+h$. But $\sum_i h_i\le2h$, which would require $6(10-h)\le2h$, impossible for $h\le6$.

It follows that repeated roots are parallel and each square has an oriented endpoint column $v_s=e_p-e_q$ on the six axes. The isometry scaling squared norms by 14 gives a virtual column for any coordinate difference, even a missing endpoint pair. All these columns are integral, with squared norm 28 and the parity mask of the corresponding pair of axes. Their potentials have equal values at the two members of a far label whenever both belong to the six active axes, by the own-label argument.

## Integer representatives of the potentials

Let $V$ have columns $v_s$, and let $M$ have the label sums restricted to the active axes. In a square with source $p$, sink $q$ and center $c$, order its two orbits by their labels $cp,cq$. Add constants to the potentials of the two orbits so that the first has coordinate $q$ equal to zero, and the second has coordinate $p$ equal to zero. Both potentials have difference one from $p$ to $q$. The square-sum identity for virtual columns then makes their sum exactly $v_s$.

On active coordinates these two rows of a $42\times6$ integer matrix $H$ are consequently
\[
e_p+e_c+2k_s,\qquad -e_q-e_c-2k_s,
\]
where $e_c$ means zero for the isolated center. The integer column $k_s$ vanishes at the endpoints and the center. Indeed the parity mask determines the even coordinates of the first row, and when $c$ is active its value equals one by the label equality. Write $D$ for the matrix with columns $k_s$.

We have $\sum_s v_s=0$. The square Gram matrix $K$ annihilates the all-ones vector by its formula, since $N$ has row sum 20 and the seven-axis label-sum matrix has row sums 12 and column sums four. The balanced representation now gives the assertion. For every active $i$, the diagonal entry $(UH)_{ii}$ vanishes: centered squares cancel in pairs, while the endpoint contributions sum to the oriented degree difference at $i$. Also $U(H_i-H_j)=0$ for all active coordinate columns, since these are virtual negative eigenvectors vanishing on all near orbits. Thus the six active rows of $UH$ vanish. Taking the sums and differences in the two orbits of each square gives
\[
 MV^\top + V(M+4D)^\top=0.
\]
It follows that $VD^\top$ is symmetric and has row sums zero (its column sums vanish since each $v_s$ sums to zero).

## Fifteen independent pair budgets

For any two active coordinates $i,j$, write $\partial x=x_i-x_j$. The norm of the virtual column $H_i-H_j$ gives
\[
\sum_s\bigl((\partial v_s)^2+(\partial(m_s+4k_s))^2\bigr)=56.
\]
Replacing $m_s+4k_s$ by $m_s$ on the left gives 40: $v_s,m_s$ are the difference and sum of the two labels, and exactly 20 far orbits have labels containing one of $i,j$. Each of the fifteen pairs therefore has the exact budget
\[
\sum_s\bigl((\partial m_s+4\partial k_s)^2-(\partial m_s)^2\bigr)=16.
\]
Every summand is nonnegative because $|\partial m_s|\le2$. Comparing a coordinate outside the center and endpoints with $p$, where $m_s(p)=1$, forces its $k_s$ value to be zero or one: any other value already costs more than 16. Thus $k_s$ is the indicator of a subset of the active axes outside $p,q,c$.

Divide the pair budgets by eight. A nonempty subset contributes one for each pair joining an endpoint to the subset, and two for a pair joining the subset to another active axis outside the center and endpoints. All other pairs cost zero. The total cost is $2l(4-l)$ for an active center and $2l(5-l)$ for the isolated center, where $l$ is the size of the subset. It is at least six, so at most five squares have nonempty subsets.

The [standard-library checker](../../experiments/workspace/involution_six_axis_cover.py) exhausts the resulting small cover problem. It enumerates all 645 endpoint, center and nonempty subset choices. Normalize one of highest cost by permuting the six active axes. This gives seven starting types. At each node choose an unfilled pair and try every event covering it without exceeding any budget; repetitions and all admissible orderings are allowed. On reaching all fifteen totals, test all signs for the oriented endpoints, checking zero row sums and symmetry of $VD^\top$. Across 104 terminal orderings, 208 sign assignments have zero row sums and none is symmetric. This contradiction excludes the last component case. Run `python experiments/workspace/involution_six_axis_cover.py` to replay it.
