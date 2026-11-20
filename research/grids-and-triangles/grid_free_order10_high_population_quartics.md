# Bounded populations of high neighborhood classes

## Result

The current 48-cut integer count point passes 3,583 exact polynomial inequalities across 153 neighborhood-class families.
The scan covers all 62 six-vertex roots and takes 2.713 seconds.
It finds no negative polynomial.
These finite tests do not construct a graph or a joint distribution across all classes.

The [source](../../experiments/workspace/grid_free_order10_high_population_quartics.py) uses only the complete existing moments through degree four.
The [result](../../experiments/logs/moments-and-counts/order10-high-population-quartics-scan01.json) has SHA256
`8afaa028d2ef8b43b561ba2f0de2f41413748632d8e2666e8eb1ef7c22884fec`.

## Population bounds

Fix an actual six-vertex root with adjacency matrix \(B\).
For distinct root vertices \(i,j\), the remaining common-neighbor quota is

\[
G_{ij}=2-B_{ij}-(B^2)_{ij}.
\]

For a subset \(C\) of root vertices, define

\[
R_C=\sum_{\{i,j\}\subseteq C}G_{ij}.
\]

Every outside vertex contributes one unit for each pair of its neighbors in \(C\).
Therefore

\[
R_C=\sum_{v\text{ outside the root}}\binom{|N(v)\cap C|}{2}.
\]

The sum uses unordered pairs. There is no factor of two.
Every omitted outside vertex has a nonnegative contribution.

A high class has at least three neighbors in the root.
Each high class is binary because two vertices in that class violate the common-neighbor cap.
Let \(X_h\) denote its indicator.
For a family \(F\), let \(S=\sum_{h\in F}X_h\).
If every \(h\in F\) contributes at least \(m>0\) to \(R_C\), then

\[
0\le S\le \left\lfloor R_C/m\right\rfloor.
\]

The class count also gives \(S\le |F|\).
The preparation checks every core subset \(C\) and takes the smallest resulting bound \(U\).

The family list contains all high classes, each exact neighborhood size, and each threshold size from four to six.
The preparation merges equal mask sets and omits empty families using the domain alone.
It retains all roots and uses no count-dependent pruning.
The 153 distinct families have 3,055 positive subset-capacity bounds.
Every resulting upper bound is at most ten.

## Polynomial expectations

For each family, the scan evaluates the following polynomials on its unnormalized moments:

\[
1,\quad S,\quad U-S,\quad S(U-S),
\]

\[
(S-i)(S-i-1)(S-j)(S-j-1),\qquad 0\le i\le j<U,
\]

\[
S(U-S)(S-i)(S-i-1),\qquad 0\le i<U.
\]

Every polynomial is nonnegative at each integer in \(\{0,\ldots,U\}\).
The preparation checks all those values exactly and removes duplicate polynomials.
This note makes no completeness claim for other polynomials or other mask families.

Let \(m_T\) be the labelled moment of \(\prod_{h\in T}X_h\).
Define

\[
e_j=\sum_{\substack{T\subseteq F\\|T|=j}}m_T.
\]

The empty moment \(e_0\) is the number of labelled root embeddings. It is not one.
For \(p(S)=\sum_{k=0}^4p_kS^k\), the expectation is

\[
\sum_{j=0}^4\beta_je_j,
\qquad
\beta_j=j!\sum_{k=j}^4p_k\left\{\begin{matrix}k\\j\end{matrix}\right\}.
\]

The braces denote Stirling numbers of the second kind.
Each distinct-mask moment includes every allowed internal edge pattern.
The conversion uses no free-vertex automorphism divisor.
Induced counts receive the catalogue automorphism multiplier before contraction.

## Checks and scope

The preparation reads no count point or product tensor.
Its controls include 5,376 exact pair-inventory identities on the nine-vertex rook graph.
The independent review reconstructs all families, bounds, and polynomial lists.
Finite differences independently reproduce every coefficient \(\beta_j\).
The review checks 25,168 integer evaluations and 7,166 mixture identities.

The scan uses the frozen contraction bounds and checks the complete monomial-reference stream for every root.
All later moment sums and polynomial evaluations use Python integers.
The scan commits each complete root and its saved forms together.
An interrupted root contributes no partial result.

The 60-second alarm covers contraction and scanning after preparation checks and input loading.
The alarm does not bound the total invocation time.
The completed scan uses one thread and no optimizer.
It generates no new tensor or reduced count matrix.

The [independent review](../../experiments/logs/moments-and-counts/order10-high-population-quartics-independent-review.json) records its exact checks and source hashes.
The [preparation](../../experiments/logs/moments-and-counts/order10-high-population-quartics-preparation.json) retains every bound and polynomial.
The complete result covers only these listed necessary inequalities at the saved point.
