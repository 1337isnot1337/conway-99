# Triangle replacements and dual code weights

Let a graph have 99 vertices, degree 14, and exactly one triangle through every
edge. Let a binary linear code C be orthogonal to every graph triangle. Write
g_v for the generator column at vertex v, and B_j for the number of words of
weight j in the dual code. A triangle {a,b,c} satisfies g_a+g_b+g_c=0.

The following necessary inequality holds:

\[
B_3\ge231+7(B_2-B_1).
\]

It uses only these graph hypotheses and triangle orthogonality. It does not
require a full-support code, a particular code dimension, or graph symmetry.

## Exact replacement count

B_1 counts zero columns, and B_2 counts unordered pairs of equal columns.
Each vertex lies on seven triangles. For each equal-column pair {u,v}, replace
u by v in any triangle containing u but not v, and perform the reverse
replacement in any triangle containing v but not u. There are 14 replacements
unless u and v are adjacent. In that case their unique common triangle removes
two replacements, leaving 12.

An equal-column graph edge has a zero-column third vertex on its triangle.
Conversely, each of the seven triangles through a zero-column vertex has an
equal-column opposite edge. This is a bijection even when all three columns of
a triangle are zero. The number of equal-column graph edges is therefore
7B_1. Since these edges are among all equal-column pairs, this also proves
B_2>=7B_1. The total number of replacements is

\[
14B_2-2(7B_1)=14(B_2-B_1).
\]

Every resulting triple is a dual word of weight three. It is not an actual
triangle: its surviving graph edge already has its unique original third
vertex. Conversely, fix a nontriangle dual triple and one graph edge in it.
The unique third vertex on that edge has the same generator column as the
remaining vertex of the triple. This recovers exactly one replacement.

Let n_i count nontriangle dual triples that contain i graph edges. A
nontriangle triple has at most two edges, so

\[
14(B_2-B_1)=n_1+2n_2,
\qquad B_3=231+n_0+n_1+n_2.
\]

The stated inequality follows. The proof does not assume that all nontriangle dual triples arise
from a replacement; those with no graph edges are counted by n_0.

## Independent checks and scope

The separate standard-library audit does not import the enumerator source.
It checks the literal replacement map on all 67 subspaces of the triangle
orthogonal code of the nine-vertex rook graph, all 67 subspaces for two
disjoint triangles, and all five subspaces for one triangle. These controls
use the general identity 2r(B_2-B_1)=n_1+2n_2 when each vertex lies on r
triangles. They check multiplicity for every individual nontriangle triple.

The complete original integer-enumerator source was read. Its 50 distinct
congruences retain all 99 divisibility conditions. The quotient bound
0<=q<=2047 follows from the nonnegative residues, sum A_i=2047 and residual
constant at most 2047. The numerical inequalities produce proposals; the
exact acceptance checks all 100 MacWilliams coefficients. These checks
establish formal enumerators, not actual codes.

The audit independently recomputes all 100 coefficients for both saved
formal points using the binomial Krawtchouk formula. The first point has
B_1=20 and B_2=189. It already fails the elementary condition
B_2>=binomial(B_1,2)=190: zero generator columns give every pair of their
dual unit vectors. The later full-support formal point has
B_1=0, B_2=152, B_3=239. The replacement inequality requires B_3>=1295,
so its deficit is 1056. Neither formal point can be the code of a graph with
the stated triangle properties. No exclusion of all admissible codes or of
the Conway graph is claimed by this review.

## Exact replacement LP certificate

The audit also reads the separate replacement-bound source and independently
reconstructs its 101 inequalities from the binomial Krawtchouk formula. The
99 parent forced-word lower bounds are preserved; their earlier combinatorial
proofs are outside this review. The two new pullbacks are checked coefficient
by coefficient, including the constant term coming from A_0=1 and the total
code size M=1+sum A_w.

All 101 primal inequalities, seven nonnegative primal coordinates, 101 dual
signs, and seven dual coefficient inequalities pass exact rational arithmetic.
The primal objective equals the dual bound:

\[
M\le\frac{560594944}{189229}.
\]

The nonzero dual multipliers are 61/1703061 on the weight-four row,
65/1703061 on the weight-five row, 3868/1703061 on B_2-7B_1>=0, and
407/567687 on B_3-7B_2+7B_1>=231. The bound lies between 2048 and 4096,
so it retains the dimension-at-most-eleven conclusion and incidence rank
at least 88. It does not exclude dimension eleven. The audit calls no
optimizer and imports none of the subject model sources.

Replay from the repository root:

```sh
python experiments/workspace/triangle_incidence_binary_replacement_independent_audit.py replay --certificate experiments/logs/grids-and-triangles/triangle-incidence-binary-replacement-independent-audit.json --output /tmp/triangle-replacement-independent-replay.json
```
