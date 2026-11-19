# A core matching inequality after complete selector reconstruction

## What remains to be realized

The full nonabelian selector layer identifies one Boolean vector on the 480
literal signatures. Its Fourier columns are linear functions of that same
vector. Consequently each two-dimensional Gram block is of the form
\(C^{T}HC\), with \(H=\begin{pmatrix}2&-1\\-1&2\end{pmatrix}\).
Positive semidefiniteness, rank at most two, and the identity
\[
B_{uu}B_{vv}-B_{uv}^{2}=3\det[u,v]^{2}
\]
then hold automatically. Repeating these pure-selector tests adds no
condition once the inverse links and exact Gram-product links are enforced.
This assertion concerns the complete linked model. It does not apply to a
model that retains only selected Gram entries or independent local tables.

The remaining edge problem is different. Let \(S\) be the 60 selected
signatures, let \(W\) contain their incidence columns on the fixed
18-vertex component, and let \(D\) be that component's adjacency matrix.
An actual exterior graph has one symmetric Boolean adjacency matrix \(A\)
on \(S\), with zero diagonal, satisfying
\[
WA=2J-(D+I)W,\qquad A\mathbf1=8\mathbf1.
\]
The second equation follows from the first because every incidence column
has weight three and every mixed target has sum 24. Eligible edges, all
common-neighbor caps, and global motif restrictions impose further
conditions.

The orbit variables \(Y_R\) record numbers of actual edges in each finite
core-action orbit. The current averaged equalities and inequalities do not,
by their definition alone, construct this single Boolean matrix \(A\).
The earlier local-neighbor witnesses also chose their neighbors separately.
No claim is made here that the new inequality is independent of the complete
current constraint system.

These normalizations are fixed in
[the fractional-model plan](root_prism_free_f0_fractional_model_plan.md)
and [the nonabelian reconstruction proof](root_prism_free_f0_nonabelian_pair_factorization.md).

## Eight vertices must pair off at each fixed core site

For a core site \(i\), define
\[
U_i=\{a:i\in h_a,\ h_a\cap N_D(i)=\varnothing\}.
\]
Equivalently, \(i\in h_a\) and the mixed target
\(q_{ai}=2-\mathbf1_{i\in h_a}-|N_D(i)\cap h_a|\) equals one.

Every selected \(a\in U_i\) is adjacent to \(i\) and has no already-fixed
common neighbor with \(i\). Since \(\lambda=1\), exactly one exterior vertex
must complete the unique triangle through the edge \(ia\). Its signature
also lies in \(U_i\). If it had a neighbor of \(i\) in the fixed component,
that fixed vertex and \(a\) would be two common neighbors of its edge to
\(i\). Therefore the actual edges among the selected vertices of \(U_i\)
form a perfect matching.

There are exactly eight selected vertices in \(U_i\). This follows directly
from the original Gram rows:
\[
\sum_{a\in U_i}x_a
 =G_{ii}-\sum_{j\in N_D(i)}G_{ij}
 =10-2=8.
\]
The attached checker verifies the coefficient identity on all 480 literal
coordinates at each of the 18 core sites. This is an original-row
consequence, not a new population assumption.

The complete possible sets have sizes 50 at sites 0 through 5 and 61 at
sites 6 through 17. These cardinalities describe possible signatures;
exactly eight are selected at each site in an actual incidence.

For any fixed subset \(T\subseteq U_i\), matching edges satisfy
\[
\sum_{\{a,b\}\subseteq T} y_{ab}\le
\left\lfloor\frac{|T|}{2}\right\rfloor,
\]
where ineligible or proved-zero edges contribute zero. These are ordinary
matching odd-set inequalities. Their validity does not require any symmetry
of a hypothetical graph.

## One explicit three-edge inequality

Take \(i=0\) and the following literal signatures, using the frozen
zero-based indices.

| Signature ID | Core neighbors |
|---:|---|
| 1 | \(\{0,2,8\}\) |
| 47 | \(\{0,9,10\}\) |
| 61 | \(\{0,11,15\}\) |

All three belong to \(U_0\), and all three possible mutual edges are live
in the frozen domain. The matching condition gives
\[
y_{1,47}+y_{1,61}+y_{47,61}\le1.
\]

The checker applies every one of the twelve actual core relabelings. The
three edges lie in original edge orbits 69, 76, and 4554, respectively.
Each orbit has size twelve, and each of its literal edges occurs exactly
once in the corresponding transported sum. In the unchanged reduced count
namespace, the resulting primitive inequality is
\[
\boxed{Y_{96}+Y_{103}+Y_{4477}\le12.}
\]

Here the subscripts are native reduced-count column IDs, not original edge
orbit IDs. The certificate retains all twelve literal transports and all
36 summed literal edge coefficients. This is a sum of valid inequalities
for one graph under changes of labels; no graph automorphism is assumed.

A four-vertex control fixes a central star and enumerates its eight possible
graphs on the three leaves. Exactly the zero-edge and three one-edge cases
satisfy the common-neighbor caps. Thus all cap-valid cases satisfy the
triangle matching inequality.

## Precisely limited comparison

The frozen explicit domains have upper bounds 3, 3, and 12 for the three
displayed \(Y\) columns. The three corresponding averaged star inequalities
are
\[
\begin{aligned}
Y_{96}+Y_{103}&\le N_0,\\
Y_{96}+Y_{4477}&\le N_{22},\\
Y_{103}+Y_{4477}&\le N_{25}.
\end{aligned}
\]
The endpoint selector orbits also have size twelve, so no extra ratio enters.

The six integer values
\[
(N_0,N_{22},N_{25};Y_{96},Y_{103},Y_{4477})
=(3,12,12;1,2,10)
\]
belong to their current explicit domains. Their three star slacks, written
as left minus right, are \(0,-1,0\). The new row has activity 13 and exceeds
its right-hand side by one.

This proves that the new row does not follow from those six domain boxes
and those three star rows alone. These six values are not asserted to
extend to a full-model point. No other native row, local profile table,
Fourier relation, or saved selector inequality was checked at that local
comparison. In particular, full-model nonredundance remains unproved.

The half-valued triangle \((1/2,1/2,1/2)\) separately illustrates the
unaveraged issue: it satisfies the three pairwise edge conflicts and
violates the triangle matching bound. That is a synthetic fractional
control, not a point of the F0 model.

## Artifact scope and next finite family

[The checker](../experiments/workspace/root_prism_free_f0_core_matching_blossom.py)
uses only frozen finite input records. Its
[certificate](../experiments/logs/root-prism-free/f0-core-matching-one-blossom01.json)
and [separate cold replay](../experiments/logs/root-prism-free/f0-core-matching-one-blossom01-cold.json)
check the original Gram combination, exact transports, count normalization,
and the limited comparison. No production candidate or optimizer was used.

The proposed next family consists only of legal three-edge cliques within
the 18 sets \(U_i\). Before edge pruning, it has at most
\[
6\binom{50}{3}+12\binom{61}{3}=549480
\]
literal triples. A separate bounded source will average the twelve
actions, add repeated orbit coefficients, normalize by a positive gcd,
and deduplicate the resulting integer count rows. It will record known
zero-edge dispositions and compare against the frozen single-orbit
packing bounds and explicit variable domains. It will not treat these
comparisons as a full inequality-redundance test.

No row from this note has been appended to the frozen native model.
